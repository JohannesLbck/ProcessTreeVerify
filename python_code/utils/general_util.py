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

import requests
import logging

logger = logging.getLogger(__name__)

def transform_log(log, cpee_instance = "local testing"):
    instance = None
    event_log = []
    for msg in log:
        timestamp, module, pattern, data= msg.split(" - ", 3)
        if data.startswith("Verifying Requirement "):
            instance = data.split(":", 1)[0].split()[-1]
            lifecycle = "start"
        elif data.startswith("Requirement "):
            lifecycle = "complete"
        else:
            lifecycle = "unknown"
        if instance is None:
            instance = "preprocessing"
        event = {
            "concept:instance": instance,
            "concept:name": pattern,
            "id:id": module,
            "ptv:activity_uuid": hash(instance+pattern+module),
            "cpee:instance": cpee_instance, 
            "lifecycle:transition": lifecycle,
            "ptv:lifecycle:transition": lifecycle,
            "data": data, 
            "time:timestamp": timestamp,          
        }
        event_log.append({"event": event})
    return event_log

def add_start_end(tree):
    new_first_sibling = ET.Element("{http://cpee.org/ns/description/1.0}start_activity")
    new_first_sibling.text = "Inserted Start Activity"

    new_last_sibling = ET.Element("{http://cpee.org/ns/description/1.0}end_activity")
    new_last_sibling.text = "Inserted End Activitiy"
    
    tree.insert(0, new_first_sibling)

    tree.append(new_last_sibling)
    return tree


## This method combines all subprocesses into the main tree, there is one unintended feature, where subprocesses are still in its own description element, which should be fine, since it makes you able to tell where they are, but does not really affect the other functions I think, lets keep this for now, even if it might lead to errors later
def combine_sub_trees(tree):
    ns1 = {"ns0": "http://cpee.org/ns/description/1.0"}
    ns2 = {"": "http://cpee.org/ns/properties/2.0"}
    
    # Iterate over the subprocess elements and replace them in the same loop
    for elem in tree.findall(".//ns0:call[@endpoint='subprocess']", ns1):
        url_elem = elem.find("ns0:parameters/ns0:arguments/ns0:url", ns1)
        url = url_elem.text
        if url is not None:
            url = url_elem.text
            logger.info(f"Fetching XML for subprocess from URL: {url}")            
            try:
                # Fetch the XML from the URL
                r = requests.get(url)
                r.raise_for_status()
                xml = ET.fromstring(r.text)
                # Find the subtree in the fetched XML
                subtree = xml.find(".//description", namespaces=ns2)
                
                if subtree is not None:
                    for parent in tree.iter():
                        if elem in parent:
                            # Get the index of the subprocess element manually
                            target_index = None
                            for i, child in enumerate(parent):
                                if child == elem:
                                    target_index = i
                                    break
                            
                            if target_index is not None:
                                # Insert all child elements of <description> before the subprocess
                                for child in subtree:
                                    parent.insert(target_index, child)
                                # Remove the subprocess element after adding its children
                                parent.remove(elem)
                                logger.info("Subprocess replaced with its child elements successfully.")
                            break
                else:
                    logger.warning(f"No <description> found in the fetched XML.")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error fetching the XML file for subprocess at {url}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error: {e}")
        else:
            logger.warning(f"Url of a subprocess is None")
    return tree

def find_subprocess(tree):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    
    results = [
    (elem, elem.find("ns0:parameters/ns0:arguments/ns0:url", namespace).text)
    for elem in tree.findall(".//ns0:call[@endpoint='subprocess']", namespace)
    if elem.find("ns0:parameters/ns0:arguments/ns0:url", namespace) is not None
    ]
    return results

#def combine_sub_trees(tree, paths):
#    ns1 = {"ns0": "http://cpee.org/ns/description/1.0"}
#    ns2 = {"": "http://cpee.org/ns/properties/2.0"}
#    for each in paths:
#        ## for each It will have to get the xml from the .xml and combine it with the tree at spot path
#        print(each[0])
#        try:
#            r = requests.get(each[1])
#            r.raise_for_status()
#            xml = ET.fromstring(r.text)
#            subtree = xml.find(".//description", namespaces=ns2)
#            print("reached")
#            target = tree.find(each[0], namespaces = ns1)
#            print("not reached")
#            target_parent = target.getparent()
#            target_index = list(target_parent).index(target)
#            target_parent[target_index] = subtree
#            print(tree.to_string())
#        except requests.exceptions.RequestException as e:
#            print(f"Error fetchign the XML file, bad path for subprocess: {e}")
