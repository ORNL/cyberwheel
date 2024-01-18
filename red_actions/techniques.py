class Technique():
    id = ""
    name = ""

# Is it worth having subtechniques (T1003.003) that inherit or 
# relate to techniques (T1003), or just better to map as individual
# components?

class OSCredentialDumping(Technique):
    id = "T1003"
    sub_techniques = ["T1003.001", "T1003.002", "T1003.003", "T1003.004", "T1003.005", "T1003.006", "T1003.007", "T1003.008"]

class ParentPIDSpoofing(Technique):
    id = "T1134.004"
    name = "Access Token Manipulation: Parent PID Spoofing"


