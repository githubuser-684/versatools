const discordInvite = "https://discord.gg/hBCqFHV3cC";

function copyDiscordInvite() {
	const copyText = discordInvite;
	navigator.clipboard.writeText(copyText);

	Toastify({
		text: "Discord invite copied! \n" + discordInvite.replace("https://discord", ""),
		duration: 3000,
		style: {
			background: "#1d232c",
			boxShadow: "none",
		},
	}).showToast();
}
