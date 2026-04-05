"""
Tests for transaction CRUD, filtering, pagination, analytics, and export.
"""
import pytest
from datetime import date


# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_EXPENSE = {
    "amount": 1500.00,
    "type": "expense",
    "category": "food",
    "date": "2025-03-15",
    "notes": "Groceries",
}

VALID_INCOME = {
    "amount": 50000.00,
    "type": "income",
    "category": "salary",
    "date": "2025-03-01",
    "notes": "March salary",
}


def create_tx(client, headers, payload=None):
    return client.post("/transactions", json=payload or VALID_EXPENSE, headers=headers)


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateTransaction:

    def test_admin_can_create(self, client, auth_header_admin):
        resp = create_tx(client, auth_header_admin)
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "food"
        assert data["type"] == "expense"
        assert float(data["amount"]) == 1500.00

    def test_analyst_can_create(self, client, auth_header_analyst):
        resp = create_tx(client, auth_header_analyst)
        assert resp.status_code == 201

    def test_viewer_cannot_create(self, client, auth_header_viewer):
        resp = create_tx(client, auth_header_viewer)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create(self, client):
        resp = create_tx(client, {})
        assert resp.status_code == 401

    def test_negative_amount_rejected(self, client, auth_header_admin):
        resp = create_tx(client, auth_header_admin, {**VALID_EXPENSE, "amount": -100})
        assert resp.status_code == 422

    def test_zero_amount_rejected(self, client, auth_header_admin):
        resp = create_tx(client, auth_header_admin, {**VALID_EXPENSE, "amount": 0})
        assert resp.status_code == 422

    def test_invalid_category_rejected(self, client, auth_header_admin):
        resp = create_tx(client, auth_header_admin, {**VALID_EXPENSE, "category": "luxury_yacht"})
        assert resp.status_code == 422

    def test_mismatched_category_type_rejected(self, client, auth_header_admin):
        # income transaction with an expense category
        resp = create_tx(client, auth_header_admin, {
            "amount": 1000,
            "type": "income",
            "category": "food",   # expense category
            "date": "2025-03-01",
        })
        assert resp.status_code == 422

    def test_missing_required_fields(self, client, auth_header_admin):
        resp = client.post("/transactions", json={"amount": 100}, headers=auth_header_admin)
        assert resp.status_code == 422


# ── Read ──────────────────────────────────────────────────────────────────────

class TestListAndGetTransaction:

    def test_list_returns_paginated(self, client, auth_header_admin):
        for _ in range(3):
            create_tx(client, auth_header_admin)
        resp = client.get("/transactions", headers=auth_header_admin)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3
        assert data["page"] == 1

    def test_pagination_works(self, client, auth_header_admin):
        for _ in range(5):
            create_tx(client, auth_header_admin)
        resp = client.get("/transactions?page=1&page_size=2", headers=auth_header_admin)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["results"]) == 2

    def test_viewer_sees_only_own(self, client, auth_header_admin, auth_header_viewer):
        # Admin creates 2 transactions (owned by admin)
        create_tx(client, auth_header_admin)
        create_tx(client, auth_header_admin)
        # Viewer created 0 → should see 0
        resp = client.get("/transactions", headers=auth_header_viewer)
        assert resp.json()["total"] == 0

    def test_admin_sees_all(self, client, auth_header_admin, auth_header_analyst):
        create_tx(client, auth_header_admin)
        create_tx(client, auth_header_analyst)
        resp = client.get("/transactions", headers=auth_header_admin)
        assert resp.json()["total"] == 2

    def test_get_single_success(self, client, auth_header_admin):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.get(f"/transactions/{tx_id}", headers=auth_header_admin)
        assert resp.status_code == 200
        assert resp.json()["id"] == tx_id

    def test_get_nonexistent_returns_404(self, client, auth_header_admin):
        resp = client.get("/transactions/99999", headers=auth_header_admin)
        assert resp.status_code == 404

    def test_viewer_cannot_access_others_transaction(
        self, client, auth_header_admin, auth_header_viewer
    ):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.get(f"/transactions/{tx_id}", headers=auth_header_viewer)
        assert resp.status_code == 404


# ── Filtering ─────────────────────────────────────────────────────────────────

class TestFiltering:

    def test_filter_by_type(self, client, auth_header_admin):
        create_tx(client, auth_header_admin, VALID_EXPENSE)
        create_tx(client, auth_header_admin, VALID_INCOME)
        resp = client.get("/transactions?type=income", headers=auth_header_admin)
        assert resp.json()["total"] == 1
        assert resp.json()["results"][0]["type"] == "income"

    def test_filter_by_category(self, client, auth_header_admin):
        create_tx(client, auth_header_admin, VALID_EXPENSE)  # food
        create_tx(client, auth_header_admin, {**VALID_EXPENSE, "category": "transport"})
        resp = client.get("/transactions?category=food", headers=auth_header_admin)
        assert resp.json()["total"] == 1

    def test_filter_by_date_range(self, client, auth_header_admin):
        create_tx(client, auth_header_admin, {**VALID_EXPENSE, "date": "2025-01-10"})
        create_tx(client, auth_header_admin, {**VALID_EXPENSE, "date": "2025-06-10"})
        resp = client.get(
            "/transactions?date_from=2025-01-01&date_to=2025-03-31",
            headers=auth_header_admin,
        )
        assert resp.json()["total"] == 1

    def test_filter_by_amount_range(self, client, auth_header_admin):
        create_tx(client, auth_header_admin, {**VALID_EXPENSE, "amount": 500})
        create_tx(client, auth_header_admin, {**VALID_EXPENSE, "amount": 5000})
        resp = client.get("/transactions?max_amount=1000", headers=auth_header_admin)
        assert resp.json()["total"] == 1


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdateTransaction:

    def test_admin_can_update(self, client, auth_header_admin):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.patch(
            f"/transactions/{tx_id}",
            json={"amount": 999.99, "notes": "Updated note"},
            headers=auth_header_admin,
        )
        assert resp.status_code == 200
        assert float(resp.json()["amount"]) == 999.99
        assert resp.json()["notes"] == "Updated note"

    def test_viewer_cannot_update(self, client, auth_header_admin, auth_header_viewer):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.patch(
            f"/transactions/{tx_id}", json={"amount": 1}, headers=auth_header_viewer
        )
        assert resp.status_code == 403

    def test_empty_update_rejected(self, client, auth_header_admin):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.patch(f"/transactions/{tx_id}", json={}, headers=auth_header_admin)
        assert resp.status_code == 422

    def test_update_nonexistent_returns_404(self, client, auth_header_admin):
        resp = client.patch(
            "/transactions/99999", json={"amount": 100}, headers=auth_header_admin
        )
        assert resp.status_code == 404


# ── Delete ────────────────────────────────────────────────────────────────────

class TestDeleteTransaction:

    def test_admin_can_delete(self, client, auth_header_admin):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.delete(f"/transactions/{tx_id}", headers=auth_header_admin)
        assert resp.status_code == 204
        # Confirm gone
        resp2 = client.get(f"/transactions/{tx_id}", headers=auth_header_admin)
        assert resp2.status_code == 404

    def test_analyst_cannot_delete(self, client, auth_header_admin, auth_header_analyst):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.delete(f"/transactions/{tx_id}", headers=auth_header_analyst)
        assert resp.status_code == 403

    def test_viewer_cannot_delete(self, client, auth_header_admin, auth_header_viewer):
        tx_id = create_tx(client, auth_header_admin).json()["id"]
        resp = client.delete(f"/transactions/{tx_id}", headers=auth_header_viewer)
        assert resp.status_code == 403


# ── Analytics ─────────────────────────────────────────────────────────────────

class TestAnalytics:

    def test_summary_structure(self, client, auth_header_admin):
        create_tx(client, auth_header_admin, VALID_INCOME)
        create_tx(client, auth_header_admin, VALID_EXPENSE)
        resp = client.get("/analytics/summary", headers=auth_header_admin)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "total_expense" in data
        assert "balance" in data
        assert "category_breakdown" in data
        assert "monthly_totals" in data
        assert "recent_transactions" in data

    def test_summary_balance_calculation(self, client, auth_header_admin):
        create_tx(client, auth_header_admin, VALID_INCOME)   # +50000
        create_tx(client, auth_header_admin, VALID_EXPENSE)  # -1500
        resp = client.get("/analytics/summary", headers=auth_header_admin)
        data = resp.json()
        assert data["total_income"] == 50000.0
        assert data["total_expense"] == 1500.0
        assert data["balance"] == 48500.0

    def test_summary_empty(self, client, auth_header_admin):
        resp = client.get("/analytics/summary", headers=auth_header_admin)
        assert resp.status_code == 200
        data = resp.json()
        assert data["balance"] == 0.0
        assert data["transaction_count"] == 0


# ── Export ────────────────────────────────────────────────────────────────────

class TestExport:

    def test_csv_export(self, client, auth_header_analyst):
        create_tx(client, auth_header_analyst, VALID_EXPENSE)
        resp = client.get("/analytics/export/csv", headers=auth_header_analyst)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        content = resp.text
        assert "id,date,type,category,amount" in content
        assert "food" in content

    def test_json_export(self, client, auth_header_analyst):
        create_tx(client, auth_header_analyst, VALID_EXPENSE)
        resp = client.get("/analytics/export/json", headers=auth_header_analyst)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["category"] == "food"

    def test_viewer_cannot_export(self, client, auth_header_viewer):
        resp = client.get("/analytics/export/csv", headers=auth_header_viewer)
        assert resp.status_code == 403
