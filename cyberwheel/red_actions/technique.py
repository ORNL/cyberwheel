import jsonpickle
import json

from typing import List

from cyberwheel.red_actions.atomic_test import AtomicTest


class Technique:
    """
    Defines base class to derive ART Techniques from. Includes all attributes from ART Technique.
    """

    @classmethod
    def get_vulnerabilities(cls):
        return cls.cve_list

    @classmethod
    def get_weaknesses(cls):
        return cls.cwe_list

    @classmethod
    def get_atomic_test(cls, atomic_test_guid: str | None) -> AtomicTest | None:
        return cls.atomic_tests.get(atomic_test_guid, None)

    @classmethod
    def get_atomic_tests(cls) -> list[AtomicTest]:
        return list(cls.atomic_tests.values())

    @classmethod
    def get_name(cls) -> str:
        return cls.name

    @classmethod
    def __str__(self):
        obj = jsonpickle.encode(self)
        return json.dumps(json.loads(obj), indent=4)  # type: ignore
