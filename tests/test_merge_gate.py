import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MergeGateFiles(unittest.TestCase):
    def test_gate_files_present_and_valid(self):
        self.assertTrue((ROOT / ".cursor/hooks/merge-gate.mjs").is_file())
        hooks = (ROOT / ".cursor/hooks.json").read_text(encoding="utf-8-sig")
        self.assertIn("merge-gate.mjs", hooks)
        json.loads(hooks)
        settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8-sig"))
        self.assertTrue(settings["enabledPlugins"]["merge-gate@nercari"])


if __name__ == "__main__":
    unittest.main()
