from Tool import Tool
from CaptchaSolver import CaptchaSolver

class SolverBalanceChecker(Tool):
    def __init__(self, app):
        super().__init__("Solver Balance Checker", "Check balance of your solvers", 5, app)

    def run(self):
        solvers = ["anti-captcha", "2captcha", "capsolver", "capbypass"]

        for solver_name in solvers:
            captcha_solver = CaptchaSolver(solver_name, self.captcha_tokens[solver_name])
            try:
                balance = captcha_solver.get_balance()
                print(f"\033[1;32m{solver_name.title()}: {balance}$\033[0;0m")
            except Exception as e:
                print(f"\033[1;31m{solver_name.title()}: ERROR {e}\033[0;0m")