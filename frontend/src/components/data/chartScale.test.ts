import { chartScale, type ChartGroup } from "./chartScale";

const group = (first: number, second: number): ChartGroup => ({ label: "m", first, second });

test("the axis goes from 0 to the next multiple of 30 that covers the largest value, with a tick every 30", () => {
  expect(chartScale([group(62, 48), group(96, 22)])).toMatchObject({
    max: 120,
    ticks: [0, 30, 60, 90, 120],
  });
});

test.each([
  [0, 30],
  [1, 30],
  [30, 30],
  [31, 60],
  [90, 90],
  [91, 120],
])("the largest value %s gives an axis up to %s, never below 30", (value, max) => {
  expect(chartScale([group(value, 0)])?.max).toBe(max);
});

test("the largest value can be in either series", () => {
  expect(chartScale([group(10, 95)])?.max).toBe(120);
  expect(chartScale([group(95, 10)])?.max).toBe(120);
});

test("with six groups each is 96 px wide, with 30 px bars separated by 4 px and centered", () => {
  const scale = chartScale(Array.from({ length: 6 }, () => group(10, 10)));
  expect(scale).toMatchObject({ groupWidth: 96, barWidth: 30, groupOffset: 16 });
});

test("the group width adapts to the number of groups and the bars shrink so they still fit", () => {
  const twelve = chartScale(Array.from({ length: 12 }, () => group(10, 10)));
  expect(twelve?.groupWidth).toBe(48);
  expect(twelve?.barWidth).toBe(14);
  expect(twelve!.groupOffset * 2 + twelve!.barWidth * 2 + 4).toBe(twelve!.groupWidth);

  const one = chartScale([group(10, 10)]);
  expect(one?.groupWidth).toBe(576);
  expect(one?.barWidth).toBe(30);
});

test("without groups there is no scale", () => {
  expect(chartScale([])).toBeNull();
});

test.each([
  ["a negative first value", group(-1, 5)],
  ["a negative second value", group(5, -1)],
  ["NaN", group(Number.NaN, 5)],
  ["infinity", group(5, Number.POSITIVE_INFINITY)],
  ["a value that is not a number", { label: "m", first: "5", second: 5 } as unknown as ChartGroup],
  ["a missing value", { label: "m", first: 5 } as unknown as ChartGroup],
])("%s makes the data invalid", (_name, invalid) => {
  expect(chartScale([group(10, 10), invalid])).toBeNull();
});

test("zero is a valid value", () => {
  expect(chartScale([group(0, 0)])).not.toBeNull();
});
