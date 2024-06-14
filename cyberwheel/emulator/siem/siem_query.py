"""
Module defines the classes related to SIEM queries.
"""

import json


class SiemQuery:
    """
    Class to define elasticsearch queries for submitting the elastic SIEM.
    """

    @classmethod
    def is_alive(cls) -> str:
        """Empyty string query to check if the SIEM is running."""

        return ""

    @classmethod
    def get_indicies(cls) -> str:
        """Query to list the elasticsearch indices."""

        return "_cat/indices"

    @classmethod
    def get_observation(cls) -> str:
        """Query to get the state of the hosts"""

        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"process.executable": {"value": "/usr/sbin/sshd"}}},
                        {"term": {"event.category": {"value": "network"}}},
                    ]
                }
            }
        }

        return json.dumps(query)
