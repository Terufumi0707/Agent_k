from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.work_parser import parse_work_request


def test_parse_work_request_with_aliases_and_month_day():
    parsed = parse_work_request(
        "2月5日に現調と宅内やりたい",
        today=date(2025, 1, 10),
        use_llm=False,
    )
    assert parsed["operation"] == "change"
    assert parsed["date"] == "2025-02-05"
    assert parsed["date_inferred"] is True
    work_types = {item["name"] for item in parsed["work_types"]}
    assert {"現地調査", "宅内工事"}.issubset(work_types)


def test_parse_work_request_with_removal_ambiguity():
    parsed = parse_work_request("撤去を5日に変更", today=date(2025, 1, 10), use_llm=False)
    assert parsed["operation"] == "change"
    assert parsed["date"] == "2025-02-05"
    assert parsed["date_inferred"] is True
    work_types = {item["name"] for item in parsed["work_types"]}
    assert {"端末撤去", "コム撤去", "地域撤去", "ケーブル撤去", "PD撤去"}.issubset(work_types)
    assert "撤去" in parsed["notes"]


def test_parse_work_request_with_explicit_date():
    parsed = parse_work_request(
        "2026年2月5日に切り替え",
        today=date(2025, 1, 10),
        use_llm=False,
    )
    assert parsed["operation"] == "change"
    assert parsed["date"] == "2026-02-05"
    assert parsed["date_inferred"] is False
    work_types = {item["name"] for item in parsed["work_types"]}
    assert "切替工事" in work_types


def test_parse_work_endpoint():
    client = TestClient(app)
    response = client.post("/work/parse", json={"message": "2月5日に現調"})
    data = response.json()
    assert response.status_code == 200
    assert data["operation"] == "change"
    assert "現地調査" in {item["name"] for item in data["work_types"]}
