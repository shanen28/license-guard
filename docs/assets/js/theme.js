(function () {
  var KEY = "licenseguard-docs-theme";
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle");
  var search = document.getElementById("sidebar-search");
  var toc = document.getElementById("page-toc");

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

  if (search) {
    search.addEventListener("input", function () {
      var q = (search.value || "").trim().toLowerCase();
      document.querySelectorAll(".sidebar a").forEach(function (a) {
        var t = (a.textContent || "").toLowerCase();
        a.style.display = !q || t.indexOf(q) >= 0 ? "block" : "none";
      });
    });
  }

  if (toc) {
    var headings = document.querySelectorAll(".doc-card h2, .doc-card h3");
    if (!headings.length) {
      toc.innerHTML = '<span style="color: var(--muted); font-size: 0.84rem;">No sections</span>';
      return;
    }
    var html = "";
    headings.forEach(function (h) {
      if (!h.id) {
        h.id = (h.textContent || "")
          .trim()
          .toLowerCase()
          .replace(/[^a-z0-9\s-]/g, "")
          .replace(/\s+/g, "-");
      }
      var indent = h.tagName === "H3" ? " style=\"padding-left:0.95rem;\"" : "";
      html += "<a" + indent + " href=\"#" + h.id + "\">" + h.textContent + "</a>";
    });
    toc.innerHTML = html;
  }
})();
