import { renderHook } from "@testing-library/react";

import { useDeadline } from "./useDeadline";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

test("calls back once when the time passes while it is active", () => {
  const onExpire = vi.fn();
  renderHook(() => useDeadline(true, 10_000, onExpire));
  vi.advanceTimersByTime(9_999);
  expect(onExpire).not.toHaveBeenCalled();
  vi.advanceTimersByTime(1);
  expect(onExpire).toHaveBeenCalledTimes(1);
  vi.advanceTimersByTime(30_000);
  expect(onExpire).toHaveBeenCalledTimes(1);
});

test("does not call back when it stops being active before the time passes", () => {
  const onExpire = vi.fn();
  const { rerender } = renderHook(({ active }) => useDeadline(active, 10_000, onExpire), {
    initialProps: { active: true },
  });
  vi.advanceTimersByTime(5_000);
  rerender({ active: false });
  vi.advanceTimersByTime(60_000);
  expect(onExpire).not.toHaveBeenCalled();
});

test("does not call back when it is never active", () => {
  const onExpire = vi.fn();
  renderHook(() => useDeadline(false, 10_000, onExpire));
  vi.advanceTimersByTime(60_000);
  expect(onExpire).not.toHaveBeenCalled();
});

test("does not call back after unmounting", () => {
  const onExpire = vi.fn();
  const { unmount } = renderHook(() => useDeadline(true, 10_000, onExpire));
  unmount();
  vi.advanceTimersByTime(60_000);
  expect(onExpire).not.toHaveBeenCalled();
});

test("starts the time again when it becomes active again", () => {
  const onExpire = vi.fn();
  const { rerender } = renderHook(({ active }) => useDeadline(active, 10_000, onExpire), {
    initialProps: { active: true },
  });
  vi.advanceTimersByTime(8_000);
  rerender({ active: false });
  rerender({ active: true });
  vi.advanceTimersByTime(8_000);
  expect(onExpire).not.toHaveBeenCalled();
  vi.advanceTimersByTime(2_000);
  expect(onExpire).toHaveBeenCalledTimes(1);
});

test("calls the latest callback", () => {
  const first = vi.fn();
  const second = vi.fn();
  const { rerender } = renderHook(({ cb }) => useDeadline(true, 10_000, cb), {
    initialProps: { cb: first },
  });
  rerender({ cb: second });
  vi.advanceTimersByTime(10_000);
  expect(first).not.toHaveBeenCalled();
  expect(second).toHaveBeenCalledTimes(1);
});
