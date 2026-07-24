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
import uvicorn
import os
import signal
import sys
import subprocess
from typing import Dict, List, Optional, Union


from rulesextract import SingleRequirementModel, extract_asts_from_text, extract_asts_from_rules, extract_single_rule, extract_single_rule_with_model
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, JSONResponse

headers = {
        "Content-Type": "application/x-yaml",
        "Content-ID": "events"
        }

class RulesModel(BaseModel):
    rules: Union[Dict[str, str], List[str]]
    
class TextModel(BaseModel):
    rule: Optional[str] = None
    text: Optional[str] = None
    
    
class SingleRuleAndModelModel(BaseModel):
    rule: str
    model: str
    
app = fastapi.FastAPI()

# Allow browser-based clients (e.g. compliance UI) to call this API from other origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main():
    content = """
    <body>
    <form action="/text" enctype="multipart/form-data" method="post">
        <input type="text" name="text">
        <input type="submit" value="Submit">
    </form>
    </body>
    """
    return HTMLResponse(content=content)

log = []

@app.post("/singlerulemodel")
async def extract_single_rule_with_model_endpoint(rule: SingleRuleAndModelModel):
    print(f"Received single rule: {rule.rule} with model: {rule.model}")
    ast = extract_single_rule_with_model(rule.rule, rule.model)
    print(f"Extracted AST: {ast}")
    return JSONResponse(content={"ast": ast})

@app.post("/singlerule")
async def extract_single_rule_endpoint(rule: SingleRequirementModel):
    print(f"Received single rule: {rule.rule}")
    ast = extract_single_rule(rule.rule)
    print(f"Extracted AST: {ast}")
    return JSONResponse(content={"ast": ast})

@app.get("/singlerule")
async def singlerule_endpoint_info():
    return JSONResponse(content={"message": "Use POST /singlerule with JSON body {\"rule\": \"...\"}"})

@app.post("/rules")
async def extract_endpoint(rules: RulesModel):
    print(f"Received rules: {rules.rules}")
    if isinstance(rules.rules, dict):
        texts = list(rules.rules.values())
    else:
        texts = rules.rules
    asts = extract_asts_from_rules(texts)
    print(f"Extracted ASTs: {asts}")
    return JSONResponse(content={"asts": asts})

@app.get("/rules")
async def rules_endpoint_info():
    return JSONResponse(content={"message": "Use POST /rules with JSON body {\"rules\": {\"R1\": \"...\"}}"})

@app.post("/text")
async def extract_text_endpoint(text: TextModel):
    value = text.rule or text.text
    if not value:
        return JSONResponse(status_code=400, content={"detail": "Provide either 'rule' or 'text'."})
    print(f"Received text: {value}")
    asts = extract_asts_from_text(value)
    print(f"Extracted ASTs: {asts}")
    return JSONResponse(content={"asts": asts})

@app.get("/text")
async def text_endpoint_info():
    return JSONResponse(content={"message": "Use POST /text with JSON body {\"text\": \"...\"} or {\"rule\": \"...\"}"})


def run_server():
    uvicorn.run("extract:app", port=3591, log_level="info")


PID_FILE = "extract.pid"
LOG_FILE = "extract.log"


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
        print(f"extract already running with PID {existing_pid}")
        return
    if existing_pid and os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    log_path = os.path.join(os.path.dirname(__file__), LOG_FILE)
    with open(log_path, "a") as log_file:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "extract:app", "--port", "3591", "--log-level", "info"],
            cwd=os.path.dirname(__file__),
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))
    print(f"Started extract daemon with PID {proc.pid}")


def _stop_daemon():
    pid = _read_pid()
    if not pid:
        print("No extract.pid found. extract is not running.")
        return
    if not _is_running(pid):
        print(f"Stale PID file found for PID {pid}. Removing it.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return

    print(f"Stopping extract daemon PID {pid}")
    os.kill(pid, signal.SIGINT)
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def _status_daemon():
    pid = _read_pid()
    if _is_running(pid):
        print(f"extract is running with PID {pid}")
    elif pid:
        print(f"extract is not running (stale PID {pid})")
    else:
        print("extract is not running")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the compliance rules extract service")
    parser.add_argument("--stop", action="store_true", help="Stop the background extract daemon")
    parser.add_argument("--status", action="store_true", help="Show extract daemon status")
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