const editor = ace.edit("json-editor");
editor.setOptions({
	theme: "ace/theme/merbivore", // https://github.com/ajaxorg/ace/blob/master/src/ext/themelist.js
	mode: "ace/mode/json",
	fontSize: 18,
	highlightActiveLine: false,
});

function set_ui_solver_config(newConfig) {
	editor.setValue(JSON.stringify(newConfig, null, 4));
	editor.selection.clearSelection();
	console.log("Solver config updated");
}

(async () => {
	const config = await eel.get_solver_config()();
	set_ui_solver_config(config);
})();

editor.getSession().on("change", async () => {
	try {
		const jsonConfig = JSON.parse(editor.getValue());
		await eel.set_solver_config(jsonConfig);
		console.log("I changed config");
	} catch (err) {
		if (err instanceof SyntaxError) {
			console.log("Solver config is not valid JSON. Not updating files/config.json");
		} else {
			throw err;
		}
	}
});

async function start_files_dir() {
	await eel.start_files_dir()();
}
