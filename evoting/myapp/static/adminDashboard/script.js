document.addEventListener('DOMContentLoaded', function() {
  var dropdowns = document.querySelectorAll('.dropdown-btn');
  dropdowns.forEach(function(dropdown) {
      dropdown.addEventListener('click', function() {
          this.classList.toggle('active');
          var dropdownContent = this.nextElementSibling;
          if (dropdownContent.style.display === "block") {
              dropdownContent.style.display = "none";
          } else {
              dropdownContent.style.display = "block";
          }
      });
  });
});
