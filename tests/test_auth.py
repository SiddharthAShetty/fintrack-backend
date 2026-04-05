"""
Tests for authentication endpoints: register, login, /me.
"""
import pytest


class TestRegister:

    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "SecureP@ss1",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "viewer"
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client, viewer_user):
        resp = client.post("/auth/register", json={
            "username": "viewer",
            "email": "other@test.com",
            "password": "SecureP@ss1",
        })
        assert resp.status_code == 409
        assert "already taken" in resp.json()["detail"]

    def test_register_duplicate_email(self, client, viewer_user):
        resp = client.post("/auth/register", json={
            "username": "anotheruser",
            "email": "viewer@test.com",
            "password": "SecureP@ss1",
        })
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    def test_register_weak_password(self, client):
        resp = client.post("/auth/register", json={
            "username": "weakpass",
            "email": "weak@test.com",
            "password": "123",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "username": "bademail",
            "email": "not-an-email",
            "password": "ValidP@ss1",
        })
        assert resp.status_code == 422


class TestLogin:

    def test_login_success(self, client, viewer_user):
        resp = client.post("/auth/login", data={
            "username": "viewer",
            "password": "Viewer@1234",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in_minutes"] > 0

    def test_login_wrong_password(self, client, viewer_user):
        resp = client.post("/auth/login", data={
            "username": "viewer",
            "password": "WrongPassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/login", data={
            "username": "ghost",
            "password": "anypassword",
        })
        assert resp.status_code == 401

    def test_login_inactive_user(self, client, db, viewer_user):
        viewer_user.is_active = False
        db.commit()
        resp = client.post("/auth/login", data={
            "username": "viewer",
            "password": "Viewer@1234",
        })
        assert resp.status_code == 403


class TestMe:

    def test_me_authenticated(self, client, auth_header_viewer):
        resp = client.get("/auth/me", headers=auth_header_viewer)
        assert resp.status_code == 200
        assert resp.json()["username"] == "viewer"

    def test_me_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer fake.token.here"})
        assert resp.status_code == 401
