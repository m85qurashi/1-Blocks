const baseInput = document.getElementById("base-url");
const apiKeyInput = document.getElementById("api-key");
const statusBar = document.getElementById("status-bar");
const ideasTableBody = document.querySelector("#ideas-table tbody");
const readinessTableBody = document.querySelector("#readiness-table tbody");
const wavesTableBody = document.querySelector("#waves-table tbody");

const state = {
  baseUrl: localStorage.getItem("readinessApiBase") || "http://localhost:8081",
  apiKey: localStorage.getItem("readinessApiKey") || "",
};

const readableDate = (value) => (value ? new Date(value).toLocaleDateString() : "—");

function setStatus(message, tone = "neutral") {
  if (!statusBar) return;
  statusBar.textContent = message;
  statusBar.dataset.tone = tone;
}

function applyStateToInputs() {
  if (baseInput) baseInput.value = state.baseUrl;
  if (apiKeyInput) apiKeyInput.value = state.apiKey;
}

applyStateToInputs();

async function request(path, options = {}) {
  if (!state.baseUrl) {
    throw new Error("Set the API base URL first.");
  }
  const headers = options.headers ? { ...options.headers } : {};
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (state.apiKey) {
    headers["X-API-Key"] = state.apiKey;
  }

  const response = await fetch(`${state.baseUrl}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return {};
  }

  return response.json();
}

function renderIdeas(data = []) {
  if (!ideasTableBody) return;
  ideasTableBody.innerHTML = "";
  data.forEach((idea) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${idea.name}</td>
      <td>${idea.sponsoring_team}</td>
      <td>${idea.workflow_family || "—"}</td>
      <td>${readableDate(idea.created_at)}</td>
    `;
    ideasTableBody.appendChild(row);
  });
}

function checksPassed(repo) {
  return ["training_completed", "cli_installed", "test_coverage_80", "runbook_acknowledged"].reduce(
    (total, field) => total + (repo[field] ? 1 : 0),
    0
  );
}

function renderReadiness(repos = []) {
  if (!readinessTableBody) return;
  readinessTableBody.innerHTML = "";
  repos.forEach((repo) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${repo.repo_name}</td>
      <td>${repo.owner || "—"}</td>
      <td><span class="pill" data-status="${repo.readiness_status}">${repo.readiness_status}</span></td>
      <td>${checksPassed(repo)}/4</td>
    `;
    readinessTableBody.appendChild(row);
  });
}

function renderWaves(summary = []) {
  if (!wavesTableBody) return;
  wavesTableBody.innerHTML = "";
  summary.forEach((wave) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${wave.wave}</td>
      <td>${wave.repo_count || 0}</td>
      <td>${readableDate(wave.earliest_date)}</td>
      <td>${readableDate(wave.latest_date)}</td>
    `;
    wavesTableBody.appendChild(row);
  });
}

async function refreshData() {
  try {
    setStatus("Refreshing data…", "neutral");
    const [ideas, readiness, waves] = await Promise.all([
      request("/api/ideas"),
      request("/api/readiness"),
      request("/api/waves/summary"),
    ]);
    renderIdeas(ideas.ideas || []);
    renderReadiness(readiness.repositories || []);
    renderWaves(waves.summary || []);
    setStatus("Dashboard updated.", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  }
}

function handleConnectionSubmit(event) {
  event.preventDefault();
  state.baseUrl = baseInput.value.trim();
  state.apiKey = apiKeyInput.value.trim();
  localStorage.setItem("readinessApiBase", state.baseUrl);
  localStorage.setItem("readinessApiKey", state.apiKey);
  setStatus("Settings saved. Loading data…", "neutral");
  refreshData();
}

function parseJson(value) {
  if (!value) return {};
  try {
    return JSON.parse(value);
  } catch (error) {
    throw new Error("Desired outcomes must be valid JSON.");
  }
}

async function handleIdeaSubmit(event) {
  event.preventDefault();
  try {
    const payload = {
      name: document.getElementById("idea-name").value.trim(),
      sponsoring_team: document.getElementById("idea-team").value.trim(),
      workflow_family: document.getElementById("idea-family").value,
      desired_outcomes: parseJson(document.getElementById("idea-outcomes").value),
      description: document.getElementById("idea-description").value.trim(),
    };

    await request("/api/ideas", { method: "POST", body: JSON.stringify(payload) });
    setStatus(`Idea "${payload.name}" created.`, "success");
    event.target.reset();
    refreshData();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function handleReadinessSubmit(event) {
  event.preventDefault();
  try {
    const payload = {
      repo_name: document.getElementById("repo-name").value.trim(),
      owner: document.getElementById("repo-owner").value.trim(),
      training_completed: document.getElementById("repo-training").value === "true",
      cli_installed: document.getElementById("repo-cli").value === "true",
      test_coverage_80: document.getElementById("repo-tests").value === "true",
      runbook_acknowledged: document.getElementById("repo-runbook").value === "true",
      notes: document.getElementById("repo-notes").value.trim(),
    };

    await request("/api/readiness", { method: "POST", body: JSON.stringify(payload) });
    setStatus(`Readiness updated for ${payload.repo_name}.`, "success");
    event.target.reset();
    refreshData();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function handleWaveSubmit(event) {
  event.preventDefault();
  try {
    const payload = {
      repo_name: document.getElementById("wave-repo").value.trim(),
      wave: document.getElementById("wave-name").value,
      scheduled_date: document.getElementById("wave-date").value || null,
      priority: Number(document.getElementById("wave-priority").value || 0),
    };

    await request("/api/waves/assign", { method: "POST", body: JSON.stringify(payload) });
    setStatus(`Wave updated for ${payload.repo_name}.`, "success");
    event.target.reset();
    refreshData();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

document.getElementById("connection-form")?.addEventListener("submit", handleConnectionSubmit);
document.getElementById("idea-form")?.addEventListener("submit", handleIdeaSubmit);
document.getElementById("readiness-form")?.addEventListener("submit", handleReadinessSubmit);
document.getElementById("wave-form")?.addEventListener("submit", handleWaveSubmit);

refreshData();
