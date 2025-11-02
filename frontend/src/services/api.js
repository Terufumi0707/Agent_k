// 入力メッセージを元にワークフロー候補を取得
export async function suggestWorkflow(message) {
  const response = await fetch("/api/workflows/suggest", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message })
  });

  if (!response.ok) {
    throw new Error("Failed to fetch chat response");
  }

  return await response.json();
}

// ワークフロー候補の採否を送信して実行結果を取得
export async function submitWorkflowSelection(payload) {
  const response = await fetch("/api/workflows/select", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Failed to submit workflow selection");
  }

  return await response.json();
}
