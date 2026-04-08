const backendBaseUrl = (import.meta.env.VITE_BACKEND_BASE_URL ?? "").replace(/\/$/, "");
const apiBasePath = (import.meta.env.VITE_API_BASE_PATH ?? "").replace(/\/$/, "");

export const JOB_STATUS = {
  CREATED: "CREATED",
  DRAFTING: "DRAFTING",
  WAITING_FOR_REVIEW: "WAITING_FOR_REVIEW",
  COMPLETED: "COMPLETED"
};

export const REVIEW_ACTION = {
  APPROVE: "approve",
  REVISE: "revise"
};

const normalizePath = (path) => (path.startsWith("/") ? path : `/${path}`);

const buildUrl = (path) => {
  const normalizedPath = normalizePath(path);
  const basePath = apiBasePath ? normalizePath(apiBasePath) : "";
  return backendBaseUrl
    ? `${backendBaseUrl}${basePath}${normalizedPath}`
    : `${basePath}${normalizedPath}`;
};

const fetchJson = async (path, options = {}) => {
  const response = await fetch(buildUrl(path), options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }
  return response.json();
};

const stringifyCandidateValue = (value, depth = 0) => {
  const indent = "  ".repeat(depth);
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (item && typeof item === "object") {
          return `${indent}-\n${stringifyCandidateValue(item, depth + 1)}`;
        }
        return `${indent}- ${item}`;
      })
      .join("\n");
  }
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([key, nested]) => `${indent}${key}\n${stringifyCandidateValue(nested, depth + 1)}`)
      .join("\n");
  }
  return `${indent}${value ?? ""}`;
};

const formatCandidateText = (candidate) => {
  if (!candidate || typeof candidate !== "object") {
    return "";
  }

  const sections = candidate.sections && typeof candidate.sections === "object"
    ? candidate.sections
    : candidate;
  const formattedSections = Object.entries(sections)
    .map(([key, value]) => `${key}\n${stringifyCandidateValue(value)}`)
    .join("\n\n")
    .trim();
  return formattedSections;
};

export const normalizeJobForUi = (job) => {
  const candidates = (job?.candidates ?? []).map((candidate, index) => ({
    id: index + 1,
    index,
    raw: candidate,
    text: formatCandidateText(candidate)
  }));

  const selectedIndex = job?.selected_candidate
    ? candidates.find((candidate) => candidate.text === formatCandidateText(job.selected_candidate))?.index ?? 0
    : candidates[0]?.index ?? 0;

  return {
    ...job,
    status: Object.values(JOB_STATUS).includes(job?.status) ? job.status : JOB_STATUS.CREATED,
    candidates,
    selectedIndex,
    selectedCandidateText: job?.selected_candidate
      ? formatCandidateText(job.selected_candidate)
      : candidates[0]?.text ?? ""
  };
};

export const createJob = (payload) => fetchJson("/minutes/jobs", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
});

export const getJob = (jobId) => fetchJson(`/minutes/jobs/${jobId}`);

export const reviewJob = (jobId, payload) => fetchJson(`/minutes/jobs/${jobId}/review`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
});
