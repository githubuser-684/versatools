<p align="center">
	<a href="https://discord.gg/sV359yYZHY"><img src="icon.ico" alt="Versatools" height="90" /></a>
</p>

<h4 align="center">VERSATOOLS - FREE MULTITOOL | BOT FOLLOWERS/GROUP JOINS & MORE</h4>
<p align="center">
	Best FREE opensource Roblox botting tools written in Python.
</p>

<p align="center">
	<a href="#installation">Installation</a> •
	<a href="#file-templates">File templates</a> •
  <a href="https://garry.lol/versatools">Website</a> •
	<a href="https://discord.gg/sV359yYZHY">Discord server</a>
</p>
<br/>

## Screenshot

![Screenshot](./screenshot.png)

## Installation

This installation is designed for advanced users. To install Versatools, you can either download the latest release or run the program from source (Must have git and python installed).

Download the latest Windows release from [here](https://github.com/GarryyBD/versatools/releases/tag/v3.0.0).

## Running from source

First clone this repository:

```bash
git clone
```

Then install the requirements:

```bash
pip install -r requirements.txt
```

Finally, run the program:

```bash
python src/main.py
```

To convert the program to an executable, run:

```bash
pyinstaller --onefile --add-data '.venv/Lib/site-packages/tls_client/dependencies/tls-client-64.dll;tls_client/dependencies' --icon=icon.ico --name=Versatools src/main.py
```

To run unit tests:

```bash
python -m unittest discover src
```

## Capbypass

Versatools uses Capbypass to solve captchas. You can add your Capbypass API key in the `config.json` file.

Register for a Capbypass API key [here](https://capbypass.com/).

## File templates

### files/config.json

All attributes are mandatory. Removing them will break the program.

### files/cookies.txt

Add your cookies in this file. You can generate them using our Cookie Generator tool.
Versatools understands both UPC and C format for cookies.

### files/proxies.txt

You can use this template to add your proxies. We currently only support HTTP proxies.
Here are some examples of valid proxies lines:

```

8.8.8.8:5001
http:8.8.8.8:5001
8.8.8.8:5003:username:password

```

## Star History

<a href="https://star-history.com/#garryybd/versatools&Timeline">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=garryybd/versatools&type=Timeline&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=garryybd/versatools&type=Timeline" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=garryybd/versatools&type=Timeline" />
  </picture>
</a>

## Show your support

If you want to support the development of Versatools, you can donate to me:

- Donate to me in Bitcoin: bc1q9pvj2apxpym5yws92y7gd98y7q57hgj9vgeetr
- Donate to me in Ethereum: 0x8dCb5195cD30ec3fC0bfaF95C7528e8F1254438b
- Donate to me in Litcoin: LfBUdmmkFbN9vNho3iAv8qowcdjakkT4zZ

```

```
