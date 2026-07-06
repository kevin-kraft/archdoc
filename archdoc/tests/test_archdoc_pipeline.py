from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from archdoc.catalog.id_resolver import resolve_catalog_id_collisions
from archdoc.linker.endpoint_service_linker import link_endpoints_to_services
from archdoc.mapper.action_mapper import map_actions
from archdoc.mapper.endpoint_mapper import map_endpoints
from archdoc.mapper.operation_link_mapper import map_operation_links
from archdoc.mapper.service_mapper import map_services
from archdoc.scanner.python_scanner import scan_project
from archdoc.validator.catalog_validator import validate_catalog

from conftest import make_config, write_file


def _run_pipeline(project_root: Path):
    config = make_config(project_root)
    facts = scan_project(config)
    services = map_services(facts, config)
    endpoints = map_endpoints(facts, config)
    services, endpoints = resolve_catalog_id_collisions(services, endpoints)
    links = link_endpoints_to_services(facts=facts, endpoints=endpoints, services=services)
    actions = map_actions(facts=facts, config=config, services=services, endpoints=endpoints)
    operation_links = map_operation_links(facts=facts, config=config, services=services)
    report = validate_catalog(facts=facts, services=services, endpoints=endpoints, links=links)
    return facts, services, endpoints, links, actions, operation_links, report


class ArchdocPipelineTests(TestCase):
    def test_pipeline_maps_fastapi_endpoint_service_link_and_database_action(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/users/user_service.py",
                """
                from sqlalchemy import select

                class User: ...

                class UserService:
                    def __init__(self, db):
                        self.db = db

                    async def reset_password(self, user_id: int):
                        result = await self.db.execute(select(User).where(User.id == user_id))
                        self.db.commit()
                        return result
                """,
            )
            write_file(
                project_root,
                "app/routers/users.py",
                """
                from fastapi import APIRouter, Depends
                from services.users.user_service import UserService

                router = APIRouter(prefix="/users")

                def get_user_service(): ...

                @router.post("/{user_id}/reset-password", response_model=dict)
                async def reset_password(user_id: int, service: UserService = Depends(get_user_service)):
                    return await service.reset_password(user_id)
                """,
            )
            write_file(
                project_root,
                "app/routers/main.py",
                """
                from fastapi import APIRouter
                from routers import users

                api = APIRouter()

                def mount():
                    api.include_router(users.router, prefix="/api")
                """,
            )

            _facts, services, endpoints, links, actions, operation_links, report = _run_pipeline(project_root)

            self.assertEqual([service.id for service in services], ["users.user"])
            self.assertEqual(endpoints[0].full_path, "/api/users/{user_id}/reset-password")
            self.assertEqual(len(links), 1)
            self.assertEqual(links[0].operation_id, "users.user.operation.reset_password")

            db_actions = [action for action in actions if action.kind == "database_action"]
            transactions = [action for action in actions if action.kind == "database_transaction"]
            self.assertTrue(any(action.call_name == "self.db.execute" for action in db_actions))
            self.assertTrue(any(action.call_name == "self.db.commit" for action in transactions))
            self.assertEqual(operation_links, [])
            self.assertEqual(report.summary.errors, 0)
            self.assertEqual(report.summary.linked_endpoints, 1)

    def test_endpoint_full_path_uses_app_routers_include_prefix(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/bootstrap/routes.py",
                """
                from typing import Any
                from app.routers import financial

                def register_runtime_api_routes(target: Any) -> None:
                    target.include_router(financial.router, prefix="/financial", tags=["Financial"])
                """,
            )
            write_file(
                project_root,
                "app/routers/financial.py",
                """
                from fastapi import APIRouter

                router = APIRouter()

                @router.get("/session-payment-requests")
                async def list_session_payment_requests():
                    return []
                """,
            )

            _facts, _services, endpoints, _links, _actions, _operation_links, _report = _run_pipeline(project_root)

            self.assertEqual(len(endpoints), 1)
            self.assertEqual(endpoints[0].path, "/session-payment-requests")
            self.assertEqual(endpoints[0].include_prefix, "/financial")
            self.assertEqual(endpoints[0].full_path, "/financial/session-payment-requests")

    def test_endpoint_linking_ignores_service_calls_inside_local_helper_definitions(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/users/user_service.py",
                """
                class UserService:
                    def reset_password(self, user_id: int):
                        return user_id
                """,
            )
            write_file(
                project_root,
                "app/routers/users.py",
                """
                from fastapi import APIRouter
                from services.users.user_service import UserService

                router = APIRouter()

                @router.post("/users/{user_id}/reset-password")
                def reset_password(user_id: int):
                    def unused_helper():
                        service = UserService()
                        return service.reset_password(user_id)

                    return {"status": "queued"}
                """,
            )

            _facts, _services, endpoints, links, _actions, _operation_links, report = _run_pipeline(project_root)

            self.assertEqual(len(endpoints), 1)
            self.assertEqual(links, [])
            self.assertEqual(report.summary.unlinked_endpoints, 1)
            self.assertIn(report.issues[0].code, {"endpoint_static_or_trivial", "endpoint_without_service_link", "endpoint_passthrough"})


    def test_service_db_origin_can_be_inherited_from_base_class(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/auth/credential_service.py",
                """
                from typing import Any
                from sqlalchemy import select

                class IAMUser: ...
                class IAMUserToken: ...

                class DbResourceMixin:
                    def __init__(self, db):
                        self.db = db

                class CredentialService(DbResourceMixin):
                    async def complete_credential_token(self, token: str, password: str) -> dict[str, Any]:
                        result = await self.db.execute(
                            select(IAMUserToken, IAMUser).where(IAMUserToken.token_hash == token)
                        )
                        return {"result": result, "password": password}
                """,
            )

            _facts, _services, _endpoints, _links, _actions, _operation_links, report = _run_pipeline(project_root)

            issue_codes = {issue.code for issue in report.issues}
            self.assertNotIn("service_db_session_not_initialized", issue_codes)
            self.assertNotIn("service_db_session_origin_unknown", issue_codes)

    def test_service_db_origin_can_be_forwarded_to_super_init(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/auth/credential_service.py",
                """
                from sqlalchemy.ext.asyncio import AsyncSession

                class CredentialService:
                    def __init__(self, db: AsyncSession):
                        super().__init__(db)

                    async def complete_credential_token(self, token: str):
                        return await self.db.execute(token)
                """,
            )

            _facts, _services, _endpoints, _links, _actions, _operation_links, report = _run_pipeline(project_root)

            issue_codes = {issue.code for issue in report.issues}
            self.assertNotIn("service_db_session_not_initialized", issue_codes)
            self.assertNotIn("service_db_session_origin_unknown", issue_codes)

    def test_service_db_origin_unknown_is_reported_with_precise_warning(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/auth/credential_service.py",
                """
                class CredentialService:
                    async def complete_credential_token(self, token: str):
                        return await self.db.execute(token)
                """,
            )

            _facts, _services, _endpoints, _links, _actions, _operation_links, report = _run_pipeline(project_root)

            issues = [issue for issue in report.issues if issue.code == "service_db_session_origin_unknown"]
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].details["db_attribute"], "self.db")
            self.assertEqual(issues[0].details["db_calls"], ["self.db.execute"])
    def test_inherited_service_operations_are_linked_to_declaring_service_operations(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/finance/budget.py",
                """
                class BudgetService:
                    async def create_budget(self, org_id: str, budget_data):
                        self.db.add(budget_data)
                        await self.db.flush()
                        await self.db.refresh(budget_data)
                        return budget_data
                """,
            )
            write_file(
                project_root,
                "app/services/finance/core.py",
                """
                from services.finance.budget import BudgetService

                class PaymentsService:
                    pass

                class FinancialService(PaymentsService, BudgetService):
                    def __init__(self, db):
                        self.db = db
                """,
            )
            write_file(
                project_root,
                "app/routers/financial.py",
                """
                from fastapi import APIRouter, Depends
                from services.finance.core import FinancialService

                router = APIRouter(prefix="/finance")

                def get_financial_service(): ...

                @router.post("/budgets")
                async def create_budget(service: FinancialService = Depends(get_financial_service)):
                    return await service.create_budget("org-1", {})
                """,
            )

            _facts, _services, _endpoints, links, _actions, operation_links, report = _run_pipeline(project_root)

            self.assertEqual(len(links), 1)
            self.assertEqual(links[0].operation_id, "finance.financial.operation.create_budget")

            inherited_links = [link for link in operation_links if link.link_type == "inherited_operation"]
            self.assertEqual(len(inherited_links), 1)
            self.assertEqual(inherited_links[0].source.operation_id, "finance.financial.operation.create_budget")
            self.assertEqual(inherited_links[0].target.operation_id, "finance.budget.operation.create_budget")

            unreferenced_ids = {
                issue.item_id
                for issue in report.issues
                if issue.code == "operation_without_endpoint_link"
            }
            self.assertNotIn("finance.budget.operation.create_budget", unreferenced_ids)
            self.assertEqual(report.summary.unreferenced_operations, 0)
    def test_direct_service_operation_without_db_origin_still_warns(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/finance/budget.py",
                """
                class BudgetService:
                    async def create_budget(self, org_id: str, budget_data):
                        await self.db.refresh(budget_data)
                        return budget_data
                """,
            )
            write_file(
                project_root,
                "app/routers/budgets.py",
                """
                from fastapi import APIRouter
                from services.finance.budget import BudgetService

                router = APIRouter(prefix="/budgets")

                @router.post("")
                async def create_budget():
                    service = BudgetService()
                    return await service.create_budget("org-1", {})
                """,
            )

            _facts, _services, _endpoints, links, _actions, _operation_links, report = _run_pipeline(project_root)

            self.assertEqual(len(links), 1)
            self.assertEqual(links[0].operation_id, "finance.budget.operation.create_budget")
            warnings = [issue for issue in report.issues if issue.code == "service_db_session_origin_unknown"]
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0].item_id, "finance.budget.operation.create_budget")
    def test_duplicate_service_ids_are_resolved_to_unique_catalog_ids(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            write_file(
                project_root,
                "app/services/calendar/core.py",
                """
                class CalendarService:
                    def detect_conflicts(self):
                        return []
                """,
            )
            write_file(
                project_root,
                "app/services/calendar/service.py",
                """
                class CalendarService:
                    def detect_conflicts(self):
                        return []
                """,
            )

            config = make_config(project_root)
            facts = scan_project(config)
            services = map_services(facts, config)
            services, endpoints = resolve_catalog_id_collisions(services, [])
            report = validate_catalog(facts=facts, services=services, endpoints=endpoints, links=[])

            service_ids = [service.id for service in services]
            operation_ids = [operation.id for service in services for operation in service.operations]

            self.assertEqual(len(service_ids), len(set(service_ids)))
            self.assertEqual(len(operation_ids), len(set(operation_ids)))
            self.assertTrue(all(service_id.startswith("calendar.calendar--") for service_id in service_ids))
            self.assertEqual(report.summary.errors, 0)
            self.assertTrue(any(issue.code == "resolved_service_logical_id_collision" for issue in report.issues))
