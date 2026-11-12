// jsdom no implementa `showModal()` ni `close()` de `<dialog>`; `setupTests.ts` añade un doble mínimo
// para que los tests de los modales puedan abrirlos y cerrarlos.
function makeDialog() {
  const dialog = document.createElement("dialog");
  document.body.append(dialog);
  return dialog;
}

afterEach(() => {
  document.body.replaceChildren();
});

test("showModal opens the dialog", () => {
  const dialog = makeDialog();
  expect(dialog.open).toBe(false);

  dialog.showModal();

  expect(dialog.open).toBe(true);
  expect(dialog).toHaveAttribute("open");
});

test("close closes the dialog and emits close once", () => {
  const dialog = makeDialog();
  const onClose = vi.fn();
  dialog.addEventListener("close", onClose);
  dialog.showModal();

  dialog.close();

  expect(dialog.open).toBe(false);
  expect(dialog).not.toHaveAttribute("open");
  expect(onClose).toHaveBeenCalledTimes(1);
});

test("closing a dialog that is already closed emits nothing", () => {
  const dialog = makeDialog();
  const onClose = vi.fn();
  dialog.addEventListener("close", onClose);

  dialog.close();

  expect(onClose).not.toHaveBeenCalled();
});

test("showModal on a dialog that is already open keeps it open without a second event", () => {
  const dialog = makeDialog();
  const onClose = vi.fn();
  dialog.addEventListener("close", onClose);
  dialog.showModal();

  dialog.showModal();
  dialog.close();

  expect(dialog.open).toBe(false);
  expect(onClose).toHaveBeenCalledTimes(1);
});
