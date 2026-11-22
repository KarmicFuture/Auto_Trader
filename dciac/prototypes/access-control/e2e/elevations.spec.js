const { test, expect } = require("@playwright/test");

async function signIn(page) {
  await page.goto("/");
  await page.evaluate(() => localStorage.removeItem("dciac.world"));
  await page.goto("/");
  await page.locator('[data-user="dsvs.operator"]').click();
  await expect(page.locator(".who strong")).toHaveText("dsvs.operator");
}

test("login and rail drop Vertiv and Avocent branding", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".wordmark")).toContainText("DCIAC");
  await expect(page.locator("body")).not.toContainText("VERTIV");
  await expect(page.locator("body")).not.toContainText("Avocent");
  await expect(page.locator(".product-name")).toHaveText("Access");
  await page.locator('[data-user="dsvs.operator"]').click();
  await expect(page.locator(".rail .wordmark")).toContainText("DCIAC");
  await expect(page.locator(".rail")).not.toContainText("VERTIV");
  await expect(page.locator(".rail")).not.toContainText("Avocent");
  for (const label of ["Overview", "Manage", "Rack", "Port map", "Control", "Sessions", "Audit"]) {
    await expect(page.locator(".rail nav").getByRole("button", { name: label })).toBeVisible();
  }
});

test("elevation strip walks outside through the device", async ({ page }) => {
  await signIn(page);
  const strip = page.locator(".page-head .elevation-nav");
  await expect(strip).toBeVisible();
  await expect(strip.locator('[data-level="site"]')).toHaveAttribute("aria-current", "step");

  await strip.locator('[data-level="hall"]').click();
  await expect(page.locator("h1")).toHaveText("Level 1 · AI Hall");
  await expect(strip.locator('[data-level="hall"]')).toHaveAttribute("aria-current", "step");

  await strip.locator('[data-level="pod"]').click();
  await expect(page.locator(".inspector h2")).toHaveText("AI Pod A");
  await expect(strip.locator('[data-level="pod"]')).toHaveAttribute("aria-current", "step");

  await strip.locator('[data-level="row"]').click();
  await expect(page.locator(".inspector h2")).toHaveText("North row");

  await strip.locator('[data-level="rack"]').click();
  await expect(page.locator(".chassis-top")).toContainText("cold aisle front");
  await expect(strip.locator('[data-face="rear"]')).toBeVisible();

  await strip.locator('[data-face="rear"]').click();
  await expect(page.locator(".chassis-top")).toContainText("hot aisle rear");
  await expect(page.locator(".cabinet.rear")).toBeVisible();

  await strip.locator('[data-level="server"]').click();
  await expect(page.locator(".inspector h2").first()).toBeVisible();
  await expect(strip.locator('[data-level="server"]')).toHaveAttribute("aria-current", "step");

  await page.keyboard.press("[");
  await expect(strip.locator('[data-level="rack"]')).toHaveAttribute("aria-current", "step");
});

test("rack page jumps U positions and switches faces", async ({ page }) => {
  await signIn(page);
  await page.locator('nav [data-view="rack"]').click();
  await expect(page.locator("h1")).toHaveText("Rack A14");
  await expect(page.locator(".rack-nav .elevation-nav")).toBeVisible();
  await expect(page.locator(".elevation h2, .panel h2").first()).toContainText("Cold aisle front");

  await page.getByRole("button", { name: "Hot aisle rear" }).first().click();
  await expect(page.locator(".panel h2").first()).toHaveText("Hot aisle rear");
  await expect(page.locator(".cabinet.rear")).toBeVisible();

  await page.locator('.u-jump [data-device="tray-06"]').click();
  await expect(page.locator(".detail h3")).toHaveText("GPU Tray 06");
  await page.getByRole("button", { name: "Next U" }).click();
  await expect(page.locator(".detail h3")).toHaveText("GPU Tray 07");
});
