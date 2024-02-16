from typing import List

from red_actions.red_base import RedAction, RedActionResults, validate_attack, check_vulnerability, targets
from red_actions.Technique import Technique
from network.host import Host
from network.service import Service

import art_techniques
import inspect

class KillChainPhase(RedAction):
    """
    Base class for defining a KillChainPhase. Any new Killchain Phase (probably not needed) should inherit from this class.
    """
    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = []) -> None:
        """
        Same parameters as defined and described in the RedAction base class.
        - `src_host`: Host from which the attack originates.

        - `target_service`: The service being targeted.

        - `target_hosts`: The hosts being targeted. Can either be a list of hosts or list of subnets. If it is a list of subnets, then the attack should target all known hosts on that subnet.

        - `techniques`: A list of techniques that can be used to perform this attack.
        """
        super().__init__(src_host, target_service, target_hosts, techniques)

    def load_valid_techniques(self, killchain_phase: str, valid_os: List[str] = []) -> None:
        all_valid = valid_os == []
        for name, obj in inspect.getmembers(art_techniques):
            if not inspect.isclass(obj) or name == "Technique":
                continue
            obj = obj()
            if killchain_phase not in obj.kill_chain_phases:
                continue
            elif all_valid or any(x in obj.supported_os for x in valid_os):
                self.techniques.append((obj.mitre_id, obj.name))

    def set_techniques(self, techniques: List[str]):
        pass
    
    def sim_execute(self) -> RedActionResults:
        return NotImplementedError



class InitialAccess(KillChainPhase):
    """
    InitialAccess Killchain Phase Attack. As described by MITRE:

    The adversary is trying to get into your network.

    Initial Access consists of techniques that use various entry vectors to gain their initial foothold within a network. 
    Techniques used to gain a foothold include targeted spearphishing and exploiting weaknesses on public-facing web servers. 
    Footholds gained through initial access may allow for continued access, like valid accounts and use of external remote 
    services, or may be limited-use due to changing passwords.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "initial-access"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
    
class Execution(KillChainPhase):
    """
    Execution Killchain Phase Attack. As described by MITRE:

    The adversary is trying to run malicious code.

    Execution consists of techniques that result in adversary-controlled code running on a local or remote system. 
    Techniques that run malicious code are often paired with techniques from all other tactics to achieve broader goals, 
    like exploring a network or stealing data. For example, an adversary might use a remote access tool to run a 
    PowerShell script that does Remote System Discovery.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "execution"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class Persistence(KillChainPhase):
    """
    Persistence Killchain Phase Attack. As described by MITRE:

    The adversary is trying to maintain their foothold.

    Persistence consists of techniques that adversaries use to keep access to systems across restarts, changed credentials, 
    and other interruptions that could cut off their access. Techniques used for persistence include any access, action, 
    or configuration changes that let them maintain their foothold on systems, such as replacing or hijacking legitimate 
    code or adding startup code.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "persistence"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class PrivilegeEscalation(KillChainPhase):
    """
    PrivilegeEscalation Killchain Phase Attack. As described by MITRE:

    The adversary is trying to gain higher-level permissions.

    Privilege Escalation consists of techniques that adversaries use to gain higher-level permissions on a system or network. 
    Adversaries can often enter and explore a network with unprivileged access but require elevated permissions to follow 
    through on their objectives. Common approaches are to take advantage of system weaknesses, misconfigurations, and 
    vulnerabilities. Examples of elevated access include:
    - SYSTEM/root level
    - local administrator
    - user account with admin-like access
    - user accounts with access to specific system or perform specific function

    These techniques often overlap with Persistence techniques, as OS features that let an adversary persist can execute in an elevated context.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "privilege-escalation"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class DefenseEvasion(KillChainPhase):
    """
    DefenseEvasion Killchain Phase Attack. As described by MITRE:

    The adversary is trying to avoid being detected.

    Defense Evasion consists of techniques that adversaries use to avoid detection throughout their compromise. Techniques 
    used for defense evasion include uninstalling/disabling security software or obfuscating/encrypting data and scripts. 
    Adversaries also leverage and abuse trusted processes to hide and masquerade their malware. Other tactics' techniques 
    are cross-listed here when those techniques include the added benefit of subverting defenses.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "defense-evasion"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class CredentialAccess(KillChainPhase):
    """
    CredentialAccess Killchain Phase Attack. As described by MITRE:

    The adversary is trying to steal account names and passwords.

    Credential Access consists of techniques for stealing credentials like account names and passwords. Techniques used
    to get credentials include keylogging or credential dumping. Using legitimate credentials can give adversaries access 
    to systems, make them harder to detect, and provide the opportunity to create more accounts to help achieve their goals.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "credential-access"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class Discovery(KillChainPhase):
    """
    Discovery Killchain Phase Attack. As described by MITRE:

    The adversary is trying to figure out your environment.

    Discovery consists of techniques an adversary may use to gain knowledge about the system and internal network.
    These techniques help adversaries observe the environment and orient themselves before deciding how to act. 
    They also allow adversaries to explore what they can control and what's around their entry point in order to 
    discover how it could benefit their current objective. Native operating system tools are often used toward 
    this post-compromise information-gathering objective.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "discovery"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class LateralMovement(KillChainPhase):
    """
    LateralMovement Killchain Phase Attack. As described by MITRE:

    The adversary is trying to move through your environment.

    Lateral Movement consists of techniques that adversaries use to enter and control remote systems on a network.
    Following through on their primary objective often requires exploring the network to find their target and 
    subsequently gaining access to it. Reaching their objective often involves pivoting through multiple systems 
    and accounts to gain. Adversaries might install their own remote access tools to accomplish Lateral Movement 
    or use legitimate credentials with native network and operating system tools, which may be stealthier.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "lateral-movement"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class Collection(KillChainPhase):
    """
    Collection Killchain Phase Attack. As described by MITRE:

    The adversary is trying to gather data of interest to their goal.

    Collection consists of techniques adversaries may use to gather information and the sources information is collected 
    from that are relevant to following through on the adversary's objectives. Frequently, the next goal after collecting 
    data is to steal (exfiltrate) the data. Common target sources include various drive types, browsers, audio, video, 
    and email. Common collection methods include capturing screenshots and keyboard input.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "collection"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class Exfiltration(KillChainPhase):
    """
    Exfiltration Killchain Phase Attack. As described by MITRE:

    The adversary is trying to steal data.

    Exfiltration consists of techniques that adversaries may use to steal data from your network. Once they've collected 
    data, adversaries often package it to avoid detection while removing it. This can include compression and encryption. 
    Techniques for getting data out of a target network typically include transferring it over their command and control 
    channel or an alternate channel and may also include putting size limits on the transmission.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "exfiltration"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class CommandAndControl(KillChainPhase):
    """
    CommandAndControl Killchain Phase Attack. As described by MITRE:

    The adversary is trying to communicate with compromised systems to control them.

    Command and Control consists of techniques that adversaries may use to communicate with systems under their control within a victim
    network. Adversaries commonly attempt to mimic normal, expected traffic to avoid detection. There are many ways an adversary can 
    establish command and control with various levels of stealth depending on the victim's network structure and defenses.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "command-and-control"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError
        
class Impact(KillChainPhase):
    """
    Impact Killchain Phase Attack. As described by MITRE:

    The adversary is trying to manipulate, interrupt, or destroy your systems and data.

    Impact consists of techniques that adversaries use to disrupt availability or compromise integrity by manipulating business and 
    operational processes. Techniques used for impact can include destroying or tampering with data. In some cases, business processes 
    can look fine, but may have been altered to benefit the adversaries' goals. These techniques might be used by adversaries to follow 
    through on their end goal or to provide cover for a confidentiality breach.
    """
    name : str
    valid_os : List[str]

    def __init__(self, src_host: Host = None, target_service: Service = None, target_hosts: targets = [], techniques: List[Technique] = [], valid_os : List[str] = [], load_techniques : bool = True):
        """
        - `name`: Name of the Killchain Phase
        - `valid_os`: List of operating systems compatible with attack
        """
        super().__init__(src_host, target_service, target_hosts, techniques)
        self.name = "impact"
        self.valid_os = valid_os
        if load_techniques:
            self.load_valid_techniques(self.name, self.valid_os)

    def sim_execute(self) -> RedActionResults:
        return NotImplementedError