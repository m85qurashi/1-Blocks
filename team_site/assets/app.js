const personaList = document.getElementById("persona-list");
const detailsPanel = document.getElementById("details");
const searchInput = document.getElementById("search");

let personas = [];
let activePersona = null;

const state = {
  loading: true,
  error: null,
};

const setDetailsContent = (html) => {
  detailsPanel.innerHTML = html;
};

function renderEmptyState(message = "Select a persona") {
  setDetailsContent(`
    <div class="empty-state">
      <h2>${message}</h2>
      <p>Review outstanding requests, file locations, and suggested response steps.</p>
    </div>
  `);
}

function createListItem(persona) {
  const li = document.createElement("li");
  li.className = "persona-item";
  li.dataset.persona = persona.name;
  li.innerHTML = `
    <h3>${persona.name}</h3>
    <p>${persona.role} — ${persona.focus}</p>
  `;

  li.addEventListener("click", () => {
    activePersona = persona;
    updateActiveListItem();
    renderPersonaDetails(persona);
  });

  return li;
}

function updateActiveListItem() {
  personaList.querySelectorAll(".persona-item").forEach((item) => {
    if (activePersona && item.dataset.persona === activePersona.name) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });
}

function renderPersonas(list) {
  personaList.innerHTML = "";
  if (!list.length) {
    personaList.innerHTML = `<li class="persona-item muted">No personas match that search.</li>`;
    renderEmptyState("No persona found");
    activePersona = null;
    return;
  }

  list.forEach((persona) => {
    personaList.appendChild(createListItem(persona));
  });
  updateActiveListItem();
}

function renderListSection(label, items) {
  if (!items?.length) return "";
  return `
    <div class="detail-row">
      <h4>${label}</h4>
      <ul>
        ${items.map((item) => `<li>${item}</li>`).join("")}
      </ul>
    </div>
  `;
}

function renderPaths(paths = []) {
  if (!paths.length) return "";
  return `
    <div class="detail-row">
      <h4>Key Paths</h4>
      <div class="path-grid">
        ${paths
          .map(
            (path) => `
          <div class="path-box">
            <span>${path}</span>
            <button type="button" data-copy="${path}">Copy</button>
          </div>
        `
          )
          .join("")}
      </div>
    </div>
  `;
}

function attachCopyHandlers() {
  detailsPanel.querySelectorAll("button[data-copy]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        btn.textContent = "Copied!";
        setTimeout(() => (btn.textContent = "Copy"), 1200);
      } catch (err) {
        btn.textContent = "Error";
        setTimeout(() => (btn.textContent = "Copy"), 1200);
      }
    });
  });
}

function renderPersonaDetails(persona) {
  setDetailsContent(`
    <div class="details-card">
      <div class="detail-header">
        <div>
          <h2>${persona.name}</h2>
          <p class="muted">${persona.role} — ${persona.focus}</p>
        </div>
        <span class="badge">${persona.requests.length} open items</span>
      </div>
      <div class="detail-row">
        <h4>What they owe</h4>
        <p>${persona.description}</p>
      </div>
      ${renderListSection("Requests", persona.requests)}
      ${renderListSection("How to respond", persona.steps)}
      ${renderPaths(persona.paths || persona.documents)}
    </div>
  `);
  attachCopyHandlers();
}

function filterPersonas(query) {
  if (!query) return personas;
  return personas.filter((persona) => {
    const haystack = `${persona.name} ${persona.role} ${persona.focus} ${persona.description}`.toLowerCase();
    return haystack.includes(query.toLowerCase());
  });
}

async function loadPersonas() {
  try {
    const response = await fetch("data/requests.json");
    if (!response.ok) throw new Error("Unable to load persona data");
    personas = await response.json();
    renderPersonas(personas);
    renderEmptyState();
    state.loading = false;
  } catch (error) {
    console.error(error);
    state.error = error.message;
    setDetailsContent(`
      <div class="empty-state">
        <h2>Unable to load personas</h2>
        <p>${error.message}</p>
      </div>
    `);
  }
}

searchInput?.addEventListener("input", (event) => {
  const query = event.target.value.trim();
  const filtered = filterPersonas(query);
  renderPersonas(filtered);
});

loadPersonas();
