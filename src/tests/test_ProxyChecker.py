import unittest
from tools.ProxyChecker import ProxyChecker
from App import App

class TestProxyChecker(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.app = App()
        self.tool = ProxyChecker(self.app)
    
    def test_test_proxy_line(self):
        is_working, proxy_type, proxy_ip, proxy_port, proxy_user, proxy_pass = self.tool.test_proxy_line("http:8.8.8.8:80:admin:1234", 1)

        self.assertEqual(is_working, False)
        self.assertEqual(proxy_type, "http")
        self.assertEqual(proxy_ip, "8.8.8.8")
        self.assertEqual(proxy_port, 80)
        self.assertEqual(proxy_user, "admin")
        self.assertEqual(proxy_pass, "1234")