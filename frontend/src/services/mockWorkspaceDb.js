import { DEFAULT_GREETING_MESSAGE } from "../constants/chat";

const artificialLatency = 120;

let sequence = 3;

function createTranscriptEntry(role, content, offsetMs = 0) {
  return {
    role,
    content,
    timestamp: new Date(Date.now() - offsetMs).toISOString()
  };
}

let workspaceTable = [
  {
    id: "ws-001",
    title: "A社提案準備",
    summary: "提案シナリオの素案をエージェントに依頼。資料構成のチェックを進行中。",
    status: "running",
    lastUpdatedAt: new Date().toISOString(),
    transcript: [
      createTranscriptEntry("assistant", DEFAULT_GREETING_MESSAGE, 1000 * 60 * 5),
      createTranscriptEntry(
        "user",
        "A社向けの提案資料で、想定課題の整理を手伝ってください。",
        1000 * 60 * 4
      ),
      createTranscriptEntry(
        "assistant",
        "承知しました。提案資料の想定課題としては、現状分析、導入メリット、運用体制が焦点となりそうです。",
        1000 * 60 * 3
      )
    ]
  },
  {
    id: "ws-002",
    title: "A社アポイント準備",
    summary: "議事録のたたき台作成を依頼済み。担当者へ共有し完了扱い。",
    status: "completed",
    lastUpdatedAt: new Date(Date.now() - 3600 * 1000).toISOString(),
    transcript: [
      createTranscriptEntry("assistant", DEFAULT_GREETING_MESSAGE, 3600 * 1000 + 1000 * 60 * 5),
      createTranscriptEntry(
        "user",
        "アポイント後の議事録素案をまとめて。ポイントは簡潔さです。",
        3600 * 1000 + 1000 * 60 * 4
      ),
      createTranscriptEntry(
        "assistant",
        "以下の構成で議事録素案をまとめました。1) 概要 2) 決定事項 3) アクションアイテム。",
        3600 * 1000 + 1000 * 60 * 3
      ),
      createTranscriptEntry(
        "user",
        "ありがとう。担当者に共有したので完了としておいてください。",
        3600 * 1000 + 1000 * 60 * 2
      ),
      createTranscriptEntry(
        "assistant",
        "共有完了しました。必要であれば追って修正案もご用意できます。",
        3600 * 1000 + 1000 * 60
      )
    ]
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
        lastUpdatedAt: new Date().toISOString(),
        transcript: [createTranscriptEntry("assistant", DEFAULT_GREETING_MESSAGE)]
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
