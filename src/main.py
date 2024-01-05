from multiprocessing import freeze_support
import click
from App import App
import random
import json
import signal
from threading import Thread

app = App()
global tool

@click.group()
def cli():
    pass

@click.command(help="Run a botting tool.")
@click.option('--name', required=True, help='Specify the tool name or number.')
def run(name):
    global tool
    tool = app.get_tool_from(name)

    app.launch_tool(tool)

@click.command(help="Get botting tools list.")
def tools():
    tools = app.tools

    output = "─══════════════════════════☆☆══════════════════════════─\n"
    for i, tool in enumerate(tools):
        random_color = random.choice(['red', 'green', 'yellow', 'blue', 'magenta', 'cyan'])

        output += f"({i+1}) "
        output += click.style(tool.name, fg=random_color)
        output += " | "

    output = output[:-3]
    output += "\n─══════════════════════════☆☆══════════════════════════─"
    click.echo(output)

@click.command(help="Get a tool's description.")
@click.option('--name', required=True, help='Specify the tool name or number.')
def desc(name):
    tool = app.get_tool_from(name)
    click.echo(tool.description)

@click.command(help="Edit a tool's config.")
@click.option('--name', required=True, help='Specify the tool name or number.')
def config(name):
    tool = app.get_tool_from(name)
    config_json = json.dumps(tool.config, indent=2)  # Convert config to a formatted JSON string

    edited_config = click.edit(config_json)  # Open the editor with the JSON content

    if edited_config is not None:
        updated_config = json.loads(edited_config)
        app.set_tool_config(tool, updated_config)
        click.echo(f"Configuration for {tool.name} updated.")
    else:
        click.echo("No changes made.")

@click.command(help="Setup your captcha solver keys.")
def setup():
    config = app.get_solver_config()
    config_json = json.dumps(config, indent=2)  # Convert config to a formatted JSON string

    edited_config = click.edit(config_json)  # Open the editor with the JSON content

    if edited_config is not None:
        updated_config = json.loads(edited_config)
        app.set_solver_config(updated_config)
        click.echo(f"Captcha solver keys updated.")
    else:
        click.echo("No changes made.")

@click.command(help="Check amount of proxies and cookies loaded.")
def loaded():
    proxies_loaded = app.get_proxies_loaded()
    cookies_loaded = app.get_cookies_loaded()
    click.echo(f"Proxies loaded: {proxies_loaded}")
    click.echo(f"Cookies loaded: {cookies_loaded}")

@click.command(help="Display the version of the application.")
def version():
    version = app.get_version()
    click.echo(version)

cli.add_command(run)
cli.add_command(tools)
cli.add_command(desc)
cli.add_command(config)
cli.add_command(setup)
cli.add_command(loaded)
cli.add_command(version)

if __name__ == "__main__":
    freeze_support()

    def handle(signum, frame):
        tool.signal_handler()
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, handle)

    cli()