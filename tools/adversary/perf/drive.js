// Drive the probe build in Chromium: start page click, autopilot plays, collect per-frame records.
// Usage: node drive.js <query> <seconds> <outfile> [headed]
// PLAYWRIGHT_MODULE and CHROME_PATH override the defaults: Playwright from local/piskel (gitignored) and the system Chromium.
const path = require("path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || path.resolve(__dirname, "../../../local/piskel/node_modules/playwright"));
const fs = require("fs");

const [query, seconds, out] = [process.argv[2], Number(process.argv[3]), process.argv[4]];

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || "/opt/playwright/chromium-1247/chrome-linux64/chrome",
    headless: true,
    args: ["--autoplay-policy=no-user-gesture-required", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const logs = [];
  page.on("console", (m) => { const t = m.text(); if (!t.startsWith("PROBE")) logs.push(t); });
  await page.goto("http://localhost:6081/" + query, { waitUntil: "load" });
  // Wait for the start page to be ready, then press a key on the page (the gesture).
  for (let i = 0; i < 900; i++) {
    await page.waitForTimeout(1000);
    const ready = await page.evaluate(() => typeof window.__probe !== "undefined" || document.body.innerText.includes("PRESS") || document.body.innerText.includes("CLICK"));
    if (ready) break;
  }
  await page.mouse.click(640, 400);
  await page.keyboard.press("Enter");
  for (let i = 0; i < 900; i++) {
    await page.waitForTimeout(1000);
    const n = await page.evaluate(() => (window.__probe ? window.__probe.length : -1));
    if (n > 60) break;
    if (i % 5 === 4) { await page.mouse.click(640, 400); await page.keyboard.press("Enter"); }
  }
  // JS-side rAF gaps over the same window, independent of Python.
  await page.evaluate(() => {
    window.__raf = [];
    let last = performance.now();
    const f = (t) => { window.__raf.push(+(t - last).toFixed(2)); last = t; requestAnimationFrame(f); };
    requestAnimationFrame(f);
    window.__probe.length = 0;
  });
  const t0 = Date.now();
  while (Date.now() - t0 < seconds * 1000) {
    await page.waitForTimeout(30000);
    const st = await page.evaluate(() => { const p = window.__probe; return [p.length, p.length ? p[p.length - 1].split(",").slice(-1)[0] : ""]; });
    console.log(`t=${Math.round((Date.now() - t0) / 1000)}s frames=${st[0]} last=${st[1]}`);
    if (String(st[1]).startsWith("8|") && String(st[1]).split("|")[4] === "1" && process.env.STOP_AFTER_TAIL_S && !global.tailAt) global.tailAt = Date.now();
    if (global.tailAt && Date.now() - global.tailAt > Number(process.env.STOP_AFTER_TAIL_S) * 1000) break;
  }
  const data = await page.evaluate(() => ({
    probe: window.__probe.slice(),
    raf: window.__raf.slice(),
    meta: { opts: String(window.__probe_meta.opts), py: String(window.__probe_meta.py) },
    audio: (() => {
      try {
        const out = [];
        if (window.MM) for (const k in window.MM) { const m = window.MM[k]; if (m && m.media) out.push({ k, paused: m.media.paused, t: m.media.currentTime }); }
        return out;
      } catch (e) { return String(e); }
    })(),
  }));
  data.logs = logs.filter((l) => /WARN|ERROR|audio|music|violation|Traceback/i.test(l)).slice(0, 40);
  fs.writeFileSync(out, JSON.stringify(data));
  console.log("frames", data.probe.length, "raf", data.raf.length, JSON.stringify(data.audio), data.meta.py);
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
