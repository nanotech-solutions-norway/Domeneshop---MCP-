import importlib.util
import pathlib
import sys
import types
import unittest


sys.modules.setdefault("certifi", types.SimpleNamespace(where=lambda: ""))
SCRIPTS = pathlib.Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "reconcile_conta_first_production_invoice_draft.py"
SPEC = importlib.util.spec_from_file_location("reconcile", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ReconciliationTests(unittest.TestCase):
    def test_controlled_fields_match(self):
        draft = {
            "registrationSource": "CONTA",
            "type": "NORMAL",
            "invoiceLanguage": "NO",
            "invoiceCurrency": "NOK",
            "customerId": 123,
            "invoiceDraftLines": [{
                "description": MODULE.LINE_DESCRIPTION,
                "price": 1.0,
                "quantity": 1,
                "discount": 0,
                "vatCode": "high",
                "lineNo": 1,
            }],
        }
        MODULE.assert_controlled_fields(draft, "123", "high")

    def test_mismatch_fails_closed(self):
        draft = {
            "registrationSource": "CONTA",
            "type": "NORMAL",
            "invoiceLanguage": "NO",
            "invoiceCurrency": "NOK",
            "customerId": 123,
            "lines": [{
                "description": MODULE.LINE_DESCRIPTION,
                "price": 1.01,
                "quantity": 1,
                "discount": 0,
                "vatCode": "high",
                "lineNo": 1,
            }],
        }
        with self.assertRaisesRegex(MODULE.Stop, "readback_price_mismatch"):
            MODULE.assert_controlled_fields(draft, "123", "high")

    def test_controlled_draft_requires_one_candidate(self):
        with self.assertRaisesRegex(MODULE.Stop, "candidate_count_0"):
            MODULE.controlled_draft({"id": 1})


if __name__ == "__main__":
    unittest.main()
