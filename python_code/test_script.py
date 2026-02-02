#! /usr/bin/python
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
import argparse
import time
import os
import signal
import sys
import json
import re
import logging
import assurancelogger 
import xml.etree.ElementTree as ET

from LogHandler import LogHandler
from util import transform_log, exists_by_label, get_ancestors, compare_ele, add_start_end, combine_sub_trees
from tester import run_tests
from reqparser import parse_requirements
from verificationAST import verify

logger = logging.getLogger("Top Level")
log = []
handler = LogHandler(log)
logging.basicConfig(
            level=logging.INFO,
            # The following Format is recommended for debugging
            format='%(asctime)s.%(msecs)03d - %(name)s - %(funcName)s - %(message)s',
            ## Handler for local logging below
            handlers=[handler 
            ]
        )


parser = argparse.ArgumentParser()

parser.add_argument('process', help="Path to the process tree .xml file")
args = parser.parse_args()

## File Loading
xml = ET.parse(args.process)

## data preparation
namespace1 = {"ns0": "http://cpee.org/ns/description/1.0"}
namespace2 = {"ns1": "http://cpee.org/ns/properties/2.0"} 

req = xml.find('.//ns1:requirements', namespace2)
xml = xml.find('.//ns0:description', namespace1)
requirements = parse_requirements(req.text)
xml = add_start_end(xml)
xml = combine_sub_trees(xml)
## Check if combining sub trees reduces assurance level
pre_parsing_assurance = logger.get_assurance_level()
logger.info(f"The global assurance level is {pre_parsing_assurance}")
logger.reset_assurance_level()
verified_requirements = []
for counter, req in enumerate(requirements):
    logger.info(f"Verifying Requirement R{counter}: {req}")
    result, assurance = verify(req, tree=xml)
    ## Message with Assurance Level
    message = f"Requirement R{counter} is {bool(result)} with assurance level {assurance}"
    ## Message without Assurance level
    ##message = f"Result: Requirement R{counter} is {bool(result)}"
    logger.info(message)
    verified_requirements.append((result, assurance, message))
    logger.reset_assurance_level()
logger.info(f"Currently required activities for the process are: {logger.get_activities()}")
logger.info(f"Currently missing activities for the process are: {logger.get_missing_activities()}")
xes_log = transform_log(log)
print(xes_log)
