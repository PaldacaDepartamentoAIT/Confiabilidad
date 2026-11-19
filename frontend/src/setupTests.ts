import "@testing-library/jest-dom";

// jsdom no implementa `<dialog>.showModal()` ni `close()` (el navegador real sí, y atrapa el foco y deja
// inerte la página). Este doble solo abre y cierra el diálogo y emite `close`; lo demás se prueba en
// Chromium (`frontend/visual`).
if (typeof HTMLDialogElement !== "undefined" && !HTMLDialogElement.prototype.showModal) {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    if (!this.hasAttribute("open")) return;
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
}
