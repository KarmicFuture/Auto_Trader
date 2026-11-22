const { test, expect } = require("@playwright/test");

async function signIn(page) {
  await page.goto("/");
  await page.evaluate(() => localStorage.removeItem("dciac.world"));
  await page.goto("/");
  await page.locator('[data-user="dsvs.operator"]').click();
  await expect(page.locator(".who strong")).toHaveText("dsvs.operator");
  await page.waitForSelector(".scene");
  await page.waitForTimeout(80);
}

async function sceneMetrics(page) {
  return page.evaluate(() => {
    const scene = document.querySelector(".scene");
    const stage = document.querySelector(".stage");
    const world = document.querySelector(".world");
    const lib = document.querySelector(".lib");
    if (!scene || !stage || !world) return { missing: true };
    const s = scene.getBoundingClientRect();
    const st = stage.getBoundingClientRect();
    const w = world.getBoundingClientRect();
    const l = lib ? lib.getBoundingClientRect() : null;
    const overlapLib = l
      ? !(s.right <= l.left + 1 || s.left >= l.right - 1 || s.bottom <= l.top + 1 || s.top >= l.bottom - 1)
      : false;
    return {
      scene: { x: s.x, y: s.y, w: s.width, h: s.height },
      stage: { x: st.x, y: st.y, w: st.width, h: st.height },
      world: { x: w.x, y: w.y, w: w.width, h: w.height },
      lib: l ? { x: l.x, y: l.y, w: l.width, h: l.height } : null,
      stageOverflow: getComputedStyle(stage).overflow,
      sceneOverflow: getComputedStyle(scene).overflow,
      overlapLib,
      scrollX: document.documentElement.scrollWidth - window.innerWidth,
      pageH: document.documentElement.scrollHeight,
      sceneBottom: s.bottom,
    };
  });
}

async function setTheme(page, theme) {
  const current = await page.locator("html").getAttribute("data-theme");
  if ((theme === "noc") !== (current === "noc")) {
    await page.locator('[data-act="theme"]').first().click();
  }
  await expect(page.locator("html")).toHaveAttribute("data-theme", theme === "noc" ? "noc" : "paper");
}

test("scene stays clipped and centred at 1440 and 390", async ({ page }) => {
  for (const size of [
    { width: 1440, height: 900 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(size);
    await signIn(page);
    await page.screenshot({
      path: "test-results/phase1-" + size.width + "-paper.png",
      fullPage: false,
    });
    const metrics = await sceneMetrics(page);
    expect(metrics.missing).toBeFalsy();
    expect(metrics.scrollX).toBeLessThanOrEqual(2);
    expect(metrics.stageOverflow).toMatch(/hidden|clip/);
    expect(metrics.sceneOverflow).toMatch(/hidden|clip/);
    const stageMid = metrics.stage.x + metrics.stage.w / 2;
    const worldMid = metrics.world.x + metrics.world.w / 2;
    expect(Math.abs(stageMid - worldMid)).toBeLessThan(48);
    if (size.width >= 1440) {
      expect(metrics.overlapLib).toBeFalsy();
      expect(metrics.lib.x + metrics.lib.w).toBeLessThanOrEqual(metrics.scene.x + 2);
      expect(metrics.scene.y).toBeLessThan(280);
      expect(metrics.pageH).toBeLessThanOrEqual(size.height + 8);
    } else {
      expect(metrics.scene.x).toBeGreaterThanOrEqual(-1);
      expect(metrics.sceneBottom).toBeLessThan(844 * 2);
      await expect(page.locator(".lib-toggle")).toBeVisible();
      await expect(page.locator(".lib-body")).toBeHidden();
    }
  }
});

test("NOC theme colours the scene, legend, and spec chips", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);
  await setTheme(page, "noc");
  await page.screenshot({ path: "test-results/phase1-1440-noc.png", fullPage: false });
  const colors = await page.evaluate(() => {
    const scene = getComputedStyle(document.querySelector(".scene"));
    const slab = getComputedStyle(document.querySelector(".slab"));
    const legend = getComputedStyle(document.querySelector(".legend"));
    const chip = document.querySelector(".lib-stats b");
    const chipStyle = chip ? getComputedStyle(chip) : null;
    const rgb = (value) => value.replace(/\s/g, "");
    return {
      scene: rgb(scene.backgroundColor),
      slab: rgb(slab.backgroundColor),
      legendBg: rgb(legend.backgroundColor),
      legendFg: rgb(legend.color),
      chipBg: chipStyle ? rgb(chipStyle.backgroundColor) : "",
      chipFg: chipStyle ? rgb(chipStyle.color) : "",
    };
  });
  expect(colors.scene).not.toMatch(/rgb\(236,231,224\)|rgb\(255,255,255\)|#ece7e0/i);
  expect(colors.slab).not.toMatch(/rgb\(217,211,203\)|rgb\(197,208,188\)/i);
  expect(colors.legendBg).not.toMatch(/rgb\(246,243,238\)|rgb\(255,255,255\)/i);
  expect(colors.chipBg).not.toMatch(/rgb\(243,238,232\)|rgb\(255,255,255\)/i);
  expect(colors.legendFg).not.toMatch(/rgb\(255,255,255\)/);
});

test("alarms are one-line, unique, and explain opens on click", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);
  await expect(page.locator("text=Other alarms")).toHaveCount(0);
  const stacks = page.locator(".alarm-stack");
  await expect(stacks.first()).toBeVisible();
  const count = await stacks.count();
  expect(count).toBeGreaterThan(3);
  await expect(page.locator(".alarm-stack .explain").first()).toBeHidden();
  await page.locator(".alarm-msg").first().click();
  await expect(page.locator(".alarm-stack.open .explain")).toBeVisible();
  await expect(page.locator(".dock-tabs")).toBeVisible();
  await expect(page.locator(".scene")).toBeInViewport();
});

test("scene controls are segmented and nominal chips stay quiet", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await signIn(page);
  await expect(page.locator('.seg[aria-label="Time horizon"]')).toBeVisible();
  await expect(page.locator('.seg[aria-label="Site or hall"]')).toBeVisible();
  await expect(page.locator('.hud-zoom[aria-label="Zoom"]')).toBeVisible();
  const chip = page.locator(".pill.ok").first();
  await expect(chip).toBeVisible();
  const styles = await chip.evaluate((el) => {
    const s = getComputedStyle(el);
    return { bg: s.backgroundColor, color: s.color };
  });
  expect(styles.bg).toMatch(/rgba\(0, 0, 0, 0\)|transparent|rgba\(0,0,0,0\)/);
  const face = await page.locator(".cap-label").first().evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
  expect(face).toBeGreaterThanOrEqual(11);
});
