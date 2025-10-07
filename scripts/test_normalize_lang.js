// Minimal standalone test for normalizeLang from
// frontend/src/plugins/translationsPlugin.js

function normalizeLang(input) {
  if (!input) return "en";
  let s = String(input);
  // unify separators first (all hyphens)
  s = s.replaceAll ? s.replaceAll("-", "_") : s.replace(/-/g, "_");
  const lower = s.toLowerCase();
  // Region-specific codes that Frappe expects with underscore
  const special = {
    pt_br: "pt_BR",
    zh_tw: "zh_TW",
    sr_cs: "sr_CS",
    zh_cn: "zh_CN",
  };
  if (special[lower]) return special[lower];
  // default to two-letter base (e.g., vi, de, fr)
  return lower.length >= 2 ? lower.slice(0, 2) : lower;
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    console.error(`✗ ${label}: expected ${expected}, got ${actual}`);
    process.exitCode = 1;
  } else {
    console.log(`✓ ${label}: ${actual}`);
  }
}

function run() {
  assertEqual(normalizeLang("vi"), "vi", "vi base");
  assertEqual(normalizeLang("vi-VN"), "vi", "vi-VN hyphen");
  assertEqual(normalizeLang("vi_VN"), "vi", "vi_VN underscore");
  assertEqual(normalizeLang("de"), "de", "de base");
  assertEqual(normalizeLang("de-DE"), "de", "de-DE region");
  assertEqual(normalizeLang("pt-BR"), "pt_BR", "pt-BR special");
  assertEqual(normalizeLang("zh-TW"), "zh_TW", "zh-TW special");
  assertEqual(normalizeLang("zh-cn"), "zh_CN", "zh-cn special lower");
  assertEqual(normalizeLang("fr-CA"), "fr", "fr-CA fallback base");
  assertEqual(normalizeLang("EN-us"), "en", "EN-us normalize");
  assertEqual(normalizeLang(""), "en", "empty input");
  assertEqual(normalizeLang(undefined), "en", "undefined input");
  assertEqual(normalizeLang("x"), "x", "single-char input");
  // multi-hyphen input should not throw and still reduce to base
  assertEqual(normalizeLang("en-US-x-custom"), "en", "multi-hyphen reduces to base");
}

run();

