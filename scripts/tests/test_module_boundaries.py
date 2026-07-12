from __future__ import annotations

import ast
import json
import unittest

from scripts import check_module_boundaries as boundaries


class ModuleBoundaryTests(unittest.TestCase):
    def test_repository_module_boundaries_are_valid(self) -> None:
        self.assertEqual([], boundaries.validate())

    def test_application_cannot_import_persistence(self) -> None:
        self.assertFalse(
            boundaries.layer_dependency_allowed("application", "persistence", "app/validation.py")
        )

    def test_http_can_depend_on_application_but_not_persistence(self) -> None:
        self.assertTrue(boundaries.layer_dependency_allowed("http", "application", "app/http/api.py"))
        self.assertFalse(boundaries.layer_dependency_allowed("http", "persistence", "app/http/api.py"))

    def test_cross_capability_write_catalog_fails(self) -> None:
        ownership, _ = boundaries.load_policies()
        catalog = {
            "BAD": {
                "owner": "invoices",
                "writeTables": ["invoice_versions", "validation_runs"],
            }
        }
        self.assertTrue(boundaries.validate_catalog(catalog, ownership))

    def test_table_owner_mismatch_fails(self) -> None:
        ownership, _ = boundaries.load_policies()
        catalog = {
            "BAD": {"owner": "workflow", "writeTables": ["invoice_versions"]}
        }
        self.assertTrue(boundaries.validate_catalog(catalog, ownership))

    def test_sql_cannot_touch_an_undeclared_foreign_table(self) -> None:
        ownership, _ = boundaries.load_policies()
        catalog = json.loads(boundaries.CATALOG_PATH.read_text())
        name = next(
            key
            for key, value in catalog.items()
            if value["owner"] == "invoices" and value["operation"] == "read"
        )
        catalog[name]["sql"] = "select id from validation_runs"
        failures = boundaries.validate_catalog(catalog, ownership)
        self.assertTrue(any("metadata differs from SQL" in failure for failure in failures))

    def test_sql_footprint_ignores_cte_names_and_finds_the_write_target(self) -> None:
        reads, writes = boundaries.sql_footprint(
            "with next as (select id from ingestion_jobs for update skip locked) "
            "update ingestion_jobs j set status='running' from next where j.id=next.id"
        )
        self.assertEqual({"ingestion_jobs"}, reads)
        self.assertEqual({"ingestion_jobs"}, writes)

    def test_absolute_and_from_package_imports_resolve_to_physical_modules(self) -> None:
        source = boundaries.APP_ROOT / "application/commands/validation.py"
        absolute = ast.parse("import app.adapters.persistence.postgres").body[0]
        from_package = ast.parse(
            "from app.adapters.persistence import postgres"
        ).body[0]
        expected = boundaries.APP_ROOT / "adapters/persistence/postgres.py"
        self.assertIn(expected, boundaries._imported_module_paths(source, absolute))
        self.assertIn(expected, boundaries._imported_module_paths(source, from_package))


if __name__ == "__main__":
    unittest.main()
