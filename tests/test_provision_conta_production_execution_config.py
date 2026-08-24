import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "provision_conta_production_execution_config.py"
SPEC = importlib.util.spec_from_file_location("execution_config", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


BASE = b"""<?php
return [
    'mcp_bearer_token' => 'opaque-token',
    'approval_signing_key' => '12345678901234567890123456789012',
    'approval_key_id' => 'production-key-v1',
    'release_commit' => '19d8b9fd3e7aec7fec7405df2ffec0e72839c9ac',
    'write_policy_version' => '2026-08-19-production-gate1',
    'enable_write_tools' => false,
    'runtime_write_blocked' => true,
    'execution_allowed' => false,
    'production_write_approved' => false,
];
"""


class ExecutionConfigTests(unittest.TestCase):
    def test_adds_exact_execution_metadata_and_remains_closed(self):
        updated = MODULE.update_config(BASE)
        text = updated.decode()
        MODULE.assert_closed_and_ready(text, metadata_required=True)
        self.assertIn(MODULE.SCHEMA_SHA256, text)
        self.assertIn(MODULE.CREATE_ROUTE, text)
        self.assertIn(MODULE.READBACK_ROUTE, text)

    def test_replaces_existing_values_without_duplicates(self):
        existing = BASE.replace(b"];", b"    'provider_schema_sha256' => 'old',\n    'create_invoice_draft_route' => 'old',\n    'readback_invoice_draft_route' => 'old',\n];")
        text = MODULE.update_config(existing).decode()
        MODULE.assert_closed_and_ready(text, metadata_required=True)
        self.assertEqual(text.count("'provider_schema_sha256' =>"), 1)
        self.assertEqual(text.count("'create_invoice_draft_route' =>"), 1)
        self.assertEqual(text.count("'readback_invoice_draft_route' =>"), 1)

    def test_open_runtime_is_rejected(self):
        opened = MODULE.update_config(BASE.replace(b"'enable_write_tools' => false", b"'enable_write_tools' => true"))
        with self.assertRaisesRegex(MODULE.Stop, "runtime_not_fail_closed:enable_write_tools"):
            MODULE.assert_closed_and_ready(opened.decode(), metadata_required=True)


if __name__ == "__main__":
    unittest.main()
