import { render } from "@testing-library/react";

import * as icons from "./index";

const NAMES = [
  "IconAlert",
  "IconBell",
  "IconBuilding",
  "IconCheck",
  "IconChevronDown",
  "IconChevronLeft",
  "IconChevronRight",
  "IconChevronsUpDown",
  "IconFactory",
  "IconEye",
  "IconEyeOff",
  "IconFile",
  "IconGlobe",
  "IconHouse",
  "IconInfo",
  "IconMenu",
  "IconMoon",
  "IconPackage",
  "IconPanelClose",
  "IconPanelOpen",
  "IconSearch",
  "IconSettings",
  "IconSun",
  "IconWrench",
] as const;

test("exports exactly the icons used by the design guide", () => {
  expect(Object.keys(icons).sort()).toEqual([...NAMES].sort());
});

test.each(NAMES)("%s is a 16 px icon with a 2 px stroke, hidden from screen readers", (name) => {
  const Icon = icons[name];
  const { container } = render(<Icon />);
  const svg = container.querySelector("svg");
  expect(svg).toBeInTheDocument();
  expect(svg).toHaveAttribute("width", "16");
  expect(svg).toHaveAttribute("height", "16");
  expect(svg).toHaveAttribute("stroke-width", "2");
  expect(svg).toHaveAttribute("aria-hidden", "true");
  expect(svg).toHaveAttribute("stroke", "currentColor");
});

test("a size can be overridden, as the menu toggle needs (22 px)", () => {
  const { container } = render(<icons.IconChevronLeft size={22} />);
  const svg = container.querySelector("svg");
  expect(svg).toHaveAttribute("width", "22");
  expect(svg).toHaveAttribute("height", "22");
  expect(svg).toHaveAttribute("stroke-width", "2");
});

test("props such as className reach the svg", () => {
  const { container } = render(<icons.IconCheck className="mark" />);
  expect(container.querySelector("svg")).toHaveClass("mark");
});

test("the eye icons are the open and the crossed eye, so the password toggle can tell its two states apart", () => {
  const open = render(<icons.IconEye />).container.querySelector("svg");
  const crossed = render(<icons.IconEyeOff />).container.querySelector("svg");
  expect(open).toHaveClass("lucide-eye");
  expect(crossed).toHaveClass("lucide-eye-off");
  expect(open?.innerHTML).not.toBe(crossed?.innerHTML);
});
