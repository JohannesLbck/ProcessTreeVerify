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

import logging
from hashmap import HashTable
from datetime import datetime
from dateutil.parser import parse
from utils.data_util import parse_data_access


logger = logging.getLogger(__name__)

## time exists returns a list of all timeouts with their timeout fields
def timeouts_exists(root):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    results = []
    # Iterate through all <call> elements
    for call in root.findall(".//ns0:call[@endpoint='timeout']", namespace):
        call_id = call.attrib.get('id', 'unknown') 
        timeout_element = call.find(".//ns0:arguments/ns0:timeout", namespace)

        if timeout_element is not None:
            if timeout_element.text is not None:
                timeout_value = timeout_element.text.strip()
                results.append((timeout_element, timeout_value))
            else:
                results.append((timeout_element, None))
    return results


def parse_timestamp(txt):
    if txt.isdigit():
        timestamp = int(txt)
        return datetime.utcfromtimestamp(timestamp).isoformat()
    if txt.startswith("data"):
        logger.info(f" the timestamp is a data_object, assurance reduced since dynamic timestamp")
        return input_string[4:].strip()
    try:
        return parse(txt).isoformat()
    except ValueError:
        logger.error("The timestamp sent could not be parsed")
        return None

## wait until exists: returns a list of all wait_untils with their timestamp fields
## if timestamp field = string: label of a dataobject
## if timestamp is a datatime: it is the passed timestamp
def wait_until_exists(root):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    results = []
    # Iterate through all <call> elements
    for call in root.findall(".//ns0:call[@endpoint='wait_until']", namespace):
        call_id = call.attrib.get('id', 'unknown')
        timeout_element = call.find(".//ns0:arguments/ns0:timestamp", namespace)

        if timeout_element is not None:
            if timeout_element.text is not None:
                timeout_value = timeout_element.text.strip()
                return_value = parse_timestamp(timeout_value)
                results.append((timeout_element, return_value))
            else:
                results.append((timeout_element, None))
    return results
## sync exists: returns a list of all sync elements with the data_object that its written in
## if no syncs: empty list
## if not written into any data_object, data_object is None
def sync_exists(root):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    results = []
    # Iterate through all <call> elements
    for call in root.findall(".//ns0:call[@endpoint='sync']", namespace):
        call_id = call.attrib.get('id', 'unknown')
        data_object= call.find(".//ns0:finalize", namespace)

        if data_object is not None:
            if data_object.text is not None:
                data_object= data_object.text.strip()
                data_object = parse_data_access(data_object)
                ## checking if data_object is assigned correctly
                for key, value in data_object.items():
                    if value == "result['Time']":
                        results.append((call, key))
                        break
                    logger.info(f"potentially your assignment of the result returned by the sync is incorrect, try data.sync = result['Time'] in finalize")
                    results.append((call, key))
            else:
                results.append((call, None))
    return results

def due_date_exists(root):
    namespace = {"ns0": "http://cpee.org/ns/description/1.0"}
    results = []
    # Iterate through all <call> elements
    for call in root.findall(".//ns0:call[@endpoint='due_date']", namespace):
        call_id = call.attrib.get('id', 'unknown')
        due_time = call.find(".//ns0:arguments/ns0:timestamp", namespace)
        data_object= call.find(".//ns0:finalize", namespace)

        if due_time is not None:
            if due_time.text is not None:
                due_time = due_time.text.strip()
        
        if data_object is not None:
            if data_object.text is not None:
                data_object= data_object.text.strip()
                data_object = parse_data_access(data_object)
                ## checking if data_object is assigned correctly
                for key, value in data_object.items():
                    print(f"value is {value}")
                    if "result['result']" in value:
                        data_object = key
                        break
                data_object = key
                logger.info(f"potentially your assignment of the result returned by the sync is incorrect, try data.due_date = result['result'] in finalize")
        results.append((call, due_time, data_object))
    return results


