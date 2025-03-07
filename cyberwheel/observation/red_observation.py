import numpy as np

from typing import Iterable

from cyberwheel.observation.observation import Observation

class HostView:
    def __init__(
        self,
        name: str,
        type: str = "unknown",
        sweeped: bool = False,
        scanned: bool = False,
        discovered: bool = False,
        on_host: bool = False,
        escalated: bool = False,
        impacted: bool = False,
    ):
        self.name = name
        self.type = type
        self.sweeped = sweeped
        self.scanned = scanned
        self.discovered = discovered
        self.on_host = on_host
        self.escalated = escalated
        self.impacted = impacted

    def get_type(self) -> int:
        if self.type.lower() == "workstation":
            return 1
        elif self.type.lower() == "server":
            return 2
        else: # Unknown
            return 0

class RedObservation(Observation):

    def __init__(self, max_size: int):
        self.obs : dict[str, HostView] = {}
        self.max_size = max_size
        self.obs_vec : list[int] = [0] * max_size
        self.obs_index: dict[str, int] = {}
        self.size : int = 0
        #print(len(self.obs_vec))

    def add_host(
            self,
            host: str,
            type: str = "unknown",
            sweeped: bool = False,
            scanned: bool = False,
            discovered: bool = False,
            on_host: bool = False,
            escalated: bool = False,
            impacted: bool = False,
    ):
        self.obs[host] = HostView(name=host, type=type, sweeped=sweeped, scanned=scanned, discovered=discovered, on_host=on_host, escalated=escalated, impacted=impacted)
        self.obs_index[host] = self.size
        view = self.obs[host]
        #print(len(self.obs_vec))
        self.obs_vec[self.size:(self.size + 7)] = [
                view.get_type(),
                int(view.sweeped),
                int(view.scanned),
                int(view.discovered),
                int(view.on_host),
                int(view.escalated),
                int(view.impacted),
            ]
        self.size += 7
        #print(len(self.obs_vec))
        #print(list(self.obs.keys()))
        #print(self.obs_vec)
        pass

    def update_host(self, host: str, **kwargs):
        view = self.obs[host]
        view.type = kwargs.get("type", view.type)
        view.sweeped = kwargs.get("sweeped", view.sweeped)
        view.scanned = kwargs.get("scanned", view.scanned)
        view.discovered = kwargs.get("discovered", view.discovered)
        view.on_host = kwargs.get("on_host", view.on_host)
        view.escalated = kwargs.get("escalated", view.escalated)
        view.impacted = kwargs.get("impacted", view.impacted)

        host_index = self.obs_index[host]
        self.obs_vec[host_index:host_index+7] = self.get_view_obs(view)

    def get_view_obs(self, view: HostView) -> list[int]:
        view_obs = [
                view.get_type(),
                int(view.sweeped),
                int(view.scanned),
                int(view.discovered),
                int(view.on_host),
                int(view.escalated),
                int(view.impacted),
            ]
        return view_obs

    def reset(self, entry_host: str) -> Iterable:
        self.obs = {}
        self.obs_index = {}
        self.obs_vec = [0] * self.max_size
        self.size = 0
        self.add_host(entry_host, on_host=True)

        return np.array(self.obs_vec)