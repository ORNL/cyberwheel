from technique import Technique
import sys

sys.path.append("/Users/67x/cyberwheel/")
from red_actions.actions.killchain_phases import (
    InitialAccess,
    Execution,
    Persistence,
    Discovery,
)
from pprint import pprint, pformat

supported_os = ["macos"]

temp_host = None
temp_service = "ssh"  # TODO: What are the options for Service
# discovery = Discovery(temp_host, temp_service, [temp_host], [], supported_os, scanned_hosts=[], scanned_subnets=[])
