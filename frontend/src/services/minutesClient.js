const backendBaseUrl = (import.meta.env.VITE_BACKEND_BASE_URL ?? "").replace(/\/$/, "");
const apiBasePath = (import.meta.env.VITE_API_BASE_PATH ?? "").replace(/\/$/, "");

const normalizePath = (path) => (path.startsWith("/") ? path : `/${path}`);

const buildUrl = (path) => {
  const normalizedPath = normalizePath(path);
  const basePath = apiBasePath ? normalizePath(apiBasePath) : "";
  return backendBaseUrl
    ? `${backendBaseUrl}${basePath}${normalizedPath}`
    : `${basePath}${normalizedPath}`;
};

const shouldRetryWithRelativeUrl = (error) => backendBaseUrl && error instanceof TypeError;

const fetchWithRelativeFallback = async (path, options) => {
  const primaryUrl = buildUrl(path);
  try {
    return await fetch(primaryUrl, options);
  } catch (error) {
    if (!shouldRetryWithRelativeUrl(error)) {
      throw error;
    }
    const fallbackUrl = `${apiBasePath ? normalizePath(apiBasePath) : ""}${normalizePath(path)}`;
    console.warn(`Primary API endpoint is unreachable. Falling back to ${fallbackUrl}.`, error);
    return fetch(fallbackUrl, options);
  }
};

const fetchJson = async (path, options = {}) => {
  const response = await fetchWithRelativeFallback(path, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }
  return response.json();
};

const stringifyCandidateValue = (value) => {
  if (Array.isArray(value)) {
    return value.map((item) => `- ${item}`).join("\n");
  }
  if (value && typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return `${value ?? ""}`;
};

const formatCandidateText = (candidate) => Object.entries(candidate ?? {})
  .map(([key, value]) => `${key}\n${stringifyCandidateValue(value)}`)
  .join("\n\n")
  .trim();

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
