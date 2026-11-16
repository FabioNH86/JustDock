document.addEventListener("DOMContentLoaded", function () {
  var dropdowns = document.querySelectorAll(".content-selector");

  function showSelectedContent(dropdown) {
    var selectedValue = dropdown.value;
    var box = dropdown.closest(".jobsbox");

    box.querySelectorAll(".content-section").forEach(function (section) {
      section.classList.remove("show");
    });

    var selectedContent = box.querySelector(`#${selectedValue}`);
    if (selectedContent) {
      selectedContent.classList.add("show");
    }
  }

  // Replace each <select> with a segmented control. The <select> stays in the
  // DOM (hidden) so other scripts can keep reading its value.
  function enhance(dropdown) {
    var group = document.createElement("div");
    group.className = "segmented";
    group.setAttribute("role", "tablist");

    Array.from(dropdown.options).forEach(function (option) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = option.textContent;
      btn.dataset.value = option.value;
      btn.setAttribute("role", "tab");
      btn.addEventListener("click", function () {
        dropdown.value = option.value;
        dropdown.dispatchEvent(new Event("change"));
      });
      group.appendChild(btn);
    });

    function sync() {
      group.querySelectorAll("button").forEach(function (b) {
        var active = b.dataset.value === dropdown.value;
        b.classList.toggle("active", active);
        b.setAttribute("aria-selected", active);
      });
    }

    dropdown.addEventListener("change", sync);
    dropdown.classList.add("enhanced");
    dropdown.parentNode.insertBefore(group, dropdown);
    sync();
  }

  dropdowns.forEach(function (dropdown) {
    dropdown.addEventListener("change", function () {
      showSelectedContent(dropdown);
    });
    enhance(dropdown);
    showSelectedContent(dropdown);
  });
});
