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
from semantic_matching import extract_labels, replace_labels
import argparse
import uvicorn
import time
import os
import signal
import sys
import subprocess
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
from fastapi.responses import HTMLResponse, JSONResponse
from hashmap import hash_t
from util import exists_by_label,transform_log, get_ancestors, compare_ele, add_start_end, combine_sub_trees
from tester import run_tests
from reqparser import parse_requirements, parse_req
from verificationAST import verify

url = "https://cpee.org/comp-log/receiver/" ## Points towards run/comp-receiver on cpee demo server. For production, please use your own endpoint.

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
async def _handle_subscription(request: Request, use_semantic_matching: bool = False):
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
            handlers = [handler],
            force=True
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
        description_xml = notification["content"].get("description")
        try:
            xml = ET.fromstring(description_xml)
        except Exception as exc:
            logger.exception(f"Failed to parse process description XML: {exc}")
            return

        labels = {'labels': [], 'embeddings': None}
        semantic_matching = use_semantic_matching

        if semantic_matching:
            logger.info("Semantic matching is enabled, this may lead to longer processing times and is not guaranteed to be correct")
            try:
                labels = extract_labels(xml)
            except Exception as exc:
                semantic_matching = False
                logger.exception(f"Semantic matching initialization failed, falling back to exact label matching: {exc}")
        else:
            logger.info("Semantic matching is disabled for this endpoint, using exact label matching")
        config.set_id(notification["instance"])
        xml = add_start_end(xml)
        xml= combine_sub_trees(xml)
        pre_parsing_assurance = logger.get_assurance_level()
        logger.info(f"The global assurance level is {pre_parsing_assurance}")
        requirements = parse_requirements(req)
        logger.reset_assurance_level()
        typ3 = form["type"]
        topic = form["topic"]
        event = form["event"]
        verified_requirements = []
        for tag, req in requirements.items():
            logger.info(f"Verifying Requirement {tag}: {req}")
            try:
                if semantic_matching:
                    req = replace_labels(req, labels)
                result, assurance = verify(req, tree=xml)
            except Exception as exc:
                req = parse_req(req)
                if semantic_matching:
                    req = replace_labels(req, labels)
                result, assurance = verify(req, tree=xml)
            ## Message with Assurance Level
            message = f"Requirement {tag} is {bool(result)} with assurance level {assurance}"
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
        print(yaml_log)
        response = requests.post(url, data = yaml_log.encode("utf-8"), headers=headers)
        print("Status:", response.status_code)
        print("Response:", response.text)
    return


@app.post("/Subscriber")
async def Subscriber(request: Request):
    return await _handle_subscription(request, use_semantic_matching=False)


@app.post("/SubscriberSemantic")
async def SubscriberSemantic(request: Request):
    return await _handle_subscription(request, use_semantic_matching=True)

def run_server():
    uvicorn.run("subscriber:app", port=9321, log_level="info")


PID_FILE = "subscriber.pid"
LOG_FILE = "subscriber.log"


def _read_pid(pid_file=PID_FILE):
    if not os.path.exists(pid_file):
        return None
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None


def _is_running(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _start_daemon():
    existing_pid = _read_pid()
    if _is_running(existing_pid):
        print(f"Subscriber already running with PID {existing_pid}")
        return
    if existing_pid and os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    log_path = os.path.join(os.path.dirname(__file__), LOG_FILE)
    with open(log_path, "a") as log_file:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "subscriber:app", "--port", "9321", "--log-level", "info"],
            cwd=os.path.dirname(__file__),
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    print(f"Started subscriber daemon with PID {proc.pid}")


def _stop_daemon():
    pid = _read_pid()
    if not pid:
        print("No subscriber.pid found. Subscriber is not running.")
        return
    if not _is_running(pid):
        print(f"Stale PID file found for PID {pid}. Removing it.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return

    print(f"Stopping subscriber daemon PID {pid}")
    os.kill(pid, signal.SIGINT)
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def _status_daemon():
    pid = _read_pid()
    if _is_running(pid):
        print(f"Subscriber is running with PID {pid}")
    elif pid:
        print(f"Subscriber is not running (stale PID {pid})")
    else:
        print("Subscriber is not running")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the compliance subscriber service")
    parser.add_argument("--stop", action="store_true", help="Stop the background subscriber daemon")
    parser.add_argument("--status", action="store_true", help="Show subscriber daemon status")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground for debugging")
    args = parser.parse_args()

    if args.stop:
        _stop_daemon()
    elif args.status:
        _status_daemon()
    elif args.foreground:
        run_server()
    else:
        _start_daemon()

