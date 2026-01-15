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
import re
import logging
from utils.control_util import get_shared_ancestors

namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
data_decision_tags= [ ".//ns0:loop", ".//ns0:alternative"]

logger = logging.getLogger(__name__)

## Data_objects, Finds all dataobjects, returns a list of triples with each triple being (path, sends, receives) labels can appear multiple times if they appear multiple times in the process
def data_objects(tree):
    return_list = []
    for call in tree.findall(".//ns0:call", namespace):
        send_list = []
        receive_list = []
        if not call.attrib['endpoint'] == 'timeout':
            objects = activity_data_checks(tree, call)
            for occurence in objects["prepare"]:
                send_list.append(occurence)
            for occurence in objects["arguments"]:
                send_list.append(occurence)
            for occurence in objects["finalize"]:
                receive_list.append(occurence)
            return_list.append((call, send_list, receive_list))
    return return_list 

def parse_data_access(input_string):
    """
    Parses a string to extract keys accessed via `data.` and their corresponding values.

    - Keys assigned a value via `=` will have the value set to the assigned value.
    - Keys accessed but not assigned will have their value set to the key name.

    Args:
        input_string (str): The input string to parse.

    Returns:
        dict: A dictionary with keys and their corresponding values.
    """
    if input_string is not None:
        data_dict = {}

        # Find all `data.<key>` occurrences
        data_accesses = re.findall(r"data\.([a-zA-Z_]\w*)", input_string)

        # Iterate over each access
        for key in data_accesses:
            # Look for an assignment to the key
            pattern = rf"data\.{key}\s*=\s*(.+)"
            match = re.search(pattern, input_string)
            if match:
                # Extract the assigned value
                value = match.group(1).strip()
                data_dict[key] = value
            else:
                # If no assignment, value is the key itself
                data_dict[key] = key
        return data_dict
    else:
        return {} 

## Returns whichever dataobjects are send and received by a activity a, returned as a dict with 3 lists, prepare list, arguments and finalize list, this does not work with timeouts since they have no prepare and finalizes
def activity_data_checks(tree, target):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    prepare = target.find(".//ns0:prepare", namespace)
    if prepare is not None:
        prepare = prepare.text
    arguments = target.find(".//ns0:arguments", namespace)
    if arguments is not None:
        arguments_children = [
            f"{child.tag.split('}')[-1]}: {child.text.strip() if child.text else 'No text'}"
            for child in arguments
        ]
        arguments_text = "\n".join(arguments_children) if arguments_children else None 
    else:
        arguments_text = None
        arguments_output = None


    finalize = target.find(".//ns0:finalize", namespace)
    if finalize is not None:
        finalize = finalize.text
    return { "prepare": parse_data_access(prepare), "arguments": parse_data_access(arguments_text), "finalize": parse_data_access(finalize)}

def get_default_branch(tree, target):
    target_found = False
    for ele in tree.iter():
        if ele == target:
            target_found = True
        if target_found and ele.tag == "{http://cpee.org/ns/description/1.0}otherwise":
            ancestors1, ancestors2, shared_ancestors = get_shared_ancestors(tree, target, ele)
            ## Watch this codepiece closely, it might lead to errors in the future, the reason we do this
            ## is because the elements in this case are the conditions, which should always have the
            ## actual branch as their first ancestor (which we are not interested in) and then the
            ## shared ancestors as long as they are the right otherwise.
            if ancestors1[1:] == ancestors2[1:] :
                return ele
    logger.error(f"This should never happend, it means you found a branch with no otherwise, so there is some error in the PTV")
    return None

## This is definetly a Area for future work to find or design a much better matching algorithm, likely this would be regex based where we match over all potential
## ways that a condition can be written and then also develop the default branch using not A and not B (if a and b are branches with condition A and B)
def condition_finder(tree, condition):
    condition = condition.replace(" ", "")
    for tag in data_decision_tags:
        for target in tree.findall(tag, namespace):
            try:
                condition_xml=target.attrib["condition"]
            except:
                logger.error(f'Branch with no condition was found, your model has a syntax error')
            condition_xml = condition_xml.replace(" ", "")
            if target.tag == "{http://cpee.org/ns/description/1.0}alternative":
                ## These are complicated since they potentially reduce assurance due to the default branch
                #print(f'condition: {condition}')
                #print(f'condition_xml: {condition_xml}')
                #print(f'not condition_xml: not{condition_xml}')
                if condition.strip() == condition_xml.strip(): ## High Assurance
                    return target
                elif condition.strip() in condition_xml.strip(): ## Low Assurance
                    logger.warning(f"Condition mapped via in compared to ==, lower assurances")
                    return target
                elif condition.strip() in f"not{condition_xml}": ## Low Assurance
                    logger.warning(f"Branch default was found which matches to {condition}, lower assurance")
                    target = get_default_branch(tree, target)
                    return target
            if condition in condition_xml:
                logger.info(f"Branch was found which matches to {condition}")
                return target
    logger.info(f"Found no branch which matches to {condition}")
    return None

def multi_condition_finder(tree, condition):
    condition = condition.replace(" ", "")
    for tag in data_decision_tags:
        branches = []
        for target in tree.findall(tag, namespace):
            try:
                condition_xml=target.attrib["condition"]
            except:
                logger.error(f'Branch with no condition was found, your model has a syntax error')
            condition_xml = condition_xml.replace(" ", "")
            if target.tag == "{http://cpee.org/ns/description/1.0}alternative":
                ## These are complicated since they potentially reduce assurance due to the default branch
                #print(f'condition: {condition}')
                #print(f'condition_xml: {condition_xml}')
                #print(f'not condition_xml: not{condition_xml}')
                if condition.strip() == condition_xml.strip(): ## High Assurance
                    branches.append(target)
                elif condition.strip() in condition_xml.strip(): ## Low Assurance
                    logger.warning(f"Condition mapped via in compared to ==, lower assurances")
                    branches.append(target)
                elif condition.strip() in f"not{condition_xml}": ## Low Assurance
                    logger.warning(f"Branch default was found which matches to {condition}, lower assurance")
                    target = get_default_branch(tree, target)
                    branches.append(target)
            if condition in condition_xml:
                logger.info(f"Branch was found which matches to {condition}")
                branches.append(target)
    logger.info(f"Found no branch which matches to {condition}")
    return branches 


## This method returns a list of all data object identifiers (strings) from a condition
def extract_dobjects(condition):
    ## Remove Brackets
    #s = "(4+5) == Integer and boolean" <- TestString
    s = condition
    ## Split by operators
    s = s.replace("(","").replace(")","")
    tokens = re.split(r"\s*(and|or|>=|<=|==|>|<|\+|-)\s*", s)
    ## Remove Integers
    OPERATORS = {"and", "or", "<", ">", "==", ">=", "<=", "+", "-"}
    number_re = re.compile(r"^\d+(\.\d+)?$")
    variables = [
        t for t in tokens
        if t not in OPERATORS and not number_re.match(t)
    ] 
    ## Remove true, false, ""
    quoted_re = re.compile(r"""^\s*(['"]).*\1\s*$""")

    dobjects = [
        re.sub(r"^.*\.", "", v.strip())   # <-- injected normalization
        for v in variables
        if not quoted_re.match(v)
        and v.strip().lower() not in {"true", "false"}
    ]

    return dobjects

## This method returns a list of all the activities (as paths) which influence the result of evaluating a condition ( All calls that write to the dataobjects that appear in a condition)
def condition_impacts(tree, condition):
    print(condition)
    tobjects = extract_dobjects(condition)
    print(tobjects)
    dobjects = data_objects(tree)
    impacts = []
    for call in dobjects:
        for obj in call[2]:
            if call[0] in impacts:
                continue
            for data in tobjects:
                if obj == data:
                    impacts.append(call[0])
                    continue
    return impacts

