import { test, expect } from "@playwright/test";
import fs from "node:fs";
const artifacts = "../.test-artifacts";
test.beforeAll(() => fs.mkdirSync(artifacts, { recursive: true }));

test("example draft produces ranked picks, builds, and transparent scores", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Analyze draft", exact: true }),
  ).toBeEnabled();
  await expect(
    page.getByRole("combobox", { name: "Your lane opponent" }),
  ).toHaveValue("Darius");
  await page.screenshot({
    path: `${artifacts}/draft-desktop.png`,
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "A pick with a purpose." }),
  ).toBeVisible();
  await expect(page.locator(".recommendation-card")).toHaveCount(3);
  await expect(
    page.getByRole("heading", { name: "Lane matchup", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: `${artifacts}/results-desktop.png`,
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Build & runes" }).click();
  await expect(page.getByRole("heading", { name: "Rune page" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Core items", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".rune-trees p")).toHaveCount(5);
  await page.getByRole("tab", { name: "Score breakdown" }).click();
  await expect(page.locator(".factor")).toHaveCount(11);
  await page.locator(".recommendation-card").nth(1).click();
  await expect(page.locator(".recommendation-card").nth(1)).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("button", { name: "Back to draft" }).click();
  await expect(
    page.getByRole("combobox", { name: "Your lane opponent" }),
  ).toHaveValue("Darius");
  expect(errors).toEqual([]);
});

test("search, pool editing, comfort, draft changes, and duplicate prevention", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("combobox", { name: "Ornn comfort" }).selectOption("5");
  await page.getByRole("button", { name: "Edit pool" }).click();
  await page.getByRole("textbox", { name: "Search champions" }).fill("Gwen");
  await page.getByRole("button", { name: /Gwen Top/ }).click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(
    page.getByRole("combobox", { name: "Gwen comfort" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Select enemy Top: Darius", exact: true })
    .click();
  await page.getByRole("textbox", { name: "Search champions" }).fill("Jinx");
  await expect(
    page.getByRole("button", { name: /Jinx Already picked/ }),
  ).toBeDisabled();
  await page.getByRole("textbox", { name: "Search champions" }).fill("Camille");
  await page.getByRole("button", { name: /Camille Top/ }).click();
  await expect(
    page.getByRole("combobox", { name: "Your lane opponent" }),
  ).toHaveValue("");
  await page
    .getByRole("combobox", { name: "Your lane opponent" })
    .selectOption("Camille");
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(page.locator(".matchup-badge")).toHaveText("Unrated");
});

test("all roles work with partial drafts and jungle disables lane opponent", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Analyze draft", exact: true }),
  ).toBeEnabled();
  for (const role of ["Jungle", "Mid", "ADC", "Support"]) {
    await page.getByRole("button", { name: role, exact: true }).click();
    if (role === "Jungle")
      await expect(
        page.getByRole("combobox", { name: "Your lane opponent" }),
      ).toBeDisabled();
    await page
      .getByRole("button", { name: "Analyze draft", exact: true })
      .click();
    await expect(page.locator(".recommendation-card")).toHaveCount(3);
    await expect(
      page.getByText(/Partial draft: scores may change/),
    ).toBeVisible();
    await page.getByRole("button", { name: "Back to draft" }).click();
  }
});

test("empty pool prevents analysis and failed requests stay recoverable", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Edit pool" }).click();
  for (const name of ["Ornn", "Garen", "Malphite", "Mordekaiser"])
    await page
      .getByRole("button", { name: new RegExp(`^${name} (Top.*)$`) })
      .click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Analyze draft", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Load example" }).click();
  await page.route("**/api/analyze", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Temporary test failure. Try again." }),
    }),
  );
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("Temporary test failure");
  await expect(
    page.getByRole("button", { name: "Analyze draft", exact: true }),
  ).toBeEnabled();
  await page.unroute("**/api/analyze");
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(page.locator(".recommendation-card")).toHaveCount(3);
});

test("mobile layout, keyboard dialog, and results have no horizontal overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Analyze draft", exact: true }),
  ).toBeEnabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `${artifacts}/draft-mobile.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Edit pool" }).click();
  await expect(
    page.getByRole("textbox", { name: "Search champions" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator("dialog")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(page.locator(".recommendation-card")).toHaveCount(3);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `${artifacts}/results-mobile.png`,
    fullPage: true,
  });
});

test("full roster champions can be searched, picked, and analyzed", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Mid", exact: true }).click();
  await page.getByRole("button", { name: "Edit pool" }).click();
  await page.getByRole("textbox", { name: "Search champions" }).fill("Akali");
  await page.getByRole("button", { name: /Akali/ }).click();
  await page.getByRole("textbox", { name: "Search champions" }).fill("Locke");
  await expect(page.getByRole("button", { name: /Locke/ })).toBeVisible();
  await page.getByRole("button", { name: /Locke/ }).click();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(
    page.getByRole("combobox", { name: "Akali comfort" }),
  ).toBeVisible();
  await expect(
    page.getByRole("combobox", { name: "Locke comfort" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Select enemy Top", exact: true })
    .click();
  await page.getByRole("textbox", { name: "Search champions" }).fill("Zaahen");
  await page.getByRole("button", { name: /Zaahen/ }).click();
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(page.locator(".recommendation-card")).toHaveCount(3);
  await expect(
    page.getByRole("region", { name: "Recommendation statistics" }),
  ).toBeVisible();
});
