"""Integration tests for all REST API endpoints and trading workflow."""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_get_account_summary(client):
    response = await client.get("/account")
    assert response.status_code == 200
    data = response.json()
    assert "cash_balance" in data
    assert "portfolio_value" in data
    assert data["cash_balance"] > 0


@pytest.mark.asyncio
async def test_get_positions(client):
    response = await client.get("/account/positions")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert len(data["positions"]) >= 4  # Seeded with TCS, INFY, RELIANCE, HDFCBANK


@pytest.mark.asyncio
async def test_market_instruments_and_price(client):
    # Instruments
    resp_inst = await client.get("/market/instruments")
    assert resp_inst.status_code == 200
    instruments = resp_inst.json()["instruments"]
    assert any(i["symbol"] == "TCS" for i in instruments)

    # Specific price
    resp_price = await client.get("/market/TCS/price")
    assert resp_price.status_code == 200
    price_data = resp_price.json()
    assert price_data["symbol"] == "TCS"
    assert price_data["price"] > 0
    assert "bid" in price_data and "ask" in price_data


@pytest.mark.asyncio
async def test_ai_chat_query(client):
    # Ask about cash
    resp = await client.post("/ai/chat", json={"message": "What is my available cash?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "available cash" in data["message"].lower() or "cash" in data["message"].lower()


@pytest.mark.asyncio
async def test_ai_chat_create_proposal_and_execute(client):
    # 1. Ask to buy 10 TCS
    resp_chat = await client.post(
        "/ai/chat", json={"message": "Buy 10 TCS at market price"}
    )
    assert resp_chat.status_code == 200
    chat_data = resp_chat.json()
    assert chat_data["order_proposal"] is not None
    proposal = chat_data["order_proposal"]
    assert proposal["symbol"] == "TCS"
    assert proposal["side"] == "BUY"
    assert proposal["quantity"] == 10
    assert proposal["status"] == "PENDING_APPROVAL"
    order_id = proposal["id"]

    # 2. Confirm/Execute the order proposal via API
    resp_exec = await client.post(f"/orders/{order_id}/execute")
    assert resp_exec.status_code == 200
    exec_data = resp_exec.json()
    assert exec_data["status"] == "FILLED"
    assert exec_data["execution_quantity"] == 10

    # 3. Check that the order is now FILLED
    resp_order = await client.get(f"/orders/{order_id}")
    assert resp_order.status_code == 200
    assert resp_order.json()["status"] == "FILLED"

    # 4. Check audit logs
    resp_audit = await client.get("/audit/logs")
    assert resp_audit.status_code == 200
    audit_data = resp_audit.json()
    assert len(audit_data["logs"]) > 0
