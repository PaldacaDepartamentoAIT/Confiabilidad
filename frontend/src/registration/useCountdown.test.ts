import { act, renderHook } from "@testing-library/react";

import { useCountdown } from "./useCountdown";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

function advance(seconds: number) {
  act(() => {
    vi.advanceTimersByTime(seconds * 1000);
  });
}

test("does not count nor warn before it is started", () => {
  const onZero = vi.fn();
  const { result } = renderHook(() => useCountdown(onZero));

  advance(5);

  expect(result.current.remaining).toBe(0);
  expect(onZero).not.toHaveBeenCalled();
});

test("counts down one second at a time from the given seconds", () => {
  const { result } = renderHook(() => useCountdown());

  act(() => result.current.start(3));
  expect(result.current.remaining).toBe(3);

  advance(1);
  expect(result.current.remaining).toBe(2);
  advance(1);
  expect(result.current.remaining).toBe(1);
});

test("warns once when it reaches zero and stays at zero", () => {
  const onZero = vi.fn();
  const { result } = renderHook(() => useCountdown(onZero));

  act(() => result.current.start(2));
  advance(1);
  expect(onZero).not.toHaveBeenCalled();

  advance(1);
  expect(result.current.remaining).toBe(0);
  expect(onZero).toHaveBeenCalledTimes(1);

  advance(10);
  expect(result.current.remaining).toBe(0);
  expect(onZero).toHaveBeenCalledTimes(1);
});

test("starting again restarts from the new value, even if it is the same", () => {
  const onZero = vi.fn();
  const { result } = renderHook(() => useCountdown(onZero));

  act(() => result.current.start(5));
  advance(3);
  act(() => result.current.start(5));
  expect(result.current.remaining).toBe(5);

  advance(4);
  expect(result.current.remaining).toBe(1);
  expect(onZero).not.toHaveBeenCalled();
  advance(1);
  expect(onZero).toHaveBeenCalledTimes(1);
});

test("can be started again after reaching zero", () => {
  const onZero = vi.fn();
  const { result } = renderHook(() => useCountdown(onZero));

  act(() => result.current.start(1));
  advance(1);
  act(() => result.current.start(2));

  advance(1);
  expect(result.current.remaining).toBe(1);
  advance(1);
  expect(onZero).toHaveBeenCalledTimes(2);
});

test("follows the clock, not the number of ticks, if the page was asleep", () => {
  const { result } = renderHook(() => useCountdown());

  act(() => result.current.start(60));
  act(() => {
    vi.setSystemTime(Date.now() + 30_000);
  });
  advance(1);

  expect(result.current.remaining).toBe(29);
});

test("stops counting when the screen goes away", () => {
  const onZero = vi.fn();
  const { result, unmount } = renderHook(() => useCountdown(onZero));

  act(() => result.current.start(2));
  unmount();
  advance(5);

  expect(onZero).not.toHaveBeenCalled();
});
