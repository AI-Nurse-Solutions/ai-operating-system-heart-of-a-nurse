"""Design tokens meet their declared contrast minimums (NM-002)."""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "design" / "tokens.json"
sys.path.insert(0, str(ROOT / "tools"))
import gen_tokens_css  # noqa: E402


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(fg: str, bg: str) -> float:
    hi, lo = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class DesignTokenTests(unittest.TestCase):
    def setUp(self):
        self.tokens = json.loads(TOKENS.read_text(encoding="utf-8"))

    def test_every_declared_pair_meets_its_minimum(self):
        for req in self.tokens["contrast_requirements"]:
            theme = self.tokens["themes"][req["theme"]]
            ratio = contrast(theme[req["fg"]], theme[req["bg"]])
            with self.subTest(**req):
                self.assertGreaterEqual(round(ratio, 2), req["min"])

    def test_body_text_pairs_require_aa(self):
        for req in self.tokens["contrast_requirements"]:
            if not req["use"].startswith("non-text") and ("text" in req["use"] or "label" in req["use"]):
                with self.subTest(**req):
                    self.assertGreaterEqual(req["min"], 4.5)

    def test_the_review_orange_is_never_declared_as_text(self):
        for req in self.tokens["contrast_requirements"]:
            if req["fg"] == "accent-review" and req["theme"] == "day":
                with self.subTest(**req):
                    self.assertIn("non-text", req["use"])
        day = self.tokens["themes"]["day"]
        self.assertLess(contrast(day["accent-review"], day["canvas"]), 4.5)

    def test_renderer_uses_the_generated_tokens_only(self):
        self.assertEqual((ROOT / "renderer" / "tokens.css").read_text(encoding="utf-8"),
                         gen_tokens_css.generate(), "run: python3 nurse-manager/tools/gen_tokens_css.py")
        css = (ROOT / "renderer" / "renderer.css").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", css), [], "raw colors bypass the tested tokens")
        self.assertNotRegex(css, r"rgba?\(|hsla?\(", "raw colors bypass the tested tokens")

    def test_spacing_is_on_the_eight_pixel_grid(self):
        self.assertTrue(all(v % 8 == 0 for v in self.tokens["spacing"]["scale"]))


if __name__ == "__main__":
    unittest.main()
