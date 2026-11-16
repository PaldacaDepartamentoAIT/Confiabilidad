import { act, renderHook } from "@testing-library/react";

import { useCoarsePointer } from "./useCoarsePointer";

type Listener = (event: { matches: boolean }) => void;

function stubMatchMedia(initial: boolean) {
  const listeners = new Set<Listener>();
  const query = {
    matches: initial,
    addEventListener: vi.fn((_type: string, listener: Listener) => listeners.add(listener)),
    removeEventListener: vi.fn((_type: string, listener: Listener) => listeners.delete(listener)),
  };
  const matchMedia = vi.fn().mockReturnValue(query);
  vi.stubGlobal("matchMedia", matchMedia);
  return {
    matchMedia,
    query,
    listeners,
    change(matches: boolean) {
      listeners.forEach((listener) => listener({ matches }));
    },
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test("is true when the main pointer is coarse and false when it is fine", () => {
  const coarse = stubMatchMedia(true);
  expect(renderHook(() => useCoarsePointer()).result.current).toBe(true);
  expect(coarse.matchMedia).toHaveBeenCalledWith("(pointer: coarse)");

  stubMatchMedia(false);
  expect(renderHook(() => useCoarsePointer()).result.current).toBe(false);
});

test("follows the pointer when it changes while the page is open", () => {
  const media = stubMatchMedia(false);
  const { result } = renderHook(() => useCoarsePointer());

  act(() => media.change(true));
  expect(result.current).toBe(true);
  act(() => media.change(false));
  expect(result.current).toBe(false);
});

test("stops listening when the component goes away", () => {
  const media = stubMatchMedia(false);
  const { unmount } = renderHook(() => useCoarsePointer());
  expect(media.listeners.size).toBe(1);

  unmount();

  expect(media.listeners.size).toBe(0);
  expect(media.query.removeEventListener).toHaveBeenCalledTimes(1);
});

test("assumes the native control when the browser cannot tell, because it always works", () => {
  vi.stubGlobal("matchMedia", undefined);
  expect(renderHook(() => useCoarsePointer()).result.current).toBe(true);
});
