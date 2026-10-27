import { act, render, screen } from "@testing-library/react";
import { useEffect } from "react";

import { useAnnouncer, type Politeness } from "./announcer";
import { LiveAnnouncer } from "./LiveAnnouncer";

let announce: (text: string, politeness?: Politeness) => void = () => {};

function Capture() {
  const current = useAnnouncer();
  useEffect(() => {
    announce = current;
  }, [current]);
  return null;
}

function regions() {
  return {
    polite: screen.getByRole("status"),
    assertive: document.querySelector('[aria-live="assertive"]'),
  };
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

test("both live regions exist and are empty from the first render", () => {
  render(
    <LiveAnnouncer>
      <Capture />
    </LiveAnnouncer>,
  );

  const { polite, assertive } = regions();
  expect(polite).toHaveAttribute("aria-live", "polite");
  expect(polite).toBeEmptyDOMElement();
  expect(assertive).not.toBeNull();
  expect(assertive).toBeEmptyDOMElement();
});

test("a polite announcement appears in the polite region on the next cycle", () => {
  render(
    <LiveAnnouncer>
      <Capture />
    </LiveAnnouncer>,
  );

  act(() => announce("Processing", "polite"));
  expect(regions().polite).toBeEmptyDOMElement();

  act(() => vi.runAllTimers());
  expect(regions().polite).toHaveTextContent("Processing");
  expect(regions().assertive).toBeEmptyDOMElement();
});

test("an assertive announcement uses the assertive region", () => {
  render(
    <LiveAnnouncer>
      <Capture />
    </LiveAnnouncer>,
  );

  act(() => announce("Too many attempts", "assertive"));
  act(() => vi.runAllTimers());

  expect(regions().assertive).toHaveTextContent("Too many attempts");
  expect(regions().polite).toBeEmptyDOMElement();
});

test("repeating the same text empties the region in between so it is announced again", () => {
  render(
    <LiveAnnouncer>
      <Capture />
    </LiveAnnouncer>,
  );

  act(() => announce("Processing"));
  act(() => vi.runAllTimers());
  act(() => announce("Processing"));

  expect(regions().polite).toBeEmptyDOMElement();
  act(() => vi.runAllTimers());
  expect(regions().polite).toHaveTextContent("Processing");
});

test("without a provider, announcing does nothing and does not fail", () => {
  render(<Capture />);

  expect(() => act(() => announce("Processing"))).not.toThrow();
});
