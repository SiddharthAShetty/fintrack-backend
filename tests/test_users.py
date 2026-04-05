"""
Tests for user management endpoints (admin only).
"""
import pytest


class TestUserManagement:

    def test_admin_can_list_users(self, client, auth_header_admin, viewer_user, analyst_user):
        resp = client.get("/users", headers=auth_header_admin)
        assert resp.status_code == 200
        # admin + viewer + analyst = 3
        assert len(resp.json()) == 3

    def test_viewer_cannot_list_users(self, client, auth_header_viewer):
        resp = client.get("/users", headers=auth_header_viewer)
        assert resp.status_code == 403

    def test_analyst_cannot_list_users(self, client, auth_header_analyst):
        resp = client.get("/users", headers=auth_header_analyst)
        assert resp.status_code == 403

    def test_admin_can_get_user_by_id(self, client, auth_header_admin, viewer_user):
        resp = client.get(f"/users/{viewer_user.id}", headers=auth_header_admin)
        assert resp.status_code == 200
        assert resp.json()["username"] == "viewer"

    def test_get_nonexistent_user_returns_404(self, client, auth_header_admin):
        resp = client.get("/users/99999", headers=auth_header_admin)
        assert resp.status_code == 404

    def test_admin_can_update_user_role(self, client, auth_header_admin, viewer_user):
        resp = client.patch(
            f"/users/{viewer_user.id}",
            json={"role": "analyst"},
            headers=auth_header_admin,
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "analyst"

    def test_admin_can_deactivate_user(self, client, auth_header_admin, viewer_user):
        resp = client.patch(
            f"/users/{viewer_user.id}",
            json={"is_active": False},
            headers=auth_header_admin,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_admin_cannot_delete_self(self, client, auth_header_admin, admin_user):
        resp = client.delete(f"/users/{admin_user.id}", headers=auth_header_admin)
        assert resp.status_code == 400
        assert "cannot delete your own" in resp.json()["detail"]

    def test_admin_can_delete_other_user(self, client, auth_header_admin, viewer_user):
        resp = client.delete(f"/users/{viewer_user.id}", headers=auth_header_admin)
        assert resp.status_code == 204
        # Confirm gone
        resp2 = client.get(f"/users/{viewer_user.id}", headers=auth_header_admin)
        assert resp2.status_code == 404

    def test_unauthenticated_cannot_manage_users(self, client, viewer_user):
        resp = client.get("/users", headers={})
        assert resp.status_code == 401
