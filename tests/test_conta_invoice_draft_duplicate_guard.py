import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "conta_invoice_draft_duplicate_guard.py"
SPEC = importlib.util.spec_from_file_location("duplicate_guard", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class DuplicateGuardTests(unittest.TestCase):
    def test_extracts_complete_hits_and_identifier(self):
        entries = MODULE.extract_draft_entries({"hitCount": 1, "hits": [{"id": 42}]}, 1)
        self.assertEqual(MODULE.extract_draft_identifier(entries[0]), "42")

    def test_incomplete_or_summary_only_list_is_ambiguous(self):
        with self.assertRaisesRegex(MODULE.DuplicateGuardError, "entries_missing"):
            MODULE.extract_draft_entries({"hitCount": 1}, 1)
        with self.assertRaisesRegex(MODULE.DuplicateGuardError, "entries_incomplete"):
            MODULE.extract_draft_entries({"hitCount": 2, "hits": [{"id": 1}]}, 2)

    def test_exact_marker_is_a_duplicate(self):
        detail = {"invoiceDraftLines": [{"description": "Conta MCP First Production Validation"}]}
        self.assertTrue(
            MODULE.detail_contains_line_description(detail, "Conta MCP First Production Validation")
        )

    def test_unrelated_marker_is_proven_nonmatching(self):
        detail = {"data": {"lines": [{"description": "Existing operator draft"}]}}
        self.assertFalse(
            MODULE.detail_contains_line_description(detail, "Conta MCP First Production Validation")
        )

    def test_missing_line_evidence_is_ambiguous(self):
        with self.assertRaisesRegex(MODULE.DuplicateGuardError, "lines_missing"):
            MODULE.detail_contains_line_description({"id": 42}, "marker")
        with self.assertRaisesRegex(MODULE.DuplicateGuardError, "description_missing"):
            MODULE.detail_contains_line_description({"lines": [{"price": 1}]}, "marker")


if __name__ == "__main__":
    unittest.main()
