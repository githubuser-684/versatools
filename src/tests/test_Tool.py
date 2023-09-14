import unittest
from tools.ProxyChecker import ProxyChecker
from App import App

class TestTool(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.app = App()
        self.tool = ProxyChecker(self.app)

    def test_clear_line(self):
        line = "  http : \n 8.8.8.8    : 80 \t   :  admin  :  1234  \n"
        cleaned_line = self.tool.clear_line(line)
        self.assertEqual(cleaned_line, "http:8.8.8.8:80:admin:1234")