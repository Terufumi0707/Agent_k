from fastapi import FastAPI

from app.models import OrderInfo

app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def build_order_info() -> OrderInfo:
    return OrderInfo(
        main_a_number="A-12345",
        backup_a_number="A-67890",
        main_work_types=["メイン回線_開通"],
        main_work_date=["2026-02-01"],
        backup_work_types=["バックアップ回線_撤去"],
        backup_work_date=["2026-02-05"],
    )


@app.get("/orders/by-a-number/{a_number}", response_model=OrderInfo)
def get_order_by_a_number(a_number: str) -> OrderInfo:
    return build_order_info()


@app.get("/orders/by-entry-id/{entry_id}", response_model=OrderInfo)
def get_order_by_entry_id(entry_id: str) -> OrderInfo:
    return build_order_info()
