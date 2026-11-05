import { act, renderHook } from "@testing-library/react";

import { matchRoute, navigate, useLocation } from "./router";

afterEach(() => {
  window.history.replaceState(null, "", "/");
});

describe("enrutador", () => {
  it("lee la ruta y el fragmento por separado", () => {
    window.history.replaceState(null, "", "/register/continue#abc123");

    const { result } = renderHook(() => useLocation());

    expect(result.current).toEqual({ path: "/register/continue", hash: "abc123" });
  });

  it("navega sin recargar y avisa a quien escucha", () => {
    const { result } = renderHook(() => useLocation());

    act(() => navigate("/register/done"));

    expect(window.location.pathname).toBe("/register/done");
    expect(result.current).toEqual({ path: "/register/done", hash: "" });
  });

  it("se actualiza al volver atrás en el historial", () => {
    const { result } = renderHook(() => useLocation());
    window.history.pushState(null, "", "/register");

    act(() => {
      window.dispatchEvent(new PopStateEvent("popstate"));
    });

    expect(result.current.path).toBe("/register");
  });

  it("da la ruta de reserva si la ruta no existe", () => {
    const routes = ["/", "/register"] as const;

    expect(matchRoute("/register", routes, "/")).toBe("/register");
    expect(matchRoute("/otra", routes, "/")).toBe("/");
    expect(matchRoute("/register/", routes, "/")).toBe("/");
  });
});
