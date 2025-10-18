document.addEventListener("DOMContentLoaded", function () {
	// Show the first tab's content by default
	document.getElementById("tab1").classList.add("active");

	// Handle tab click event
	const tabLinks = document.querySelectorAll(".tab-links li");
	tabLinks.forEach(function (tabLink) {
		tabLink.addEventListener("click", function () {
			// Remove the "active" class from all tabs
			tabLinks.forEach(function (tl) {
				tl.classList.remove("active");
			});

			// Add "active" class to the clicked tab
			tabLink.classList.add("active");

			// Hide all tab content
			const tabContents = document.querySelectorAll(".tab-content");
			tabContents.forEach(function (tc) {
				tc.classList.remove("active");
			});

			// Show the content of the clicked tab
			const tabId = tabLink.querySelector("a").getAttribute("href").substring(1);
			document.getElementById(tabId).classList.add("active");
		});
	});
});