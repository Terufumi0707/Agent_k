const JSON_HEADERS = {
  "Content-Type": "application/json"
};

async function handleResponse(response) {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Workspace API request failed");
  }
  return response.status === 204 ? null : response.json();
}

export async function fetchWorkspaces() {
  const response = await fetch("/api/workspaces");
  return handleResponse(response);
}

export async function createWorkspaceRecord({ title } = {}) {
  const response = await fetch("/api/workspaces", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ title })
  });
  return handleResponse(response);
}

export async function updateWorkspaceRecord(id, patch) {
  const response = await fetch(`/api/workspaces/${id}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(patch)
  });
  return handleResponse(response);
}

export async function deleteWorkspaceRecord(id) {
  const response = await fetch(`/api/workspaces/${id}`, {
    method: "DELETE"
  });
  return handleResponse(response);
}
