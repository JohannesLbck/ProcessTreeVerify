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

## Methods for parsing the Requirements from whatever language we choose
import json
import re

## when using the "language" I used, only this tiny bit of replacement is needed, but this could be replaced with an extensive dictionary to enable a mapping between any language and the code 
method_dict = {
    "prohibition": "not ",
    "root": "Start Activity",
    "end": "End Activity",
}


#parses the requirements into requirements that can be passed to the AST
def parse_requirements(req):
    req = re.sub(r'=>', ':', req)
    req = json.loads(req)
    return req

## enables writing an ast without the tree in every method as it would be in a proper object oriented implementation 
def parse_req(string):
    result = []
    for word in string.split("("):
        word = f'(tree, {word}'
        result.append(word)
    result = " ".join(result)
    return result[7:]
