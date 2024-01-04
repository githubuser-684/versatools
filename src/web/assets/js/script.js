class WebApp {
	constructor() {
		this.runState = false;
		this.toolName = null;

		this.ensureInternetConnection();
		this.loadProxies();
		this.loadCookies();
		this.terminal = this.setupXTermJs("terminal");
		this.jsonEditor = this.setupJsonEditor();
		this.toolsInfo = this.setupSelectTools();
		this.setupButtons();
	}

	ensureInternetConnection() {
		if (!navigator.onLine) {
			alert("No internet connection!");
			// exit
			window.close();
		}
	}

	async loadProxies() {
		const proxiesEl = document.getElementById("proxies-loaded");
		proxiesEl.innerHTML = await eel.get_proxies_loaded()();
	}

	async loadCookies() {
		const cookiesEl = document.getElementById("cookies-loaded");
		cookiesEl.innerHTML = await eel.get_cookies_loaded()();
	}

	setupXTermJs(elementId) {
		const terminal = new Terminal();
		terminal.open(document.getElementById(elementId));

		return terminal;
	}

	setupJsonEditor() {
		const editor = ace.edit("json-editor");
		editor.setOptions({
			theme: "ace/theme/merbivore", // https://github.com/ajaxorg/ace/blob/master/src/ext/themelist.js
			mode: "ace/mode/json",
			fontSize: 18,
			highlightActiveLine: false,
		});

		editor.getSession().on("change", async () => {
			try {
				const jsonConfig = JSON.parse(editor.getValue());
				await eel.set_tool_config(this.toolName, jsonConfig);
				console.log("config.json updated");
			} catch (err) {
				if (err instanceof SyntaxError) {
					console.log("Config tool is not valid JSON. Not updating files/config.json");
				} else {
					throw err;
				}
			}
		});

		return editor;
	}

	setupButtons() {
		// setup terminal btns
		const btnClear = document.getElementById("btn-clear");
		btnClear.addEventListener("click", () => {
			this.terminal.clear();
		});

		const btnMenu = document.getElementById("btn-menu");
		btnMenu.addEventListener("click", async () => {
			await eel.show_menu()();
		});

		// setup run btn
		const btnRun = document.getElementById("btn-run");
		if (sessionStorage.getItem("running") === "true") {
			this.toogleRun();
		}
		btnRun.addEventListener("click", async () => {
			this.toogleRun();

			if (this.runState) {
				sessionStorage.setItem("running", "true");
				clear_terminal();
				await eel.launch_app_tool(this.toolName)();
			} else {
				sessionStorage.setItem("running", "false");
				await eel.stop_current_tool()();
			}
		});
	}

	toogleRun() {
		this.runState = !this.runState;
		const btnRun = document.getElementById("btn-run");

		if (this.runState) {
			set_stats(""); // clear stats

			btnRun.innerHTML = "STOP";
			btnRun.classList.remove("btn--success");
			btnRun.classList.add("btn--danger");
		} else {
			this.finishedRun();
		}
	}

	finishedRun() {
		const btnRun = document.getElementById("btn-run");

		btnRun.innerHTML = "START";
		btnRun.classList.remove("btn--danger");
		btnRun.classList.add("btn--success");
	}

	async setupSelectTools() {
		const toolsInfo = await eel.get_tools_info()();
		const select = document.getElementById("select-tools");

		for (let i = 0; i <= toolsInfo.length - 1; i++) {
			let opt = document.createElement("option");
			opt.value = toolsInfo[i].name;
			opt.innerHTML = toolsInfo[i].name;
			select.appendChild(opt);
		}

		const selectOnChange = async () => {
			this.toolName = select.options[select.selectedIndex].value;
			const newConfig = await eel.get_tool_config(this.toolName)();
			this.set_tool_config(newConfig);
		};

		select.addEventListener("change", () => selectOnChange());
		selectOnChange();

		return toolsInfo;
	}

	setJsonValue(value) {
		this.jsonEditor.setValue(value);
	}

	set_tool_config(newConfig) {
		const json = JSON.stringify(newConfig, null, 4);
		this.jsonEditor.setValue(json);
		this.jsonEditor.selection.clearSelection();
	}
}

const app = new WebApp();

eel.expose(write_terminal);
function write_terminal(message) {
	message = message.replace("\n", "\n\r");
	fmsg = message + "\n\r";
	app.terminal.write(fmsg);
}

eel.expose(clear_terminal);
function clear_terminal() {
	app.terminal.write("\x1bc");
}

eel.expose(scroll_terminal_up);
function scroll_terminal_up() {
	app.terminal.scrollToTop();
}

function input() {
	let curr_line = "";
	let resolveFunc;
	let rejectFunc;

	const disposable = term.onData(async (key) => {
		if (key === "\r") {
			// Enter
			disposable.dispose(); // Remove the event listener
			term.write("\r\n"); // Move to the next line

			if (resolveFunc) {
				resolveFunc(curr_line);
			}
		} else if (key === "\x7F") {
			// Backspace
			if (curr_line.length > 0) {
				curr_line = curr_line.slice(0, -1);
				term.write("\b \b");
			}
		} else {
			curr_line += key;
			term.write(key);
		}
	});

	const inputPromise = new Promise((resolve, reject) => {
		resolveFunc = resolve;
		rejectFunc = reject;
	});

	inputPromise.dispose = () => {
		disposable.dispose();
		rejectFunc(new Error("Input cancelled"));
	};

	return inputPromise;
}

eel.expose(set_ui_tool_config);
function set_ui_tool_config(newConfig) {
	app.set_tool_config(newConfig);
	console.log("ui config updated");
}

eel.expose(set_stats);
function set_stats(stats) {
	const statsEl = document.getElementById("stats");
	statsEl.innerHTML = stats;
}

eel.expose(tool_finished);
function tool_finished() {
	app.finishedRun();
}

eel.expose(reload_cookies);
function reload_cookies() {
	app.loadCookies();
}

eel.expose(reload_proxies);
function reload_proxies() {
	app.loadProxies();
}