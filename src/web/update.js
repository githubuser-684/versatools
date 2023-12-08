async function update() {
	const response = await eel.update_versatools()();

	if (response == true) {
		swal("Updated!", "Versatools has been updated", "success").then(() => {
			eel.restart_versatools()();
		});
	} else {
		swal("Something went wrong :(", response, "error");
	}

	window.close();
}

update();
