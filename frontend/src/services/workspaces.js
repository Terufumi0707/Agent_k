// JSON形式でリクエストする際の共通ヘッダー
const JSON_HEADERS = {
  "Content-Type": "application/json"
};

// APIレスポンスを共通で処理し、エラー時は例外を投げる
async function handleResponse(response) {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Workspace API request failed");
  }
  return response.status === 204 ? null : response.json();
}

// ワークスペース一覧を取得
export async function fetchWorkspaces() {
  const response = await fetch("/api/workspaces");
  return handleResponse(response);
}

// 新規ワークスペースを作成
export async function createWorkspaceRecord({ title } = {}) {
  const response = await fetch("/api/workspaces", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ title })
  });
  return handleResponse(response);
}

// ワークスペース情報を部分更新
export async function updateWorkspaceRecord(id, patch) {
  const response = await fetch(`/api/workspaces/${id}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(patch)
  });
  return handleResponse(response);
}

// ワークスペースを削除
export async function deleteWorkspaceRecord(id) {
  const response = await fetch(`/api/workspaces/${id}`, {
    method: "DELETE"
  });
  return handleResponse(response);
}
