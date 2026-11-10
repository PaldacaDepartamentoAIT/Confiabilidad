import { act, renderHook } from "@testing-library/react";

import { useMediaQuery } from "./useMediaQuery";

type Listener = (event: { matches: boolean }) => void;

function stubMatchMedia(matches: Record<string, boolean>) {
  const listeners = new Map<string, Set<Listener>>();
  const matchMedia = vi.fn((query: string) => {
    if (!listeners.has(query)) listeners.set(query, new Set());
    return {
      matches: matches[query] ?? false,
      addEventListener: (_type: string, listener: Listener) => listeners.get(query)?.add(listener),
      removeEventListener: (_type: string, listener: Listener) =>
        listeners.get(query)?.delete(listener),
    };
  });
  vi.stubGlobal("matchMedia", matchMedia);
  return {
    matchMedia,
    listeners,
    change(query: string, value: boolean) {
      listeners.get(query)?.forEach((listener) => listener({ matches: value }));
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test("returns whether the query matches now", () => {
  const media = stubMatchMedia({ "(max-width: 767px)": true });

  expect(renderHook(() => useMediaQuery("(max-width: 767px)")).result.current).toBe(true);
  expect(media.matchMedia).toHaveBeenCalledWith("(max-width: 767px)");
  expect(renderHook(() => useMediaQuery("(max-width: 559px)")).result.current).toBe(false);
});

test("follows the query when the window changes size", () => {
  const media = stubMatchMedia({ "(max-width: 767px)": false });
  const { result } = renderHook(() => useMediaQuery("(max-width: 767px)"));

  act(() => media.change("(max-width: 767px)", true));
  expect(result.current).toBe(true);
  act(() => media.change("(max-width: 767px)", false));
  expect(result.current).toBe(false);
});

test("stops listening when the component goes away", () => {
  const media = stubMatchMedia({});
  const { unmount } = renderHook(() => useMediaQuery("(max-width: 767px)"));
  expect(media.listeners.get("(max-width: 767px)")?.size).toBe(1);

  unmount();

  expect(media.listeners.get("(max-width: 767px)")?.size).toBe(0);
});

test("switches to the new query when it changes", () => {
  const media = stubMatchMedia({ "(max-width: 767px)": true, "(max-width: 559px)": false });
  const { result, rerender } = renderHook(({ query }) => useMediaQuery(query), {
    initialProps: { query: "(max-width: 767px)" },
  });
  expect(result.current).toBe(true);

  rerender({ query: "(max-width: 559px)" });

  expect(result.current).toBe(false);
  expect(media.listeners.get("(max-width: 767px)")?.size).toBe(0);
  expect(media.listeners.get("(max-width: 559px)")?.size).toBe(1);
});

test("assumes a wide screen when the browser has no media queries", () => {
  vi.stubGlobal("matchMedia", undefined);
  expect(renderHook(() => useMediaQuery("(max-width: 767px)")).result.current).toBe(false);
});
