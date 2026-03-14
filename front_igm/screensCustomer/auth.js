// auth.js
(function () {
  function isLogged() {
    return localStorage.getItem("logged") === "true";
  }

  function redirectToIndex() {
    // Ajusta si tu index esta en otra ruta
    window.location.href = "index.html";
  }

  // Inserta (o reutiliza) Logout en el navbar y lo muestra/oculta segun logged
  function ensureLogoutInNav() {
    // Agarra el primer navbar-nav de la pagina
    const navList = document.querySelector(".navbar .navbar-nav");
    if (!navList) return;

    // Si ya existe, no lo duplica
    let logoutItem = document.getElementById("logoutItem");
    if (!logoutItem) {
      logoutItem = document.createElement("li");
      logoutItem.className = "nav-item d-none";
      logoutItem.id = "logoutItem";

      const a = document.createElement("a");
      a.className = "nav-link";
      a.href = "#";
      a.id = "logoutLink";
      a.textContent = "Logout";

      logoutItem.appendChild(a);
      navList.appendChild(logoutItem);
    }

    const logoutLink = document.getElementById("logoutLink");
    if (logoutLink && !logoutLink.dataset.bound) {
      logoutLink.dataset.bound = "1";
      logoutLink.addEventListener("click", function (e) {
        e.preventDefault();
        localStorage.removeItem("logged");
        // cuando desloguea, lo mando al index
        redirectToIndex();
      });
    }

    // Mostrar/ocultar
    if (isLogged()) logoutItem.classList.remove("d-none");
    else logoutItem.classList.add("d-none");
  }

  // Guardia: si NO esta logueado, en cualquier pagina que no sea index.html lo manda al index
  function guardPrivatePages() {
    const path = (window.location.pathname || "").toLowerCase();

    // Detecta index.html o raiz ("/") como pagina publica
    const isIndex =
      path.endsWith("/index.html") ||
      path.endsWith("index.html") ||
      path.endsWith("/") ||
      path === "" ||
      path === "/";

    if (!isIndex && !isLogged()) {
      redirectToIndex();
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    guardPrivatePages();
    ensureLogoutInNav();
  });
})();