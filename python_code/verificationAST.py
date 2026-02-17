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

import ast
from annotated_verification import *
import logging

VERIFICATION_FUNCTIONS = {
    "exists": exists,
    "absence": absence,
    "leads_to": leads_to,
    "precedence": precedence,
    "leads_to_absence": leads_to_absence,
    "precedence_absence": precedence_absence,
    "parallel": parallel,
    "executed_by": executed_by,
    "executed_by_identify": executed_by_identify,
    "executed_by_return": executed_by_return,
    "directly_follows": directly_follows,
    "send_exist": send_exist,
    "receive_exist": receive_exist,
    "activity_sends": activity_sends,
    "activity_receives": activity_receives,
    "min_time_between": min_time_between,
    "by_due_date_annotated": by_due_date_annotated,
    "by_due_date_explicit": by_due_date_explicit,
    "by_due_date": by_due_date,
    "recurring": recurring,
    "max_time_between": max_time_between,
    "data_value_alternative": condition,
    "data_value_alternative_directly_follows": condition_directly_follows,
    "data_value_alternative_eventually_follows": condition_eventually_follows,
    "condition": condition,
    "condition_directly_follows": condition_directly_follows,
    "condition_eventually_follows": condition_eventually_follows,
    "data_leads_to_absence": data_leads_to_absence,
    "loop": loop,
    "timed_alternative": timed_alternative,
    "failure_directly_follows": failure_directly_follows,
    "failure_eventually_follows": failure_eventually_follows,
}

logger = logging.getLogger(__name__)

class MethodValidator(ast.NodeVisitor):
    def visit_Call(self, node):
        # Ensure the function being called is in the allowed list
        if not isinstance(node.func, ast.Name) or node.func.id not in VERIFICATION_FUNCTIONS:
            raise ValueError(f"Function {node.func.id} is not allowed!")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Prevent attribute access (e.g., a.b)
        raise ValueError("Attribute access is not allowed!")

    def visit_Name(self, node):
        # Allow variables (like a, tree) used as arguments
        pass

    def visit_Expr(self, node):
        # Ensure valid expressions
        self.generic_visit(node)

    def visit_Module(self, node):
        # Allow only single expressions (not full modules with multiple statements)
        if len(node.body) != 1:
            raise ValueError("Only a single expression is allowed!")
        self.generic_visit(node)


def verify(expression, **kwargs):
    # The following are several test expression that you can outcomment if you want to try them without sending them
    #expression = 'exists("F", tree)'
    #expression = 'leads_to(tree, "C" , "Emma")' 
    #expression = 'leads_to(tree, executed_by_identify(tree,"Maokai"), "Emma")'
    eval_tree = ast.parse(expression, mode="eval")

    validator = MethodValidator()
    validator.visit(eval_tree)

    exec_env = VERIFICATION_FUNCTIONS.copy()
    exec_env.update(kwargs)
    
    evaluation = eval(compile(eval_tree, filename="<ast>", mode="eval"), {"__builtins__": None}, exec_env)
    assurance_level = logger.get_assurance_level()
    return evaluation, assurance_level 
    
