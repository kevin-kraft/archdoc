from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from archdoc.scanner.python_scanner import scan_project

from conftest import make_config, write_file


class PythonScannerTests(TestCase):
    def test_scanner_extracts_modern_function_syntax_without_nested_scope_leakage(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/accounts.py",
                """
                from sqlalchemy import select

                class User: ...

                class AccountService:
                    async def load_user(self, user_id: int, /, payload: dict | None = None, *, dry_run: bool = False, **kwargs) -> list[str]:
                        selected: User = User()

                        def local_helper():
                            helper_service = HiddenService()
                            helper_service.should_not_be_seen()

                        result = await self.db.execute(select(User).where(User.id == user_id))
                        return [str(result), str(selected), str(dry_run), str(kwargs)]
                """,
            )

            facts = scan_project(make_config(project_root))
            service_file = facts.files[0]
            method = service_file.classes[1].methods[0]

            parameters = {parameter.name: parameter for parameter in method.parameters}
            self.assertEqual(parameters["user_id"].kind, "positional_only")
            self.assertEqual(parameters["payload"].annotation, "dict | None")
            self.assertEqual(parameters["dry_run"].kind, "keyword_only")
            self.assertEqual(parameters["kwargs"].kind, "kwarg")
            self.assertEqual(method.returns, "list[str]")

            call_names = {call.name for call in method.calls}
            self.assertIn("self.db.execute", call_names)
            self.assertIn("select", call_names)
            self.assertNotIn("HiddenService", call_names)
            self.assertNotIn("helper_service.should_not_be_seen", call_names)

            assignments = {assignment.target: assignment for assignment in method.assignments}
            self.assertEqual(assignments["selected"].value_call, "User")
            self.assertNotIn("helper_service", assignments)

            self.assertEqual(
                [call.name for call in method.calls if call.name in {"self.db.execute", "select"}],
                ["self.db.execute", "select"],
            )

            execute_call = next(call for call in method.calls if call.name == "self.db.execute")
            select_call = next(call for call in method.calls if call.name == "select")
            self.assertTrue(execute_call.awaited)
            self.assertFalse(execute_call.nested_in_call)
            self.assertTrue(select_call.nested_in_call)
