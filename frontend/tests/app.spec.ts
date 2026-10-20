import { execFileSync } from "node:child_process";
import path from "node:path";
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
  await page.getByRole("button", { name: "Load example" }).click();
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
  await page.getByRole("button", { name: "Load example" }).click();
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
  await expect(
    page.getByRole("region", { name: "Champion reference" }),
  ).toContainText("Camille");
  await expect(page.locator(".matchup-badge")).toHaveCount(0);
});

test("all roles work with partial drafts and jungle disables lane opponent", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Load example" }).click();
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
    await expect(page.locator(".recommendation-card")).toHaveCount(
      role === "ADC" ? 4 : 3,
    );
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
  await page.getByRole("button", { name: "Load example" }).click();
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
  await page.getByRole("button", { name: "Load example" }).click();
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
  await page.getByRole("button", { name: "Load example" }).click();
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
    page.getByRole("region", { name: "Champion reference" }),
  ).toBeVisible();
});

test("ADC default pool has four picks and cited opponent advice", async ({
  page,
}) => {
  await page.goto("/");
  for (const name of ["Draven", "Twitch", "Caitlyn", "Ashe"]) {
    await expect(
      page.getByRole("combobox", { name: `${name} comfort` }),
    ).toBeVisible();
  }
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(page.locator(".recommendation-card")).toHaveCount(4);
  for (const name of ["Draven", "Twitch", "Caitlyn", "Ashe"]) {
    await page
      .locator(".recommendation-card")
      .filter({ hasText: name })
      .click();
    const notebook = page.getByRole("region", { name: "ADC matchup notebook" });
    await expect(notebook).toContainText("Against Jhin");
    await expect(notebook).toContainText("Enemy threat: Nautilus");
    await expect(
      notebook.getByRole("link", { name: "Mobalytics: Jhin counters" }),
    ).toHaveAttribute(
      "href",
      "https://mobalytics.gg/lol/champions/jhin/counters",
    );
  }
  await page.screenshot({
    path: `${artifacts}/adc-notebook-desktop.png`,
    fullPage: true,
  });
  await page.getByRole("tab", { name: "Build & runes" }).click();
  await expect(
    page.getByRole("region", { name: "ADC build decisions" }),
  ).toContainText("not this particular opponent");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("tab", { name: "Game plan" }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `${artifacts}/adc-notebook-mobile.png`,
    fullPage: true,
  });
});

test("saved ADC drafts survive reload and preserve empty role slots", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Remove allied Ornn", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Draven comfort" })
    .selectOption("5");
  await page
    .getByRole("textbox", { name: "Draft name" })
    .fill("Saved ADC lane");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Load Saved ADC lane", exact: true }),
  ).toBeVisible();
  await page.reload();
  await page
    .getByRole("button", { name: "Load Saved ADC lane", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Select allied Top", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Select allied Jungle: Vi", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("combobox", { name: "Draven comfort" }),
  ).toHaveValue("5");
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await expect(
    page.getByRole("region", { name: "Champion reference" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Back to draft", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Delete Saved ADC lane", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Load Saved ADC lane", exact: true }),
  ).toHaveCount(0);
});

test("imported Onetricks evidence displays champion perspective and missing builds", async ({
  page,
}) => {
  const python = path.resolve(
    process.platform === "win32"
      ? "../.venv/Scripts/python.exe"
      : "../.venv/bin/python",
  );
  execFileSync(
    python,
    [
      path.resolve("../backend/scripts/import_onetricks.py"),
      path.resolve("../backend/app/data/onetricks_reviewed.json"),
    ],
    {
      env: {
        ...process.env,
        DATABASE_PATH:
          process.env.DATABASE_PATH ||
          path.resolve("../.test-artifacts/browser-tests.sqlite3"),
      },
    },
  );
  await page.goto("/");
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  await page
    .locator(".recommendation-card")
    .filter({ hasText: "Draven" })
    .click();
  const evidence = page.getByRole("region", {
    name: "Onetricks matchup evidence",
  });
  await expect(evidence).toContainText("55.8%");
  await expect(evidence).toContainText("1,022");
  await expect(evidence).toContainText("Patch: Unknown");
  await expect(evidence).not.toContainText(
    "No verified matchup-specific item or rune record",
  );
  await expect(
    evidence.getByRole("link", { name: "View observation source" }),
  ).toHaveAttribute(
    "href",
    "https://www.onetricks.gg/champions/counter/Draven",
  );
  await page.screenshot({
    path: `${artifacts}/onetricks-desktop.png`,
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `${artifacts}/onetricks-mobile.png`,
    fullPage: true,
  });
});

test("all-roster champion shows real kit data without empty evidence panels", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Mid", exact: true }).click();
  const response = await page.request.post(
    "http://127.0.0.1:8000/api/analyze",
    {
      data: {
        role: "mid",
        championPool: ["Akali"],
        allies: [],
        enemies: ["Ahri"],
        laneOpponent: "Ahri",
        comfort: {},
      },
    },
  );
  expect(response.ok()).toBeTruthy();
  const analysis = await response.json();
  await page.route("**/api/analyze", (route) =>
    route.fulfill({ json: analysis }),
  );
  await page
    .getByRole("button", { name: "Analyze draft", exact: true })
    .click();
  const kit = page.getByRole("region", { name: "Champion reference" });
  await expect(kit).toContainText("Assassin's Mark");
  await expect(kit).toContainText("Five Point Strike");
  await expect(kit).toContainText("Ahri");
  await expect(
    page.getByRole("heading", { name: "Observed performance" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("region", { name: "Onetricks matchup evidence" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Lane matchup", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("tab", { name: "Build & runes" }).click();
  await expect(page.getByRole("heading", { name: "Rune page" })).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "Core items", exact: true }),
  ).toHaveCount(0);
  await expect(kit.getByRole("link", { name: "OP.GG builds" })).toHaveAttribute(
    "href",
    "https://op.gg/lol/champions/akali/build/mid",
  );
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: `${artifacts}/champion-toolkit-mobile.png`,
    fullPage: true,
  });
});
