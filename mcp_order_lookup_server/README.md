# Order Lookup MCP Server

`api` サービスの以下2つのオーダー照会APIを利用するための MCP サーバーです。

- `GET /v1/orders/by-n-number/{n_number}`
- `GET /v1/orders/{web_entry_id}`

## 提供ツール

- `get_order_by_n_number(n_number: str)`
- `get_order_by_web_entry_id(web_entry_id: str)`

どちらも以下形式で返します。

```json
{
  "ok": true,
  "status_code": 200,
  "payload": { "...": "APIレスポンス" }
}
```

エラー時は `ok=false` かつ `payload.error` を返します。

## セットアップ

```bash
cd mcp_order_lookup_server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動

```bash
ORDER_LOOKUP_API_BASE_URL=http://localhost:8001 \
ORDER_LOOKUP_API_TIMEOUT_SECONDS=5 \
MCP_TRANSPORT=streamable-http \
MCP_HOST=0.0.0.0 \
MCP_PORT=9000 \
python server.py
```

## 環境変数

- `ORDER_LOOKUP_API_BASE_URL` (default: `http://localhost:8001`)
- `ORDER_LOOKUP_API_TIMEOUT_SECONDS` (default: `5`)


## Docker

```bash
docker build -t order-lookup-mcp ./mcp_order_lookup_server
docker run --rm -p 9000:9000 \
  -e ORDER_LOOKUP_API_BASE_URL=http://host.docker.internal:8001 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=9000 \
  order-lookup-mcp
```
