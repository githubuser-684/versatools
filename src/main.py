from multiprocessing import freeze_support
import click
from App import App
import json
import signal
import traceback
from os import system, name
from JsonEditor import JsonEditor

app = App()

global tool
tool = None

def config(tool_name):
    # Define styles for editor
    tool = app.get_tool_from(tool_name)
    initial_config = json.dumps(tool.config, indent=2)  # Convert config to a formatted JSON string

    json_editor = JsonEditor()
    edited_config = json_editor.edit(f"Editing config for {tool.name}", initial_config)

    try:
        updated_config = json.loads(edited_config)
    except json.JSONDecodeError:
        click.secho("Invalid JSON format. Please try again.", fg='red')
        return

    app.set_tool_config(tool, updated_config)
    click.secho(f"Configuration for {tool.name} updated.", fg='green')

def setup():
    config = app.get_solver_config()
    config_json = json.dumps(config, indent=2)

    json_editor = JsonEditor()
    edited_config = json_editor.edit("Editing captcha tokens config", config_json)

    try:
        updated_config = json.loads(edited_config)
    except json.JSONDecodeError:
        click.secho("Invalid JSON format. Please try again.", fg='red')
        return

    app.set_solver_config(updated_config)
    click.secho(f"Configuration for captcha tokens updated.", fg='green')

def files():
    click.secho("Cookies and proxies must be put in their respective files, one per line.", fg='bright_black')
    click.secho("Proxies are in the format: ip:port:username:password", fg='bright_black')

    app.start_files_dir()

def version():
    version = app.get_version()
    return version

def clear_terminal():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

def display_logo():
    logo = f"""                                                        /$$                         /$$
                                                       | $$                        | $$
    /$$    /$$ /$$$$$$   /$$$$$$   /$$$$$$$  /$$$$$$  /$$$$$$    /$$$$$$   /$$$$$$ | $$  /$$$$$$$
   |  $$  /$$//$$__  $$ /$$__  $$ /$$_____/ |____  $$|_  $$_/   /$$__  $$ /$$__  $$| $$ /$$_____/
    \  $$/$$/| $$$$$$$$| $$  \__/|  $$$$$$   /$$$$$$$  | $$    | $$  \ $$| $$  \ $$| $$|  $$$$$$
     \  $$$/ | $$_____/| $$       \____  $$ /$$__  $$  | $$ /$$| $$  | $$| $$  | $$| $$ \____  $$
      \  $/  |  $$$$$$$| $$       /$$$$$$$/|  $$$$$$$  |  $$$$/|  $$$$$$/|  $$$$$$/| $$ /$$$$$$$/
       \_/    \_______/|__/      |_______/  \_______/   \___/   \______/  \______/ |__/|_______/

    Version {version()} | Free | Open Source | Made by garryybd#0
"""
    click.secho(logo, fg='yellow')

def show_menu():
    tools = app.tools
    tools.sort(key=lambda x: x.name)

    for i, tool in enumerate(tools):
        tool_name_str = click.style(f"   {(' ' if i<9 else '') + str(i+1)} - ", fg='yellow') + tool.name
        space = " " * (25 - len(tool.name))
        tool_desc_str = click.style(tool.description, fg='bright_black')

        click.secho(tool_name_str + space + tool_desc_str)

    click.echo(click.style("   99 - ", fg='yellow') +"Exit")

    tool_name = None
    invalid_option = True

    while invalid_option:
        choice = input(click.style("\n ► Select an option: ", fg='yellow'))

        if choice == "99":
            raise KeyboardInterrupt()

        # select tool
        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(tools):
            tool_name = tools[int(choice) - 1].name
            invalid_option = False
        else:
            click.secho("Invalid option. Please try again.", fg='red')

    click.secho(f" ✓ Selected tool: {tool_name}", fg='green')
    return tool_name

def sigint_handle(signum, frame):
    click.secho("\n ✖ Stopping tool please wait... █▒▒▒▒▒▒▒▒▒ 0%", fg='yellow')
    if tool is not None:
        tool.signal_handler()
        raise KeyboardInterrupt()

def reset_signal_handler():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def launch_tool(tool_name):
    global tool

    signal.signal(signal.SIGINT, sigint_handle)

    try:
        tool = app.get_tool_from(tool_name)
        tool.load_config()
        app.launch_tool(tool)

        reset_signal_handler()
    except (KeyboardInterrupt, EOFError):
        reset_signal_handler()

        click.secho(" ✖ Tool stopped by user ██████████ 100%", fg='red')
    except Exception as err:
        reset_signal_handler()

        traceback_str = traceback.format_exc()
        click.echo(traceback_str)
        click.secho(str(err), fg='red')

def last_step(tool_name):
    click.secho("\n    1 - Run", fg='green')
    click.secho("    2 - Config tool", fg='yellow')
    click.secho("    3 - Add proxies / cookies", fg='magenta')
    click.secho("    4 - Setup captcha solver keys", fg='blue')
    click.secho("    5 - Return to menu", fg='cyan')

    wait_option = True
    option = None

    while wait_option:
        option = input(click.style("\n ► Select an option: ", fg='yellow'))

        if option == "1":
            wait_option = False
            launch_tool(tool_name)
            input("\nPress Enter to come back to the menu...")
        elif option == "2":
            config(tool_name)
        elif option == "3":
            files()
        elif option == "4":
            setup()
        elif option == "5":
            break
        else:
            click.secho("Invalid option. Please try again.", fg='red')
            wait_option = True

def run_program():
    clear_terminal()
    display_logo()
    tool_name = show_menu()
    last_step(tool_name)

if __name__ == "__main__":
    freeze_support()

    while True:
        try:
            run_program()
        except (KeyboardInterrupt, EOFError):
            click.secho("\n 〜 See you next time :)", fg='blue')
            break