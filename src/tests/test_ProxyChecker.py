import unittest
import os
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
        
    def test_test_proxy(self):
        is_working = self.tool.test_proxy({
            "http": f"http://10.8.8.8@admin:1234/",
            "https": f"http://10.8.8.8@admin:1234/"
        }, 1)

        self.assertEqual(is_working, False)

    def test_write_proxy_line(self):
        line = self.tool.write_proxy_line("http", "8.8.8.8", 80, "admin", "1234")
        self.assertEqual(line, "http:8.8.8.8:80:admin:1234\n")

        line = self.tool.write_proxy_line("http", "8.8.8.8", 80)
        self.assertEqual(line, "http:8.8.8.8:80\n")

        line = self.tool.write_proxy_line(None, "8.8.8.8", 80, "admin", "1234")
        self.assertEqual(line, "8.8.8.8:80:admin:1234\n")

        line = self.tool.write_proxy_line(None, "8.8.8.8", 80)
        self.assertEqual(line, "8.8.8.8:80\n")

        with self.assertRaises(ValueError, msg="Should raise error when username is provided but password is not"):
            self.tool.write_proxy_line("http", "8.8.8.8", 80, "admin", None)