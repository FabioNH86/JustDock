document.addEventListener("DOMContentLoaded", function () {
	var firstTab = document.getElementById("tab1");
	if (!firstTab) return; // empty states have no tabs

	// Show the first tab's content by default
	firstTab.classList.add("active");

	// Handle tab click event
	const tabLinks = document.querySelectorAll(".tab-links li");
	tabLinks.forEach(function (tabLink) {
		tabLink.addEventListener("click", function (event) {
			event.preventDefault(); // avoid jumping to the #anchor

			tabLinks.forEach(function (tl) {
				tl.classList.remove("active");
			});
			tabLink.classList.add("active");

			document.querySelectorAll(".tab-content").forEach(function (tc) {
				tc.classList.remove("active");
			});

			const tabId = tabLink.querySelector("a").getAttribute("href").substring(1);
			document.getElementById(tabId).classList.add("active");

			// Mol* viewers created inside hidden tabs need a resize to fill their container
			window.dispatchEvent(new Event("resize"));
		});
	});

	renderAffinities();
});

// Parse the AutoDock Vina score table into stats + a table with affinity bars.
// Falls back to only showing the raw output if the format is not recognised.
function renderAffinities() {
	var raw = document.getElementById("vina-raw");
	var target = document.getElementById("affinity-summary");
	if (!raw || !target) return;

	var rows = [];
	raw.textContent.split("\n").forEach(function (line) {
		var m = line.match(/^\s*(\d+)\s+(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$/);
		if (m) rows.push({ mode: m[1], aff: parseFloat(m[2]), lb: m[3], ub: m[4] });
	});
	if (!rows.length) return;

	var best = Math.min.apply(null, rows.map(function (r) { return r.aff; }));
	var worst = Math.max.apply(null, rows.map(function (r) { return r.aff; }));
	var mean = rows.reduce(function (s, r) { return s + r.aff; }, 0) / rows.length;

	function pct(aff) {
		// Stronger (more negative) affinity → longer bar
		if (best === worst) return 100;
		return 25 + 75 * (worst - aff) / (worst - best);
	}

	var html = '<div class="stat-row">' +
		'<div class="stat best"><span>Best affinity</span><strong>' + best.toFixed(1) + '<small>kcal/mol</small></strong></div>' +
		'<div class="stat"><span>Mean affinity</span><strong>' + mean.toFixed(1) + '<small>kcal/mol</small></strong></div>' +
		'<div class="stat"><span>Poses</span><strong>' + rows.length + '</strong></div>' +
		'</div>';

	html += '<div class="affinity-table"><table class="table"><thead><tr>' +
		'<th>Mode</th><th>Affinity (kcal/mol)</th><th></th><th>RMSD l.b.</th><th>RMSD u.b.</th>' +
		'</tr></thead><tbody>';
	rows.forEach(function (r) {
		html += '<tr><td>' + r.mode + '</td>' +
			'<td class="num">' + r.aff.toFixed(1) + '</td>' +
			'<td><div class="affinity-bar"><div style="width:' + pct(r.aff).toFixed(0) + '%"></div></div></td>' +
			'<td class="num">' + r.lb + '</td><td class="num">' + r.ub + '</td></tr>';
	});
	html += '</tbody></table></div>';

	target.innerHTML = html;
	// The parsed view covers the essentials; collapse the raw output.
	var details = document.getElementById("raw-output");
	if (details) details.open = false;
}
