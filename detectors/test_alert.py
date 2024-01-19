import unittest
from ipaddress import IPv4Address
from alert import Alert

class TestAlertMethods(unittest.TestCase):

    def test_to_dict(self):
        src_ip = IPv4Address("127.0.0.1")
        dst_ips = [IPv4Address("127.0.0.1")]
        local_ports = [22]
        remote_ports = [22]
        alert = Alert(src_ip, dst_ips, local_ports, remote_ports)
        t = {"src_ip": IPv4Address("127.0.0.1"),
             "dst_ips": [IPv4Address("127.0.0.1")],
             "local_ports": [22],
             "remote_ports": [22]}
        self.assertDictEqual(alert.to_dict(), t)
if __name__ == "__main__":
    unittest.main()