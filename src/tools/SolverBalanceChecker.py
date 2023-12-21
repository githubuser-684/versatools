from Tool import Tool
from CaptchaSolver import CaptchaSolver
import eel

class SolverBalanceChecker(Tool):
    def __init__(self, app):
        super().__init__("Solver Balance Checker", "Check balance of your solvers", 5, app)

    def run(self):
        solvers = ["anti-captcha", "2captcha", "capsolver", "capbypass"]

        for solver_name in solvers:
            if self.exit_flag is False:
                captcha_solver = CaptchaSolver(solver_name, self.captcha_tokens[solver_name])
                try:
                    balance = captcha_solver.get_balance()
                    eel.write_terminal(f"\x1B[1;32m{solver_name.title()}: {balance}$\x1B[0;0m")
                except Exception as e:
                    eel.write_terminal(f"\x1B[1;31m{solver_name.title()}: ERROR {e}\x1B[0;0m")

                import time
                time.sleep(1)
                print("flag: "+ str(self.exit_flag))