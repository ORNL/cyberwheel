from Technique import Technique
import sys

sys.path.append("/Users/67x/cyberwheel/")
from red_actions.actions.killchain_phases import InitialAccess, Execution, Persistence
from pprint import pprint, pformat

supported_os = ["macos"]

initial_access = InitialAccess(supported_os)
execution = Execution(supported_os)
persistence = Persistence(supported_os)
pprint(initial_access.get_techniques())
pprint(execution.get_techniques())
pprint(persistence.get_techniques())
