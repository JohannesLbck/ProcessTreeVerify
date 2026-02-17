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
import uvicorn
import time
import os
import signal
import sys
import json
from share import config
import re
import uuid
import logging
import assurancelogger 
import xml.etree.ElementTree as ET
import requests
import yaml
import uuid

from LogHandler import LogHandler
from fastapi import FastAPI, File, UploadFile, Request, Form
from pydantic import BaseModel
from multiprocessing import Process
from fastapi.responses import HTMLResponse, JSONResponse
from hashmap import hash_t
from util import exists_by_label,transform_log, get_ancestors, compare_ele, add_start_end, combine_sub_trees
from tester import run_tests
from reqparser import parse_requirements
from verificationAST import verify

url = "https://cpee.org/comp-log/receiver/"

headers = {
        "Content-Type": "application/x-yaml",
        "Content-ID": "events"
        }

class Model(BaseModel):
    cpee: str
    instance_url: str
    instance: int
    topic: str
    type: str
    name: str
    timestamp: str
    content: dict
    instance_uuid: str
    instance_name: str

app = FastAPI()

@app.get("/")
async def main():
    content = """
    <body>
    <form action="/Subscriber" enctype="multipart/form_data" method="post">
    </form>
    </body>
    """
    return HTMLResponse(content=content)

log = []
@app.post("/Subscriber")
async def Subscriber(request: Request):
    call_id = str(uuid.uuid4())
    async with request.form() as form:
        notification = json.loads(form["notification"])
        hash_t.insert(notification["instance-uuid"], notification)
        # Start Logging 
        handler = LogHandler(log)
        logger = logging.getLogger(__name__)
        logging.basicConfig(
                level = logging.INFO,
                format='%(asctime)s.%(msecs)03d - %(name)s - %(funcName)s - %(message)s',
                handlers = [handler]
                )
        try:
            req = notification["content"]["attributes"]["requirements"]
        except:
            logger.info("No requirements attribute was passed, nothing to check")
            return
        try:
            save = notification["content"]["attributes"]["save"]
            if save:
                hash_t.save_disk("TrackedUIDsHashmap.json")
        except:
            logger.info("No save attribute was passed, previous version will only be stored in memory and not written to disk")
            #logger.info("If a save attribute was passed, and this message still shows, there is a internal server error")
        config.set_id(notification["instance"])
        requirements = parse_requirements(req)
        xml = ET.fromstring(notification["content"]["description"])
        xml = add_start_end(xml)
        xml= combine_sub_trees(xml)
        pre_parsing_assurance = logger.get_assurance_level()
        logger.info(f"The global assurance level is {pre_parsing_assurance}")
        logger.reset_assurance_level()
        typ3 = form["type"]
        topic = form["topic"]
        event = form["event"]
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
        logger.reset_activities()
        logger.reset_missing_activities()
        xes_log = transform_log(log, call_id, notification["instance-uuid"])
        log.clear()
        yaml_log= yaml.dump_all(
            xes_log,
            sort_keys=False,
            default_flow_style=False,
            explicit_start=True
        )
        #print(yaml_log)
        response = requests.post(url, data = yaml_log.encode("utf-8"), headers=headers)
        print("Status:", response.status_code)
        print("Response:", response.text)
    return

def run_server():
    pid = os.fork()
    if pid != 0:
        return
    print('Starting ' + str(os.getpid()))
    print(os.getpid(), file=open('subscriber.pid', 'w'))
    uvicorn.run("subscriber:app", port=9321, log_level="info")

if __name__ == "__main__":
    if os.path.exists('subscriber.pid'):
      with open("subscriber.pid","r") as f: pid =f.read()
      print('Killing ' + str(int(pid)))
      os.remove('subscriber.pid')
      os.kill(int(pid),signal.SIGINT)
    else:
      proc = Process(target=run_server, args=(), daemon=True)
      proc.start()
      proc.join()

