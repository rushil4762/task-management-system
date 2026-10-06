import pytest
from httpx import AsyncClient

from app.models.task import TaskPriority, TaskStatus
from app.models.user import UserRole


@pytest.mark.asyncio
class TestAuthenticationRBAC:
    """Test RBAC in registration, login, and user profile."""

    async def test_register_creates_employee_by_default(self, client: AsyncClient):
        payload = {
            "name": "Jane Employee",
            "email": "jane@example.com",
            "password": "Password123!",
        }
        res = await client.post("/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "jane@example.com"
        assert data["role"] == "EMPLOYEE"

    async def test_registration_cannot_create_ceo_privilege_escalation(self, client: AsyncClient):
        # Even if attacker supplies role=CEO, server must force EMPLOYEE
        payload = {
            "name": "Attacker",
            "email": "attacker@example.com",
            "password": "Password123!",
            "role": "CEO",
        }
        res = await client.post("/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["role"] == "EMPLOYEE"
        assert data["role"] != "CEO"

    async def test_auth_me_returns_role_for_ceo_and_employee(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_auth_headers: dict[str, str]
    ):
        # CEO /auth/me
        ceo_res = await client.get("/auth/me", headers=auth_headers)
        assert ceo_res.status_code == 200
        assert ceo_res.json()["role"] == "CEO"

        # Employee /auth/me
        emp_res = await client.get("/auth/me", headers=employee_auth_headers)
        assert emp_res.status_code == 200
        assert emp_res.json()["role"] == "EMPLOYEE"

    async def test_login_works_for_both_ceo_and_employee(
        self, client: AsyncClient, test_user, employee_user
    ):
        # Login CEO
        res_ceo = await client.post(
            "/auth/login",
            json={"email": test_user.email, "password": "Password123!"},
        )
        assert res_ceo.status_code == 200
        assert "access_token" in res_ceo.json()

        # Login Employee
        res_emp = await client.post(
            "/auth/login",
            json={"email": employee_user.email, "password": "Employee123!"},
        )
        assert res_emp.status_code == 200
        assert "access_token" in res_emp.json()


@pytest.mark.asyncio
class TestCEOPermissions:
    """Test CEO exclusive permissions."""

    async def test_ceo_can_retrieve_active_employees(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_user, inactive_user
    ):
        res = await client.get("/users/employees", headers=auth_headers)
        assert res.status_code == 200
        employees = res.json()
        assert isinstance(employees, list)
        emails = [e["email"] for e in employees]
        assert employee_user.email in emails
        assert inactive_user.email not in emails  # inactive filtered out
        for emp in employees:
            assert "password_hash" not in emp
            assert emp["role"] == "EMPLOYEE"

    async def test_ceo_can_create_and_assign_task(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_user
    ):
        payload = {
            "title": "Task for Employee",
            "description": "Important project task",
            "priority": "high",
            "assigned_to_id": employee_user.id,
        }
        res = await client.post("/tasks", json=payload, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["assigned_to_id"] == employee_user.id

    async def test_ceo_can_assign_task_via_assign_endpoint(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_user
    ):
        # Create unassigned task
        res = await client.post("/tasks", json={"title": "Unassigned Task"}, headers=auth_headers)
        task_id = res.json()["id"]

        # Assign via dedicated endpoint
        assign_res = await client.patch(
            f"/tasks/{task_id}/assign",
            json={"assigned_to_id": employee_user.id},
            headers=auth_headers,
        )
        assert assign_res.status_code == 200
        assert assign_res.json()["assigned_to_id"] == employee_user.id

    async def test_ceo_can_manage_categories(self, client: AsyncClient, auth_headers: dict[str, str]):
        # Create category
        create_res = await client.post(
            "/categories", json={"name": "Engineering", "description": "Tech tasks"}, headers=auth_headers
        )
        assert create_res.status_code == 201
        cat_id = create_res.json()["id"]

        # Update category
        update_res = await client.put(
            f"/categories/{cat_id}",
            json={"name": "Engineering & Ops", "description": "Updated"},
            headers=auth_headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Engineering & Ops"

        # Delete category
        del_res = await client.delete(f"/categories/{cat_id}", headers=auth_headers)
        assert del_res.status_code == 204


@pytest.mark.asyncio
class TestEmployeePermissionsAndRestrictions:
    """Test Employee capabilities and security restrictions."""

    async def test_employee_cannot_retrieve_employee_list(
        self, client: AsyncClient, employee_auth_headers: dict[str, str]
    ):
        res = await client.get("/users/employees", headers=employee_auth_headers)
        assert res.status_code == 403
        assert "CEO" in res.json()["detail"]

    async def test_employee_cannot_assign_task_on_create(
        self, client: AsyncClient, employee_auth_headers: dict[str, str], employee_user
    ):
        payload = {
            "title": "Employee attempting to assign",
            "assigned_to_id": employee_user.id,
        }
        res = await client.post("/tasks", json=payload, headers=employee_auth_headers)
        assert res.status_code == 403
        assert "assign" in res.json()["detail"].lower()

    async def test_employee_cannot_assign_task_via_assign_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        employee_auth_headers: dict[str, str],
        employee_user,
        other_employee_user,
    ):
        # CEO creates task assigned to employee
        res = await client.post(
            "/tasks",
            json={"title": "Task", "assigned_to_id": employee_user.id},
            headers=auth_headers,
        )
        task_id = res.json()["id"]

        # Employee tries to reassign to other employee
        reassign_res = await client.patch(
            f"/tasks/{task_id}/assign",
            json={"assigned_to_id": other_employee_user.id},
            headers=employee_auth_headers,
        )
        assert reassign_res.status_code == 403

    async def test_employee_cannot_create_or_edit_or_delete_category(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_auth_headers: dict[str, str]
    ):
        # Create category attempt
        create_res = await client.post(
            "/categories", json={"name": "Hacked Category"}, headers=employee_auth_headers
        )
        assert create_res.status_code == 403

        # CEO creates a category
        ceo_cat = await client.post("/categories", json={"name": "Legit"}, headers=auth_headers)
        cat_id = ceo_cat.json()["id"]

        # Employee tries to edit category
        edit_res = await client.put(
            f"/categories/{cat_id}", json={"name": "Changed"}, headers=employee_auth_headers
        )
        assert edit_res.status_code == 403

        # Employee tries to delete category
        del_res = await client.delete(f"/categories/{cat_id}", headers=employee_auth_headers)
        assert del_res.status_code == 403

    async def test_employee_can_view_existing_categories(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_auth_headers: dict[str, str]
    ):
        # CEO creates a category
        await client.post("/categories", json={"name": "Visible Category"}, headers=auth_headers)

        # Employee retrieves categories
        list_res = await client.get("/categories", headers=employee_auth_headers)
        assert list_res.status_code == 200
        cats = list_res.json()
        assert any(c["name"] == "Visible Category" for c in cats)

    async def test_employee_can_update_status_of_assigned_task(
        self, client: AsyncClient, auth_headers: dict[str, str], employee_auth_headers: dict[str, str], employee_user
    ):
        # CEO creates task assigned to employee
        create_res = await client.post(
            "/tasks",
            json={"title": "Actionable Task", "assigned_to_id": employee_user.id},
            headers=auth_headers,
        )
        task_id = create_res.json()["id"]

        # Employee updates status to in_progress
        update_res = await client.patch(
            f"/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=employee_auth_headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "in_progress"

        # Employee marks task completed
        complete_res = await client.patch(
            f"/tasks/{task_id}/complete",
            headers=employee_auth_headers,
        )
        assert complete_res.status_code == 200
        assert complete_res.json()["status"] == "completed"
        assert complete_res.json()["completed_at"] is not None

    async def test_employee_cannot_update_unassigned_or_other_employee_task(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        employee_auth_headers: dict[str, str],
        other_employee_user,
    ):
        # CEO creates task assigned to other_employee_user
        create_res = await client.post(
            "/tasks",
            json={"title": "Private Task", "assigned_to_id": other_employee_user.id},
            headers=auth_headers,
        )
        task_id = create_res.json()["id"]

        # First employee tries to update status
        res = await client.patch(
            f"/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=employee_auth_headers,
        )
        assert res.status_code in (403, 404)

        # First employee tries to mark complete
        complete_res = await client.patch(
            f"/tasks/{task_id}/complete",
            headers=employee_auth_headers,
        )
        assert complete_res.status_code in (403, 404)

    async def test_employee_cannot_delete_task(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        employee_auth_headers: dict[str, str],
        employee_user,
    ):
        # CEO creates task assigned to employee
        create_res = await client.post(
            "/tasks",
            json={"title": "Delete Target", "assigned_to_id": employee_user.id},
            headers=auth_headers,
        )
        task_id = create_res.json()["id"]

        # Employee tries to delete
        del_res = await client.delete(f"/tasks/{task_id}", headers=employee_auth_headers)
        assert del_res.status_code == 403

    async def test_employee_cannot_modify_task_fields_other_than_status(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        employee_auth_headers: dict[str, str],
        employee_user,
    ):
        create_res = await client.post(
            "/tasks",
            json={"title": "Original Title", "priority": "low", "assigned_to_id": employee_user.id},
            headers=auth_headers,
        )
        task_id = create_res.json()["id"]

        # Employee attempts to edit title or priority
        res = await client.patch(
            f"/tasks/{task_id}",
            json={"title": "Tampered Title", "priority": "urgent"},
            headers=employee_auth_headers,
        )
        assert res.status_code == 403
        assert "status" in res.json()["detail"].lower()

