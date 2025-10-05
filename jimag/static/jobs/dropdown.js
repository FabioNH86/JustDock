document.addEventListener("DOMContentLoaded", function () {
  //var contentSelector = document.getElementById("contentSelector");
  var dropdowns = document.querySelectorAll(".content-selector");

  function showSelectedContent(dropdown) {
    var selectedValue = dropdown.value;

    var contentSections = dropdown.closest(".jobsbox").querySelectorAll(".content-section");
    contentSections.forEach(function (section) {
      section.classList.remove("show");
    });

    var selectedContent = dropdown.closest(".jobsbox").querySelector(`#${selectedValue}`)
    if (selectedContent) {
      selectedContent.classList.add("show");
      //console.log("showing ", selectedContent);
    }
  }

  dropdowns.forEach(function (dropdown) {
    dropdown.addEventListener("change", function (){
      showSelectedContent(dropdown);
    });

    showSelectedContent(dropdown);
  });

});
