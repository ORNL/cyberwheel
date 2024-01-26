from Technique import Technique
import art_techniques
from pprint import pprint, pformat
import inspect

total = 0
for name, obj in inspect.getmembers(art_techniques):
    if inspect.isclass(obj) and name != "Technique":
        obj = obj()
        pprint(obj.get_vulnerabilities())
        pprint(obj.get_weaknesses())
        total += 1
