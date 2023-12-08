async function update() {
	const response = await eel.update_versatools()();

	if (response == true) {
		window.close();
	} else {
		swal("Something went wrong :(", response, "error").then(() => {
			window.close();
		});
	}
}

update();
