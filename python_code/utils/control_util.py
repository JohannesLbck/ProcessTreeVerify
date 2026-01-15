#    Copyright (C) <2025>  <Johannes Löbbecke>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
import xml.etree.ElementTree as ET

## find ele by label
def exists_by_label(root, mlabel):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    for call in root.findall(".//ns0:call", namespace):
        label = call.find("ns0:parameters/ns0:label", namespace)
        if label is not None and label.text == mlabel:
            return call 
    return None

## Helper: Returns the ancestors of two elements 
def get_ancestors(root, ele):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    ancestors = [ele]
    current = ele 
    while current is not None:
        for parent in root.iter():
            if current in parent:
                ancestors.append(parent)
                current = parent
                break
        else:
            break
    return ancestors

## Helper: get shared ancestors and ancestors
def get_shared_ancestors(root, ele1, ele2):
    ancestors1 = get_ancestors(root, ele1)
    ancestors2 = get_ancestors(root, ele2)
    shared_ancestors = []
    for ancestor in ancestors1:
        if ancestor in ancestors2:
            shared_ancestors.append(ancestor)

    return ancestors1, ancestors2, shared_ancestors


## This method is idenpendent of the annotation style, this code is absolutly disgusting, I search through the entire tree
## 3 times which should really only take one search, but whatever, I dont like , this method assumes that the ele 
## exists in the tree
def compare_ele(root, ele1, ele2):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    ancestors1, ancestors2, shared_ancestors = get_shared_ancestors(root, ele1, ele2)
    shared_ex_branch = 0 
    exclusive = 0 
    parallel = 0 
    shared_par_branch = 0
    for ancestor in shared_ancestors: ## This checks if on the same branch
        if ancestor.tag.endswith("otherwise") or ancestor.tag.endswith("alternative"):
            shared_ex_branch += 1 
        if ancestor.tag.endswith("parallel_branch"):
            shared_par_branch += 1  
        if ancestor.tag.endswith("choose"): ## this then checks if exclusive (one level higher)
            exclusive += 1
        elif ancestor.tag.endswith("parallel"): ## checks if parallel (one level higher)
            parallel += 1
    if exclusive > shared_ex_branch:
        return 0
    elif parallel > shared_par_branch:
        return -1
    else:
        for element in root.iter():
            if element == ele1:
                return 1 
            elif element == ele2:
                return 2

## Some explanation here is required, so directly follows is not always checkable, say for example for the
## last activity in an exclusive which could either be directly before the one after the exclusive, but also
## never be executed in case the branch is never chosen. This method only returns True if it MUST directly
## follow each other, meaning they are in the same branches or not in parallels/exclusives
def directly_follows_must(root, ele1, ele2):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    ancestors1, ancestors2, shared_ancestors = get_shared_ancestors(root, ele1, ele2)
    shared_ex_branch = 0
    exclusive = 0
    parallel = 0
    shared_par_branch = 0
    for ancestor in shared_ancestors: ## This checks if on the same branch
        if ancestor.tag.endswith("otherwise") or ancestor.tag.endswith("alternative"):
            shared_ex_branch += 1
        if ancestor.tag.endswith("parallel_branch"):
            shared_par_branch += 1
        if ancestor.tag.endswith("choose"): ## this then checks if exclusive (one level higher)
            exclusive += 1
        elif ancestor.tag.endswith("parallel"): ## checks if parallel (one level higher)
            parallel += 1
    if exclusive > shared_ex_branch:
        return False 
    elif parallel > shared_par_branch:
        return False 
    elements = [elem for elem in root.iter() if elem.tag.endswith('call') or elem.tag.endswith("terminate") or elem.tag.endswith("start_activity")or elem.tag.endswith("end_activity")]
    for i in range(len(elements) - 1):
        if elements[i] is ele1 and elements[i + 1] is ele2:
            return True 
    return False

## Read above for longer explanation, but this also returns true if they are potentially directly follows
## like if they are the last activtiy in a exclusive branch and the first after the exclusive
def directly_follows_can(root, ele1, ele2):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    ancestors1, ancestors2, shared_ancestors = get_shared_ancestors(root, ele1, ele2)
    shared_ex_branch = 0
    exclusive = 0
    parallel = 0
    shared_par_branch = 0
    for ancestor in shared_ancestors: ## This checks if on the same branch
        if ancestor.tag.endswith("otherwise") or ancestor.tag.endswith("alternative"):
            shared_ex_branch += 1
        if ancestor.tag.endswith("parallel_branch"):
            shared_par_branch += 1
        if ancestor.tag.endswith("choose"): ## this then checks if exclusive (one level higher)
            exclusive += 1
        elif ancestor.tag.endswith("parallel"): ## checks if parallel (one level higher)
            parallel += 1
    if exclusive > shared_ex_branch:
        return False
    elif parallel > shared_par_branch:
        return False
    elements = [elem for elem in root.iter() if elem.tag.endswith('call')]
    for i in range(len(elements) - 1):
        if elements[i] is ele1 and elements[i + 1] is ele2:
            return True
    last_in_branch = False
    for ancestor in ancestors1:
        if ancestor.tag.endswith("parallel") or ancestor.tag.endswith("choose"):
            elementsall = [elem for elem in root.iter() if elem.tag.endswith("call") or elem.tag.endswith("parallel") or elem.tag.endswith("choose") or elem.tag.endswith("parallel_branch") or elem.tag.endswith("alternative") or elem.tag.endswith("otherwise")]
            for i in range(len(elementsall)-1):
                if elementsall[i] is ele1:
                    if not elementsall[i + 1].tag.endswith("call"):
                        last_in_branch = True
                if elementsall[i] is ele2:
                    return last_in_branch and not shared_ex_branch == exclusive 
    return False

## Checks if two activities are in an parrallel relationship where one branch can cancel the other, assumes that a and b exist
## this used to be event based gateway, but in practice you can implement the only method that uses this (max time between) with any parallels where the branches cancel. whether it cacnels after first or last is not relevant.
## It is kept this way, since this feels like the more natural way to check and it means the process developer is not strongly restricted, which is a design goal (see documentation)
def parallel_cancel(tree, a, b):
    ancestors1, ancestors2, shared_ancestors = get_shared_ancestors(tree, a, b)
    shared_branch = 0
    parallel = 0
    for ancestor in shared_ancestors:
        if ancestor.tag.endswith("parallel_branch"):
            shared_branch += 1 
        elif ancestor.tag.endswith("parallel"):
            if shared_branch <= parallel:
                if ancestor.attrib.get("wait")== "1":  #and ancestor.attrib.get("cancel") == "first"
                    return ancestor
            parallel += 1
    return None 

