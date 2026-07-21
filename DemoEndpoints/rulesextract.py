from google import genai
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path


client = genai.Client()

class RequirementsModel(BaseModel):
    rules: List[str] = Field(..., description="List of requirement ASTs")

class SingleRequirementModel(BaseModel):
    rule: str = Field(..., description="Single requirement AST")



def extract_asts_from_rules(texts: List[str]) -> str:
    doc = Path("../methods_doc_concise.md").read_text(encoding="utf-8")
    prompt = (
                    "TASK: Extract compliance requirements from text and convert to AST expressions.\n"
                    "Format: R{NUMBER}: <expression>\n\n"

                    "CRITICAL RULES:\n"
                    "1. SYSTEM PERSPECTIVE: Model from system viewpoint. 'Customer receives email' = system sent it.\n"
                    "   Use send_exist() for outgoing, receive_exist() for incoming data.\n\n"

                    "2. ACTIVITY LABELS: Active voice, no articles or resource names.\n"
                    "   ✓ 'approve request'  ✗ 'manager approves request'\n\n"

                    "3. RESOURCE SPECIFICATION:\n"
                    "   - ALWAYS use executed_by(tree, 'activity', 'resource') pattern.\n"
                    "   - Resources must be specified separately from activity names.\n"
                    "   - ✗ WRONG:  executed_by(tree, 'manager approves request', 'manager')\n"
                    "   - ✓ RIGHT:  executed_by(tree, 'approve request', 'manager')\n\n"

                    "4. DATA OBJECTS: camelCase names, not physical objects.\n"
                    "   ✓ 'accountBalance'  ✗ 'sim card', 'pizza'\n"
                    "   Use conditions to enforce domain constraints:\n"
                    "   data_leads_to_absence(tree, 'accountBalance < 0', 'End Activity')\n\n"

                    "5. DATA DOMAIN: If a dataobject should stay in a certain domain, prevent it from reaching said domain.\n"
                    "   Example: 'accountBalance must never be negative' → no condition_eventually_follows(tree, 'accountBalance < withdrawalAmount', 'withdrawal')\n\n"

                    "5. DATA CONDITIONS: Format = 'dataName operator value'\n"
                    "   Operators: not, or, ==, and, >, <, >=, <=\n"
                    "   Example: '(loanAmount > 1000000) and (status == \"gold\")'\n\n"

                    "6. DESIGN TIME: Disjunction in NL may need conjunction of patterns.\n"
                    "   'Either delivered OR rejected' = both must exist in process\n\n"

                    "7. TIME: Encode seconds if possible (7 days = 604800s). String descriptiors if constraint is vague.\n"
                    "   Special Activities: 'Start Activity', 'End Activity', 'terminate'\n\n"

                    "8. failure_* patterns: ONLY for system execution failures, not negative results.\n"
                    "   ✗ 'check fails' (negative result) → ✓ condition_eventually_follows(tree, 'checkFailed == true', ...)\n"
                    "   ✓ 'system fails to send' (cannot execute) → failure_eventually_follows(...)\n\n"

                    "COMPLIANCE PATTERN REFERENCE\n"
                    f"{doc}\n\n"
                    "TEXT TO EXTRACT\n"
                    f"{texts}"
        )
    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": RequirementsModel.model_json_schema(),
                        "temperature": 0.3
            }
        )
    return  response.text


def extract_asts_from_text(text: str) -> str:
    doc = Path("../methods_doc_concise.md").read_text(encoding="utf-8")
    prompt = (
                    "TASK: Extract compliance requirements from text and convert to AST expressions.\n"
                    "Format: R{NUMBER}: <expression>\n\n"

                    "CRITICAL RULES:\n"
                    "1. SYSTEM PERSPECTIVE: Model from system viewpoint. 'Customer receives email' = system sent it.\n"
                    "   Use send_exist() for outgoing, receive_exist() for incoming data.\n\n"

                    "2. ACTIVITY LABELS: Active voice, no articles or resource names.\n"
                    "   ✓ 'approve request'  ✗ 'manager approves request'\n\n"

                    "3. RESOURCE SPECIFICATION:\n"
                    "   - ALWAYS use executed_by(tree, 'activity', 'resource') pattern.\n"
                    "   - Resources must be specified separately from activity names.\n"
                    "   - ✗ WRONG:  executed_by(tree, 'manager approves request', 'manager')\n"
                    "   - ✓ RIGHT:  executed_by(tree, 'approve request', 'manager')\n\n"

                    "4. DATA OBJECTS: camelCase names, not physical objects.\n"
                    "   ✓ 'accountBalance'  ✗ 'sim card', 'pizza'\n"
                    "   Use conditions to enforce domain constraints:\n"
                    "   data_leads_to_absence(tree, 'accountBalance < 0', 'End Activity')\n\n"

                    "5. DATA DOMAIN: If a dataobject should stay in a certain domain, prevent it from reaching said domain.\n"
                    "   Example: 'accountBalance must never be negative' → no condition_eventually_follows(tree, 'accountBalance < withdrawalAmount', 'withdrawal')\n\n"

                    "5. DATA CONDITIONS: Format = 'dataName operator value'\n"
                    "   Operators: not, or, ==, and, >, <, >=, <=\n"
                    "   Example: '(loanAmount > 1000000) and (status == \"gold\")'\n\n"

                    "6. DESIGN TIME: Disjunction in NL may need conjunction of patterns.\n"
                    "   'Either delivered OR rejected' = both must exist in process\n\n"

                    "7. TIME: Encode seconds if possible (7 days = 604800s). String descriptiors if constraint is vague.\n"
                    "   Special Activities: 'Start Activity', 'End Activity', 'terminate'\n\n"

                    "8. failure_* patterns: ONLY for system execution failures, not negative results.\n"
                    "   ✗ 'check fails' (negative result) → ✓ condition_eventually_follows(tree, 'checkFailed == true', ...)\n"
                    "   ✓ 'system fails to send' (cannot execute) → failure_eventually_follows(...)\n\n"

                    "COMPLIANCE PATTERN REFERENCE\n"
                    f"{doc}\n\n"
                    "TEXT TO EXTRACT\n"
                    f"{text}"
        )
    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": RequirementsModel.model_json_schema(),
                        "temperature": 0.3
            }
        )
    return  response.text


def single_rule(text: str) -> str:
    doc = Path("../methods_doc_concise.md").read_text(encoding="utf-8")
    prompt = (
                    "TASK: Extract compliance requirements from text and convert to AST expressions.\n"
                    "Format: R{NUMBER}: <expression>\n\n"

                    "CRITICAL RULES:\n"
                    "1. SYSTEM PERSPECTIVE: Model from system viewpoint. 'Customer receives email' = system sent it.\n"
                    "   Use send_exist() for outgoing, receive_exist() for incoming data.\n\n"

                    "2. ACTIVITY LABELS: Active voice, no articles or resource names.\n"
                    "   ✓ 'approve request'  ✗ 'manager approves request'\n\n"

                    "3. RESOURCE SPECIFICATION:\n"
                    "   - ALWAYS use executed_by(tree, 'activity', 'resource') pattern.\n"
                    "   - Resources must be specified separately from activity names.\n"
                    "   - ✗ WRONG:  executed_by(tree, 'manager approves request', 'manager')\n"
                    "   - ✓ RIGHT:  executed_by(tree, 'approve request', 'manager')\n\n"

                    "4. DATA OBJECTS: camelCase names, not physical objects.\n"
                    "   ✓ 'accountBalance'  ✗ 'sim card', 'pizza'\n"
                    "   Use conditions to enforce domain constraints:\n"
                    "   data_leads_to_absence(tree, 'accountBalance < 0', 'End Activity')\n\n"

                    "5. DATA DOMAIN: If a dataobject should stay in a certain domain, prevent it from reaching said domain.\n"
                    "   Example: 'accountBalance must never be negative' → no condition_eventually_follows(tree, 'accountBalance < withdrawalAmount', 'withdrawal')\n\n"

                    "5. DATA CONDITIONS: Format = 'dataName operator value'\n"
                    "   Operators: not, or, ==, and, >, <, >=, <=\n"
                    "   Example: '(loanAmount > 1000000) and (status == \"gold\")'\n\n"

                    "6. DESIGN TIME: Disjunction in NL may need conjunction of patterns.\n"
                    "   'Either delivered OR rejected' = both must exist in process\n\n"

                    "7. TIME: Encode seconds if possible (7 days = 604800s). String descriptiors if constraint is vague.\n"
                    "   Special Activities: 'Start Activity', 'End Activity', 'terminate'\n\n"

                    "8. failure_* patterns: ONLY for system execution failures, not negative results.\n"
                    "   ✗ 'check fails' (negative result) → ✓ condition_eventually_follows(tree, 'checkFailed == true', ...)\n"
                    "   ✓ 'system fails to send' (cannot execute) → failure_eventually_follows(...)\n\n"

                    "COMPLIANCE PATTERN REFERENCE\n"
                    f"{doc}\n\n"
                    "TEXT TO EXTRACT\n"
                    f"{text}"
        )
    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": SingleRequirementModel.model_json_schema(),
                        "temperature": 0.3
            }
        )
    return  response.text
