const artificialLatency = 120;

let sequence = 3;

let workspaceTable = [
  {
    id: "ws-001",
    title: "A社提案準備",
    summary: "提案シナリオの素案をエージェントに依頼。資料構成のチェックを進行中。",
    status: "running",
    lastUpdatedAt: new Date().toISOString()
  },
  {
    id: "ws-002",
    title: "A社アポイント準備",
    summary: "議事録のたたき台作成を依頼済み。担当者へ共有し完了扱い。",
    status: "completed",
    lastUpdatedAt: new Date(Date.now() - 3600 * 1000).toISOString()
  }
];

function deepClone(record) {
  return JSON.parse(JSON.stringify(record));
}

export async function fetchWorkspaces() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(workspaceTable.map((item) => deepClone(item)));
    }, artificialLatency);
  });
}

export async function createWorkspaceRecord({ title }) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newRecord = {
        id: `ws-${String(sequence).padStart(3, "0")}`,
        title,
        summary: "",
        status: "running",
        lastUpdatedAt: new Date().toISOString()
      };
      sequence += 1;
      workspaceTable = [...workspaceTable, newRecord];
      resolve(deepClone(newRecord));
    }, artificialLatency);
  });
}

export async function updateWorkspaceRecord(id, patch) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = workspaceTable.findIndex((item) => item.id === id);
      if (index === -1) {
        reject(new Error("workspace not found"));
        return;
      }

      const updated = {
        ...workspaceTable[index],
        ...patch,
        lastUpdatedAt: patch.lastUpdatedAt ?? new Date().toISOString()
      };
      workspaceTable = [
        ...workspaceTable.slice(0, index),
        updated,
        ...workspaceTable.slice(index + 1)
      ];

      resolve(deepClone(updated));
    }, artificialLatency);
  });
}

export async function deleteWorkspaceRecord(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const index = workspaceTable.findIndex((item) => item.id === id);
      if (index === -1) {
        reject(new Error("workspace not found"));
        return;
      }

      workspaceTable = [
        ...workspaceTable.slice(0, index),
        ...workspaceTable.slice(index + 1)
      ];

      resolve();
    }, artificialLatency);
  });
}
