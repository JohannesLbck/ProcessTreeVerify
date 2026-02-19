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

import logging
import re
from share import config
#from hashmap import constraints_t # Future Work :) 
import xml.etree.ElementTree as ET
from util import * 
## Check util which is an interface to all other methods if you want all method names

## Load the Hashmap for run time voting


## This contains the verification using explicit, annotated verification, meaning the activities are identified by labels and resources
## are explicity annotated

namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
data_decision_tags= [ ".//ns0:loop", ".//ns0:alternative"]
logger = logging.getLogger(__name__)

# Control Flow
## Existence: Checks if an activity a exists in the xml tree and returns the element or None, identifes by label, to identify using resource/data see below
def exists(tree, a):#
    if isinstance(a, ET.Element):
        return a   
    elif a == "End Activity" or a == "end activity":
        return tree.find(".//ns0:end_activity", namespace)
    elif a == "Start Activity" or a == "start activity":
        return tree.find(".//ns0:start_activity", namespace)
    elif a == "terminate":
        return tree.find(".//ns0:terminate", namespace)
    else:
        logger.add_activity(a)
        a_ele = exists_by_label(tree, a)
        if a_ele is None:
            logger.info(f'Activity "{a}" existence was checked but not found')
        return a_ele

## Absence: opposite of exists, returns a Boolean 
def absence(tree, a):
    return not Bool(exists(a, tree))

## loop(tree, a): checks if an activity is in a loop, returns None or said loop element
def loop(tree, a):
    loops = tree.findall(".//ns0:loop", namespace)
    for loop in loops:
        apath = exists(loop, a)
        if apath is not None:
            logger.info(f'Found Activity "{a}" in a loop {loop}')
            return loop 
    logger.info(f'Found no Loop with Activity {a} in it')
    return None


def directly_follows(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is not None:
            if a =="terminate":
                logger.info(f'terminate can never lead to another activity, "{b}" directly follows "{a}" is False')
            elif b == "terminate":
                bpaths = tree.findall(".//ns0:terminate", namespace)
                for bpath in bpaths:
                    ## For terminates only must directly follows is accepted, since can directly follows makes no sense
                    must = directly_follows_must(tree, apath, bpath)
                    if must:
                        logger.info(f'Found a terminate that directly follows "{a}"')
                        return True
                logger.info(f'Found no terminate that directly follows "{a}"')
                return False
            else:
                must = directly_follows_must(tree, apath, bpath)
                if must:
                    logger.info(f'Activity "{b}" directly follows Activity "{a}" is True')
                    return True
                else:
                    can = directly_follows_can(tree, apath, bpath)
                    if can:
                        logger.info(f'Activity "{b}" CAN directly follow "{a}": True, but does not have to')
                        return True
                    else:
                        logger.info(f'Activity "{b}" does not directly follow "{a}"')
                        return False
        else:
            logger.add_missing_activity(b)
            logger.info(f'Activity "{b}" is missing in the process')
            return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is missing in the process')
        return False

## Leads To: Checks if an activity a exists and if it does if the activity it leads to exists after
def leads_to(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is not None:
            compare = compare_ele(tree, apath, bpath)
            if compare == 0:
                logger.info(f'Activity "{a}" and Activity "{b}" are on different exclusive branches')
                return False
            elif compare == -1:
                logger.info(f'Activity "{a}" and Activity "{b}" are in parrallel')
                return False
            elif compare == 1:
                logger.info(f'Activity "{a}" is before Activity "{b}, checking if {b} is on a different exclusive branch"')
                return True
                ancestors_a, ancestors_b, shared = get_shared_ancestors(tree, apath, bpath)
                if any(elem.tag.endswith("choose") for elem in ancestors_b):
                    MCA = shared[-1].tag
                    if MCA.endswith("alternative") or MCA.endswith("otherwise") or MCA.endswith("parallel_branch"):
                        logger.info(f'Activity "{a}" and Activity "{b}" are on the same branch in the correct order')
                        return True
                    logger.info(f'Activity "{a} was found before "{b}, but it is in a different exclusive branch, so leads_to can not be guaranteed in every trace')
                    return False
            elif compare == 2:
                logger.info(f'Activity "{b}" is before Activity "{a}"')
                return False
        else:
            logger.info(f'Activity "{b}" is not found in the tree')
            return False 
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is not found in the tree')
        return True


## Precedence: Checks if an activity a exists, and if it does if the activity it requires as a precedence exists prior
def precedence(tree, a, b):
    a_ele= exists(tree, a)
    b_ele = exists(tree, b)
    if a_ele is not None:
        if b_ele is not None:
            compare = compare_ele(tree, a_ele, b_ele)
            if compare == 0:
                logger.info(f'Activities "{a}" and "{b}" are in different exclusive branches and accordingly cannot be compared using precedence')
                return False
            elif compare == -1:
                logger.info(f'Activities "{a}" and "{b}" are in parrallel and accordingly cannot be compared using precedence')
                return False
            elif compare == 1:
                logger.info(f'Activity "{a}" was found before "{b}", so precedence "{a}" requires "{b}" before is False')
                return False 
            elif compare == 2:
                logger.info(f'Activity "{b}" was found before "{a}". Ensuring that {b} is not on an exclusive branch which could lead to violations in some traces')
                ancestors_a, ancestors_b, shared = get_shared_ancestors(tree, a_ele, b_ele)
                if any(elem.tag.endswith("choose") for elem in ancestors_b):
                    LCA = shared[0].tag
                    if LCA.endswith("alternative") or LCA.endswith("otherwise"):
                        logger.info(f'Activity "{a}" and Activity "{b} are on the same branch in the correct order')
                        return True
                    logger.info(f'Activity "{b} was found before "{a}, but it is in a different exclusive branch, so precedence can not be guaranteed in every trace')
                    
                    return False
                logger.info(f'Activity "{b}" was found before "{a}", and "{b}" is not on an exclusive branch, so precedence "{a}" requires "{b}" before is True')
                return True
        else:
            logger.add_missing_activity(b)
            logger.info(f'Activity "{a}" was found but Activity "{b}" was not found, so precedence "{a}" requires "{b}" before it is false')
            return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" was not found in the process so precedence "{a}" requires "{b}" before it is true')
        return True


## Leads To Absence: if activity a exists, activity b does not exist after:
def leads_to_absence(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is None:
            return True
        else:
            compare = compare_ele(tree, apath, bpath)
            if compare == 0:
                return True
            elif compare == -1:
                return False
            elif compare == 1:
                return False
            elif compare == 2:
                return True
    else:
        return True
## Precdence Absence: if activity a exists, then activity b does not exist before
def precedence_absence(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if not bpath is not None:
            return True
        else:
            compare = compare_ele(tree, apath, bpath)
            if compare == 0: ## exclusive, different branch
                return True 
            elif compare == -1: ## parallel, different branch
                return False 
            elif compare == 1: ## apath is first
                return True
            elif compare == 2: ## bpath is first
                return False 
    else:
        return True

## parallel: checks if activities a and b are in parallel, if either does not exist return false
def parallel(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is not None:
            compare = compare_ele(tree, apath, bpath)
            if compare == -1:
                logger.info(f'Activities "{a}" and "{b}" are in parallel')
                return True
            else:
                logger.info(f'Activities "{a}" and "{b}" are not in parallel')
                return False
        else:
            logger.add_missing_activity(b)
            logger.info(f'Activity "{b}" is missing in the process')
            return False

    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is missing in the process')
        return False


# Resource

## Returns whichever activity is executed a resource, if none does return value is None
def executed_by_identify(tree, resource):
    for call in tree.findall(".//ns0:call", namespace):
        target = call.find('.//ns0:annotations/ns0:_generic/ns0:Resource', namespace)
        if target is not None:
            resources_split = target.text.split(",")
            for target_resource in resources_split:
                if resource.strip() == target_resource.strip():
                    label = call.find('.//ns0:parameters/ns0:label', namespace).text
                    logger.info(f'Activity "{label}" was found which is executed by resource {resource}')
                    return label 
    logger.info(f'No Activity was found where resource "{resource}" is annotatet as Resource')
    return None
## Executed By Annotation: checks if an activity a exists, and if it does if it is executed by resource, by checking the annotation for Input Name: Resource
def executed_by(tree, a, resource,):
    apath = exists(tree, a)
    if apath is not None:
        for a_resource in executed_by_annotated(apath, tree):
            if a_resource.strip() == resource.strip():
                logger.info(f'Activity "{a}" is executed by Resource "{resource}"')
                return True
        logger.info(f'Activity "{a}" does not have an annotation Resource "{resource}"')
        return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is missing in the process')
        return False

## Returns the FIRST resource that is executing activity a, used to compare resources for segregation type requirements
def executed_by_return(tree, a):
    apath = exists(tree, a)
    if apath is not None:
        for resource in executed_by_annotated(apath, tree):
            logger.info(f'Activity "{a}" is executed by resource "{resource}"')
            return resource 
    else:
        logger.add_missing_activity(a)
        logger.info("Activity " + a + " does not exist.")
        return None 


## Time

# Recurring: checks if an activity is in a loop that contains a timeout activity with time t after a
def recurring(tree, a, t):
    a_ele = exists(tree, a)
    if a_ele is not None:
        loop_ele = loop(tree, a)
        if loop_ele is not None:
            for timeout in timeouts_exists(loop_ele):
                if timeout[1] is not None:
                    if not timeout[1].isdigit():
                        logger.warning('timeout in the loop uses a dataobject timestamp or is not passed a digit, correct dataobject is assumed, but this is a dynamic data requirement')
                        return leads_to(loop_ele, a_ele, timeout[0])
                    else:
                        logger.info(f'Identified a timeout in a loop with "{a}"')
                        if t == int(timeout[1]):
                            logger.info(f'Verifying existence of "{a} in {loop_ele}')
                            return leads_to(loop_ele, a_ele, timeout[0])
            logger.info('No timeout was found to enforce the recurring requirement')
            return False
        else:
            logger.info(f'Activity "{a}" is not in a loop and accordingly can not be recurring')
            return False
    else:
        logger.info(f'Activity "{a}" is missing in the process, so the recurring requirement is trivially false')

# timed_alternative: checks if two activities are in a cancel branch relationship, with a timeout before the time_alternative b, if either is missing its false
def timed_alternative(tree, a, b, time):
    a_ele = exists(tree, a)
    if a_ele is not None:
        b_ele = exists(tree, b)
        if b_ele is not None:
            for timeout in timeouts_exists(tree):
                  parallel = cancel_first(tree, timeout[0], a_ele)
                  if parallel is not None:
                      if timeout[1] is not None:
                          if not timeout[1].isdigit():
                              logger.warning('timeout in the parallel cancel uses a dataobject timestamp or is not passed a digit, correct dataobject is assumed, but this is a dynamic data requirement')
                              return exists(timeout[0], a)
                          else:
                              logger.info(f'Identified a timeout in a parallal cancel with "{b}"')
                              if time == int(timeout[1]):
                                  logger.info(f'Verifying existence of "{a} in {parallel}')
                                  return exists(parallel, a)
                              else:
                                  logger.info(f'timeout: "{timeout[1]}", while time required is: "{time}"')
                                  return False
            logger.info('No timeout was found to enforce the timed_alternative requirement')
            return False
        else:
            logger.info(f'Activity {b} is missing so the timed_alternative relationship is False')
    else:
        logger.info(f'Activity "{a}" is missing so the timed_alternative relationship is False')
        return False

## Min Time between two activities, enforced via Voting
def min_time_between(tree, a, b, time, c = None):
    a_sync = False
    if leads_to(tree, a, b):
        apath = exists(tree, a)
        bpath = exists(tree, b)
        data = {
            "Pattern": "min_time_between",
            "A": apath.attrib["id"],
            "B": bpath.attrib["id"],
            "time": time,
            "alternative": c,
            "A_time": None
        }
        constraints_t.insert(config.get_id(), data)
        if not c:
            logger.info(f'{a} and {b} were found without an alternative, so the voter will wait before {b} if necessary')
            return True 
        else:
            logger.info(f'{a} and {b} were found, so {c} will be executed by the voter before {b} if possible')
            return True
    else:
        logger.info(f'Activities "{a}" and "{b}" are not in a leads_to relationship, so the min_time_between requirement is False')
        return False 
## By Due Date: annotated, 
## This simply reads the annotation whether the due date is set correctly in the annotation, it does not check actual implementation, could be extended with voting later then it would even work during execution
def by_due_date_annotated(tree, a, timestamp):
    for call in tree.findall(".//ns0:call", namespace):
        label = call.find("ns0:parameters/ns0:label", namespace)
        if label is not None and label.text == a:
            annotation = call.find('.//ns0:annotations/ns0:_generic/ns0:DueDate', namespace)
            if annotation is not None:
                if int(annotation.text) <= int(timestamp):
                    logger.info(f'Annotation for Activity "{a}" which equals the timestamp or is smaller was found')
                    return True
                else:
                    logger.info(f'Activity "{a}" has a annotation for a due date but it is empty')
                    return False
            else:
                logger.info(f'Activity "{a}" does not have a annotation for a due date, add it using the generic annotations DueDate with a unix timestamp')
    logger.add_missing_activity(a)
    logger.info(f'Activity "{a}" does not exist in the tree, and can accordingly never be executed before its due data')
    return False 
## By Due Date: checks if the due date requirement is explicitly defined through sync check 
def by_due_date_explicit(tree, a, timestamp):
    apath = exists(tree, a)
    if apath:
        for call in due_date_exists(tree):
            if int(call[1]) <= int(timestamp):
                condition = f"data.{call[2]}"
                logger.info(f'found a due date activity that enforces the date requirement, check for alternative branch with condition: "{condition}" that eventually leads to "{a}"')
                return condition_directly_follows(tree, condition, a)
        logger.info(f'no due date activity was found to enforce the due date requirement')
        return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" does not exist in the tree, and can accordingly never be executed before its due data')
        return False

## checks both annotated and explicit, returns true if either
def by_due_date(tree, a, timestamp, c = None):
    if not c:
        annotated = by_due_date_annotated(tree, a, timestamp)
        explicit = by_due_date_explicit(tree, a, timestamp)
        logger.info(f'The due date is enforced through annotation: {annotated}. The due date is enforced explicitly: {explicit}. Overall this means the due date is {annotated or explicit}')
        if explicit:
            return True
        elif annotated:
            logger.warning('Assurance level is reduced, since the due date is only enforced through annotation')
            return True
        else:
            return False
    else:
        ### Here we set up the voter
        logger.info(f'The due date is enforced through a voter that replaces with the alternative at run time')
        return True

## There are technically many ways to implement this and accordingly many ways this could be checked, we enforcce here a very visually pleasing way of enforcing this, which is a event based gateway with a timeout. If said timeout finishes first it would mean that the max time between has passed. This is just one of many ways such as adding syncs before and after a and b, but this would be much less checkable and also have several ways of implementing
def max_time_between(tree, a, b, time, c = None):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is not None:
            if not c:
                for timeout in timeouts_exists(tree):
                    if cancel_last(tree, timeout[0], bpath) is not None:
                        if timeout[1] is not None:
                            if not timeout[1].isdigit(): 
                                logger.warning('timeout in the parallel with cancel uses a dataobject timestamp or is not passed a digit')
                                return True 
                            else:
                                logger.info(f'Identified a timeout in a parrallel with cancel relationship with "{b}"')
                                return time == int(timeout[1])## only works as long as all times are parsed as seconds
                        else:
                            logger.info('timeout in the parallel with cancel is not passed a argument or 0')
                            return False
                        ## A timeout is in an event based gateway with the second one, can be explicitly checked
                logger.info('No timeout was found to enforce the max time between requirement')
                return False
            else:
                ### Here we set up the voter
                logger.info(f'The due date is enforced through a voter that replaces the alternative at run time')
                return True
        else:
            logger.add_missing_activity(b)
            logger.info(f'Activity "{b}" is missing in the process')
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is missing in the process')
        return False


## Data
## Send Exist: Checks if any activity in tree sends data data, returns those activity as a list or None
def send_exist(tree, data):
    dataobjects = data_objects(tree)
    returnlist = []
    for call in dataobjects:
        for data_object in call[1]:
            if data_object == data:
                label = call[0].find("ns0:parameters/ns0:label", namespace)
                if label is not None:
                    label = label.text
                logger.info(f'found activity"{label}" which sends dataobject "{data}"')
                returnlist.append(call[0])
    if len(returnlist) > 0:
        return returnlist
    else:
        logger.info(f'did not find any activity which sends dataobject "{data}"')
        return None
## Receive Exist: Checks if any activity in tree receives data data, returns those activities or None
def receive_exist(tree, data):
    dataobjects = data_objects(tree)
    returnlist = []
    for call in dataobjects:
        for data_object in call[2]:
            if data_object == data:
                label = call[0].find("ns0:parameters/ns0:label", namespace)
                if label is not None:
                    label = label.text
                logger.info(f'found activity at path "{call[0]}" with label "{label}" which receives dataobject {data}')
                returnlist.append(call[0])
    if len(returnlist) > 0:
        return returnlist
    else
        logger.info(f'did not find any activity which receives dataobject "{data}"')
        return None
def activity_sends(tree, a, data):
    apath = exists(tree, a)
    if apath is not None:
        a_dict = activity_data_checks(tree, apath)
        arguments = a_dict["arguments"]
        prepare = a_dict["prepare"]
        for occurance in arguments:
            if occurance == data:
                logger.info(f'data object "{data}" is sent in the arguments of activity "{a}"')
                return True
        for occurance in prepare:
            if occurance == data:
                logger.info(f'data object "{data}" is prepared for sending in prepare of activity "{a}"')
                return True
        logger.info(f'data object "{data}" is not found in neither prepare nor arguments of Activity "{a}"')
        return False
    else:
        logger.info(f'Activity "{a}" does not exist in the tree, accordingly the send is trivally true')
        return True
def activity_receives(tree, a, data):
    apath = exists(tree, a)
    if "data." in data:
        data = data.split(".",1)
    if apath is not None:
        a_dict = activity_data_checks(tree, apath)
        finalize = a_dict["finalize"]
        for occurance in finalize:
            if occurance == data:
                logger.info(f'data object "{data}" is finalized from Activity "{a}"')
                return True
        logger.info(f'data object "{data}" is not found in finalize of Activity "{a}"')
        return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" does not exist in the tree, accordingly the receive is trivally true')
        return True
    
def condition(tree, condition):
    if condition_finder(tree, condition):
        return True
    else:
        return False
## One aspect to note, is that this function works trivially with terminates, because there can always only be a single terminate per branch
def condition_directly_follows(tree, condition , a):
    impacts = condition_impacts(tree, condition)
    if len(impacts) > 1:
        for i in len(impacts):
            try:
                if directly_follows(impacts[i], impacts[i+1]):
                    impacts.pop(i)
            except:
                continue
        logger.info(f'Found {len(impacts)} calls that influence condition "{condition}. Checking for a directly following branch for each')
    if len(impacts) < 2:
        branch = condition_finder(tree, condition)
        if branch is None:
            logger.info(f'No branch with condition: "{condition}" was found')
            return False
        apath = exists(branch, a)
        onbranch = False
        counter = 0
        if apath is None:
            logger.info(f'Activity "{a}" did not exist in the branch of condition: "{condition}"')
            return False
        ## This is highly inefficient (3 Iterations instead of 1) but it works and is easy to understand)
        elements = [elem for elem in branch.iter() if elem.tag.endswith('call') or elem.tag.endswith("terminate")]
        for ele in elements:
            if counter == 1:
                logger.info(f'Activity "{a}" did not directly follow the data condition "{condition}"')
                return False
            if ele == apath:
                parent_map = {c:p for p in tree.iter() for c in p}
                logger.info(f'Activity "{a}" directly followed the data_condition "{condition}"')
                if len(impacts) == 0:
                    logger.info(f'Found no activity that impacts the condition, so the branch has to be the first branch to directly follow')
                    return siblings(exists(tree, "Start Activity"), parent_map[branch], parent_map)
                else:
                    logger.info(f'Comparing if the branch directly follows after the condition is impacted')
                    return siblings(impacts[0], parent_map[branch], parent_map)
            counter += 1
    else:
        branches = multi_condition_finder(tree, condition)
        if len(branches) == 0:
            logger.info(f'No branch with condition: "{condition}" was found')
            return True
        else:
            if not len(impacts) == len(branches):
                logger.warning(f'There is not a branch condition for every time the condition can change so immediatelly follows is violated')
                return False
            logger.info(f'Checking for all data impact and branch pairs')
            for i in len(impacts):
                logger.info(f'Pair {i}:')

                counter = 0
                elements = [elem for elem in branches[i].iter() if elem.tag.endswith('call') or elem.tag.endswith("terminate")]
                for ele in elements:
                    if counter == 1:
                        logger.info(f'Activity "{a}" did not directly follow the data condition "{condition}"')
                        return False
                    if ele == apath:
                        logger.info(f'Activity "{a}" directly followed the data_condition "{condition}"')
                        logger.info(f'Comparing if the branch directly follows after the condition is impacted')
                        return siblings(impacts[i], parent_map[branches[i]], parent_map)
                    counter += 1
    logger.error(f"IF we got here something went wrong, in the condition_directly_follows function")
    return False


## activity failure eventually follows: If an activity a fails then b has to be executed. Checks for existence of a and b and then checks if a has a dataobject rescue that then has to exist in a condition towards a branch b
def failure_eventually_follows(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is not None:
            dataobjects = activity_data_checks(tree,apath)
            for data_object in dataobjects["rescue"]:
                condition = f"data.{data_object}"
                logger.info(f'Found a dataobject "{data_object}" that is used in a rescue of "{a}", checking if there is a branch with condition: "{condition}" that eventually leads to "{b}"')
                if condition_eventually_follows(tree, condition, b):
                    logger.info(f'Activity "{b}" eventually follows the failure of "{a}" through the dataobject "{data_object}"')
                    return True
            logger.info(f'No dataobject in rescue of "{a}" is used in a branch condition, so failure eventually follows can not be guaranteed')
            return False
        else:
            logger.add_missing_activity(b)
            logger.info(f'Activity "{b}" is missing in the process, so failure eventually follows can not be guaranteed')
            return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is missing in the process, so failure eventually follows is trivially true')
        return True

## activity failure directly follows: If an activity a fails then b has to be executed directly after. Checks for existence of a and b and then checks if a has a dataobject rescue that then has to exist in a condition towards a branch b that directly follows
def failure_directly_follows(tree, a, b):
    apath = exists(tree, a)
    bpath = exists(tree, b)
    if apath is not None:
        if bpath is not None:
            dataobjects = activity_data_checks(tree, apath)
            for data_object in dataobjects["rescue"]:
                condition = f"data.{data_object}"
                logger.info(f'Found a dataobject "{data_object}" that is used in a rescue of "{a}", checking if there is a branch with condition: "{condition}" that directly leads to "{b}"')
                if condition_directly_follows(tree, condition, b):
                    logger.info(f'Activity "{b}" directly follows the failure of "{a}" through the dataobject "{data_object}"')
                    return True
            logger.info(f'No dataobject in rescue of "{a}" is used in a branch condition, so failure directly follows can not be guaranteed')
            return False
        else:
            logger.add_missing_activity(b)
            logger.info(f'Activity "{b}" is missing in the process, so failure directly follows can not be guaranteed')
            return False
    else:
        logger.add_missing_activity(a)
        logger.info(f'Activity "{a}" is missing in the process, so failure directly follows is trivially true')
        return True


## Eventually follows a data condition. The default here is to check in the same branch (see scope = "branch") if the scope is said to global it checks anywhere after the branch as well 
def condition_eventually_follows(tree, condition, a, scope = "branch"):
    branch = condition_finder(tree, condition)
    if branch is not None:
        apath = exists(branch,a)
        if apath is not None:
            logger.info(f'Activity "{a}" was found on branch following condition "{condition}"')
            impacts = condition_impacts(tree, condition)
            logger.info(f'Found {len(impacts)} calls that influence condition "{condition}. Checking if both are prior to branch"')
            for call in impacts:
                if not leads_to(tree, call, branch):
                    logger.warning(f"Found a call {call} that is not prior to the identified branch, so compliance can be violated if said call can cause the condition to evaluate to true")
                    return False
            logger.info(f"All calls that influence the condition are prior to the condition, so eventually follows is satisfied")
            return True
        else:
            if scope == "branch":
                logger.info(f'While Branch following condition "{condition}" was found, the Activity "{a}" was not found on the branch')
                return False
            else: ## Scope is global or misspelled
                logger.info(f'Branch following condition"{condition} was found, however the Activity "{a}" was not found on the branch, since the scope is global, the two elements are compared')
                apath = exists(tree, a)
                if a is not None:
                    compare = compare_ele(tree, branch, apath)
                    if compare == 0: ## ele and branch are exclusive different branches
                        logger.info(f'branch and "{a}" are on different exclusive branches')
                        return False
                    elif compare == -1:
                        logger.info(f'branch and "{a}" are on different parallel branches')
                        return False
                    elif compare == 1:
                        logger.info(f'branch is before "{a}", True')
                        return True
                    elif compare == 2:
                        logger.info(f'branch is after "{a}", False')
                        return False
                else:
                    logger.info(f'Activity "{a}" does not exist in the process, eventually follows is False')
                    return False

    else:
        logger.info(f'No branch with condition: "{condition}" was found')
        return False
def data_leads_to_absence(tree, condition, a):
    return not condition_eventually_follows(tree, condition, a)

## Obligations vs Permissions: These can be modeled on the requirements side, using ands, ors and by just included the rule or not
## Complex resource requirements: These can also be modeled on the requirements side usind ands, ors and by just including rule or not
