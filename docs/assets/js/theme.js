(function () {
  var KEY = "licenseguard-docs-theme";
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle");

  function setTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(KEY, theme);
    if (btn) {
      btn.textContent = theme === "dark" ? "Light mode" : "Dark mode";
    }
  }

  var initial = localStorage.getItem(KEY) || "light";
  setTheme(initial);

  if (btn) {
    btn.addEventListener("click", function () {
      var current = root.getAttribute("data-theme") || "light";
      setTheme(current === "dark" ? "light" : "dark");
    });
  }
})();
