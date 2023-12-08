async function update() {
	const response = await eel.update_versatools()();

	if (response == true) {
		swal("Updated!", "Versatools has been updated", "success").then(() => {
			eel.restart_versatools()();
			window.close();
		});
	} else {
		swal("Something went wrong :(", response, "error").then(() => {
			window.close();
		});
	}
}

update();
