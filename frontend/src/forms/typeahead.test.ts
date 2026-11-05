import { createTypeahead } from "./typeahead";

const COUNTRIES = ["Ecuador", "España", "Estonia", "Perú", "Portugal", "Österreich"];

function clock() {
  let time = 0;
  return { now: () => time, advance: (ms: number) => void (time += ms) };
}

test("finds the first option that starts with the key, ignoring case and accents", () => {
  const { now } = clock();
  const find = createTypeahead(now);

  expect(find("p", COUNTRIES, 0)).toBe(3);
});

test("keys typed in less than 500 ms add up", () => {
  const time = clock();
  const find = createTypeahead(time.now);

  find("p", COUNTRIES, 0);
  time.advance(200);
  expect(find("o", COUNTRIES, 3)).toBe(4);
  time.advance(200);
  find("r", COUNTRIES, 4);
  time.advance(200);
  expect(find("u", COUNTRIES, 4)).toBe(-1);
});

test("an accented word is found without its accents", () => {
  const time = clock();
  const find = createTypeahead(time.now);

  find("p", COUNTRIES, 0);
  time.advance(100);
  find("e", COUNTRIES, 3);
  time.advance(100);
  find("r", COUNTRIES, 3);
  time.advance(100);
  expect(find("u", COUNTRIES, 3)).toBe(3);
});

test("letters typed after an accented one are still matched", () => {
  const time = clock();
  const find = createTypeahead(time.now);

  find("o", COUNTRIES, 0);
  time.advance(100);
  expect(find("s", COUNTRIES, 5)).toBe(5);
});

test("after 500 ms the search starts again", () => {
  const time = clock();
  const find = createTypeahead(time.now);

  find("p", COUNTRIES, 0);
  time.advance(500);

  expect(find("e", COUNTRIES, 3)).toBe(0);
});

test("repeating the same letter goes through the options that start with it", () => {
  const time = clock();
  const find = createTypeahead(time.now);

  expect(find("e", COUNTRIES, 4)).toBe(0);
  time.advance(100);
  expect(find("e", COUNTRIES, 0)).toBe(1);
  time.advance(100);
  expect(find("e", COUNTRIES, 1)).toBe(2);
  time.advance(100);
  expect(find("e", COUNTRIES, 2)).toBe(0);
});

test("without a match it gives -1", () => {
  expect(createTypeahead(clock().now)("z", COUNTRIES, 0)).toBe(-1);
});
