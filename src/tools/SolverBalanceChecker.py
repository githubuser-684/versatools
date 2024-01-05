from Tool import Tool
from CaptchaSolver import CaptchaSolver
import click

class SolverBalanceChecker(Tool):
    def __init__(self, app):
        super().__init__("Solver Balance Checker", "Check balance of your solvers", app)

    def run(self):
        solvers = ["anti-captcha", "2captcha", "capsolver", "capbypass"]

        for solver_name in solvers:
            if self.exit_flag is False:
                captcha_solver = CaptchaSolver(solver_name, self.captcha_tokens[solver_name])
                try:
                    balance = captcha_solver.get_balance()
                    click.echo(f"{solver_name.title()}: {balance}$")
                except Exception as e:
                    click.echo(f"{solver_name.title()}: ERROR {e}")