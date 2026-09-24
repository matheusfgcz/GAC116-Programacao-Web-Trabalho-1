(function () {
  const storageKey = "flowtask-theme";

  function getPreferredTheme() {
    const saved = localStorage.getItem(storageKey);
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(storageKey, theme);
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      const next = theme === "dark" ? "claro" : "escuro";
      btn.setAttribute("aria-label", `Ativar tema ${next}`);
      btn.setAttribute("title", `Tema ${next}`);
    });
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    applyTheme(current === "dark" ? "light" : "dark");
  }

  applyTheme(getPreferredTheme());

  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.addEventListener("click", toggleTheme);
  });

  const toggle = document.querySelector("[data-sidebar-toggle]");
  const sidebar = document.querySelector("[data-sidebar]");
  const backdrop = document.querySelector("[data-sidebar-backdrop]");

  function closeSidebar() {
    sidebar?.classList.remove("is-open");
    backdrop?.classList.remove("is-visible");
  }

  function openSidebar() {
    sidebar?.classList.add("is-open");
    backdrop?.classList.add("is-visible");
  }

  toggle?.addEventListener("click", () => {
    if (sidebar?.classList.contains("is-open")) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  backdrop?.addEventListener("click", closeSidebar);

  const drawer = document.querySelector("[data-task-drawer]");
  if (drawer) {
    const closeUrl = drawer.dataset.closeUrl;
    function closeDrawer() {
      if (closeUrl) {
        window.location.href = closeUrl;
      } else {
        window.history.back();
      }
    }

    drawer.querySelectorAll("[data-drawer-close]").forEach((el) => {
      el.addEventListener("click", (event) => {
        event.preventDefault();
        closeDrawer();
      });
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeDrawer();
      }
    });
  }
})();
