/* ===========================================================================
   lazzycommit settings - front-end logic (vanilla JS, no build step).
   ---------------------------------------------------------------------------
   One in-memory `state` mirrors the editable config. The form mutates `state`;
   "dirty" is computed by diffing `state` against the last-saved snapshot. Lists
   (types, words, patterns) live in `state` and re-render on change, so there is
   a single source of truth rather than reading values out of the DOM at save.
   =========================================================================== */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

let state = null;
let saved = null;
let apiKeyInput = "";   // tracked separately; never round-tripped from the server
let fullApiKey = "";    // cached full API key when fetched from /api/config/key

async function api(method, url, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `${res.status} ${res.statusText}`);
  return data;
}

function toast(message, kind = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  const icon = kind === "ok" ? "i-check" : kind === "warn" ? "i-alert" : "i-x";
  el.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#${icon}"></use></svg><span>${message}</span>`;
  $("#toast-host").appendChild(el);
  setTimeout(() => {
    el.classList.add("leaving");
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

// Custom confirm dialog (replaces native confirm())
function showConfirm(title, message, isDanger = true) {
  return new Promise((resolve) => {
    const dialog = $("#confirm-dialog");
    const iconContainer = dialog.querySelector(".dialog-icon");
    if (iconContainer) {
      iconContainer.classList.toggle("danger", !!isDanger);
    }
    $("#confirm-title").textContent = title;
    $("#confirm-message").textContent = message;
    dialog.showModal();
    const cleanup = (result) => {
      dialog.close();
      ok.removeEventListener("click", onOk);
      cancel.removeEventListener("click", onCancel);
      dialog.removeEventListener("cancel", onCancel);
      resolve(result);
    };
    const onOk = () => cleanup(true);
    const onCancel = () => cleanup(false);
    const ok = $("#confirm-ok");
    const cancel = $("#confirm-cancel");
    ok.addEventListener("click", onOk);
    cancel.addEventListener("click", onCancel);
    dialog.addEventListener("cancel", onCancel);
  });
}

const clone = (o) => (window.structuredClone ? structuredClone(o) : JSON.parse(JSON.stringify(o)));

function markDirty() {
  const isKeyDirty = apiKeyInput.length > 0 && !apiKeyInput.includes("•") && apiKeyInput !== fullApiKey;
  const dirty = JSON.stringify(state) !== JSON.stringify(saved) || isKeyDirty;
  const ind = $("#dirty-indicator");
  ind.classList.toggle("dirty", dirty);
  ind.textContent = dirty ? "Unsaved changes" : "All changes saved";
  $("#save").disabled = !dirty;
}

// THEME - cycle auto, light, dark; persisted across reloads.
const THEMES = ["auto", "light", "dark"];
const THEME_ICON = { auto: "i-monitor", light: "i-sun", dark: "i-moon" };

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $("#theme-toggle .theme-icon use").setAttribute("href", "#" + THEME_ICON[theme]);
  localStorage.setItem("lazzy-theme", theme);
}
$("#theme-toggle").addEventListener("click", () => {
  const current = localStorage.getItem("lazzy-theme") || "dark";
  applyTheme(THEMES[(THEMES.indexOf(current) + 1) % THEMES.length]);
});

// TABS - toggle active panel; lazy-load history the first time it opens.
let historyLoaded = false;
$$(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    $$(".tab").forEach((t) => t.classList.remove("is-active"));
    $$(".panel").forEach((p) => p.classList.remove("is-active"));
    tab.classList.add("is-active");
    $(`.panel[data-panel="${tab.dataset.tab}"]`).classList.add("is-active");
    if (tab.dataset.tab === "history" && !historyLoaded) loadHistory();
  });
});

async function fetchModels(apiKey = "") {
  const select = $("#model");
  const status = $("#model-status");
  const currentVal = state ? state.ai.model : "";
  try {
    const keyToSend = apiKey.includes("•") ? "" : apiKey;
    const url = keyToSend ? `/api/models?api_key=${encodeURIComponent(keyToSend)}` : "/api/models";
    const res = await api("GET", url);
    select.innerHTML = "";
    if (res.models && res.models.length) {
      res.models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.name;
        opt.textContent = m.display_name;
        if (m.name === currentVal) opt.selected = true;
        select.appendChild(opt);
      });
      // If current model not in list, add it at top
      if (currentVal && !res.models.find(m => m.name === currentVal)) {
        const opt = document.createElement("option");
        opt.value = currentVal;
        opt.textContent = currentVal;
        opt.selected = true;
        select.prepend(opt);
      }
      status.textContent = `${res.models.length} models available`;
      status.className = "hint";
    } else {
      select.innerHTML = '<option value="" disabled>No models found</option>';
      if (currentVal) {
        const opt = document.createElement("option");
        opt.value = currentVal;
        opt.textContent = currentVal;
        opt.selected = true;
        select.prepend(opt);
      }
      status.textContent = res.error || "Could not load models";
      status.className = "hint inline-result err";
    }
  } catch (e) {
    console.error("Failed to load models list:", e);
    select.innerHTML = '<option value="" disabled>Failed to load</option>';
    if (currentVal) {
      const opt = document.createElement("option");
      opt.value = currentVal;
      opt.textContent = currentVal;
      opt.selected = true;
      select.prepend(opt);
    }
    status.textContent = "Failed to fetch models";
    status.className = "hint inline-result err";
  }
}

// LOAD + BIND
async function load() {
  const cfg = await api("GET", "/api/config");
  state = {
    ai: {
      model: cfg.ai.model,
      max_diff_chars: cfg.ai.max_diff_chars,
      prompt_template: cfg.ai.prompt_template,
    },
    validation: clone(cfg.validation),
    history: clone(cfg.history),
    ui: clone(cfg.ui),
  };
  saved = clone(state);
  apiKeyInput = "";
  fullApiKey = "";

  bindStaticInputs();
  renderKeyStatus(cfg.ai.api_key_set, cfg.ai.api_key_source, cfg.ai.api_key_preview);
  renderTypes();
  renderWords();
  renderPatterns();
  markDirty();

  await fetchModels();
}

function renderKeyStatus(isSet, source, preview) {
  const pill = $("#api-status");
  const text = $("#api-status-text");
  pill.className = "status-pill " + (isSet ? "status-pill--ok" : "status-pill--warn");
  pill.querySelector("use").setAttribute("href", isSet ? "#i-key" : "#i-alert");
  text.textContent = isSet
    ? `key active · ${source === "env" ? "env" : "saved"}`
    : "no api key set";

  const keyInput = $("#api-key");
  if (preview && isSet) {
    keyInput.value = preview;
    apiKeyInput = preview;
  } else {
    keyInput.value = "";
    apiKeyInput = "";
  }
  keyInput.placeholder = "AIza… (blank keeps current)";
}

function bindStaticInputs() {
  const v = state.validation;

  // Model select: set value after fetchModels populates options, listen for change
  $("#model").addEventListener("change", () => { state.ai.model = $("#model").value; markDirty(); });
  bindRange("#max-diff", "#max-diff-val", () => state.ai.max_diff_chars,
            (val) => (state.ai.max_diff_chars = val), (n) => `${(n / 1000).toFixed(0)}k`);
  bindText("#prompt-template", () => state.ai.prompt_template,
           (val) => (state.ai.prompt_template = val));

  bindSwitch("#check-api-keys", () => v.check_api_keys, (val) => (v.check_api_keys = val));
  bindSwitch("#check-sensitive", () => v.check_sensitive_data, (val) => (v.check_sensitive_data = val));

  bindSwitch("#enforce-conventional", () => v.enforce_conventional_commits,
             (val) => (v.enforce_conventional_commits = val));
  bindSwitch("#enforce-length", () => v.enforce_length_limit, (val) => (v.enforce_length_limit = val));
  bindSwitch("#allow-override", () => v.allow_override, (val) => (v.allow_override = val));
  bindRange("#max-subject", "#max-subject-val", () => v.max_subject_length,
            (val) => (v.max_subject_length = val));
  bindRange("#min-length", "#min-length-val", () => v.min_message_length,
            (val) => (v.min_message_length = val));

  bindSwitch("#history-enabled", () => state.history.enabled, (val) => (state.history.enabled = val));
}

function bindText(sel, get, set) {
  const el = $(sel);
  el.value = get() ?? "";
  el.addEventListener("input", () => { set(el.value); markDirty(); });
}
function bindSwitch(sel, get, set) {
  const el = $(sel);
  el.checked = !!get();
  el.addEventListener("change", () => { set(el.checked); markDirty(); });
}
function bindRange(sel, labelSel, get, set, fmt) {
  const el = $(sel);
  const label = $(labelSel);
  const render = () => (label.textContent = fmt ? fmt(Number(el.value)) : el.value);
  el.value = get();
  render();
  el.addEventListener("input", () => { set(Number(el.value)); render(); markDirty(); });
}

// CHIPS - allowed types and forbidden words
function renderChips(containerSel, list, onRemove) {
  const box = $(containerSel);
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<span class="empty-note">None yet.</span>`;
    return;
  }
  list.forEach((item, i) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = `<span>${item}</span><button class="x" title="Remove" aria-label="Remove ${item}">×</button>`;
    chip.querySelector(".x").addEventListener("click", () => onRemove(i));
    box.appendChild(chip);
  });
}
function renderTypes() {
  renderChips("#types-chips", state.validation.allowed_types, (i) => {
    state.validation.allowed_types.splice(i, 1);
    renderTypes(); markDirty();
  });
}
function renderWords() {
  renderChips("#words-chips", state.validation.forbidden_words, (i) => {
    state.validation.forbidden_words.splice(i, 1);
    renderWords(); markDirty();
  });
}
function addChip(inputSel, list, normalize, rerender) {
  const input = $(inputSel);
  const raw = normalize(input.value);
  if (!raw) return;
  if (list.includes(raw)) { toast("Already in the list", "err"); return; }
  list.push(raw);
  input.value = "";
  rerender(); markDirty();
}
$("#add-type").addEventListener("click", () =>
  addChip("#type-input", state.validation.allowed_types, (s) => s.trim().toLowerCase(), renderTypes));
$("#add-word").addEventListener("click", () =>
  addChip("#word-input", state.validation.forbidden_words, (s) => s.trim().toLowerCase(), renderWords));
$("#type-input").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#add-type").click(); });
$("#word-input").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#add-word").click(); });

// CUSTOM SECRET PATTERNS
function renderPatterns() {
  const box = $("#patterns-list");
  const list = state.validation.custom_secret_patterns;
  box.innerHTML = "";
  if (!list.length) {
    box.innerHTML = `<span class="empty-note">No custom patterns yet. Add one below.</span>`;
    return;
  }
  list.forEach((p, i) => {
    const row = document.createElement("div");
    row.className = "pattern-item";
    row.innerHTML =
      `<span class="p-name">${p.name}</span>` +
      `<span class="p-regex">${escapeHtml(p.pattern)}</span>` +
      `<button class="x" title="Remove">×</button>`;
    row.querySelector(".x").addEventListener("click", () => {
      list.splice(i, 1); renderPatterns(); markDirty();
    });
    box.appendChild(row);
  });
}
$("#add-pattern").addEventListener("click", () => {
  const name = $("#pattern-name").value.trim();
  const pattern = $("#pattern-regex").value;
  const err = $("#pattern-error");
  err.textContent = "";
  if (!name || !pattern) { err.textContent = "Both a name and a regex are required."; err.className = "inline-result err"; return; }
  try { new RegExp(pattern); } catch (e) {
    err.textContent = `Invalid regex: ${e.message}`; err.className = "inline-result err"; return;
  }
  state.validation.custom_secret_patterns.push({ name, pattern });
  $("#pattern-name").value = ""; $("#pattern-regex").value = "";
  renderPatterns(); markDirty();
});

const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// PROMPT EDITOR
$$(".placeholder-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const area = $("#prompt-template");
    const ph = chip.dataset.ph;
    const start = area.selectionStart, end = area.selectionEnd;
    area.value = area.value.slice(0, start) + ph + area.value.slice(end);
    area.selectionStart = area.selectionEnd = start + ph.length;
    area.dispatchEvent(new Event("input"));
    area.focus();
  });
});
$("#reset-prompt").addEventListener("click", async () => {
  const confirmed = await showConfirm(
    "Reset prompt template?",
    "This will replace your custom prompt template with the system default. You must click 'Save changes' to persist this reset.",
    false
  );
  if (!confirmed) return;
  const { prompt_template } = await api("GET", "/api/defaults/prompt");
  state.ai.prompt_template = prompt_template;
  $("#prompt-template").value = prompt_template;
  markDirty();
  toast("Prompt reset to default, save to keep it");
});
$("#prompt-template").addEventListener("input", () => { $("#prompt-error").textContent = ""; });

// KEY TEST + SHOW/HIDE
$("#toggle-key").addEventListener("click", async (e) => {
  const input = $("#api-key");
  const revealed = input.type === "password";
  
  if (revealed) {
    if (input.value.includes("•") && !fullApiKey) {
      try {
        const res = await api("GET", "/api/config/key");
        fullApiKey = res.api_key || "";
      } catch (err) {
        console.error("Failed to fetch full API key:", err);
      }
    }
    if (input.value.includes("•") && fullApiKey) {
      input.value = fullApiKey;
      apiKeyInput = fullApiKey;
      markDirty();
    }
    input.type = "text";
  } else {
    input.type = "password";
  }

  const btn = e.currentTarget;
  btn.querySelector("use").setAttribute("href", revealed ? "#i-eye-off" : "#i-eye");
  btn.setAttribute("aria-label", revealed ? "Hide key" : "Show key");
});
$("#api-key").addEventListener("input", (e) => { apiKeyInput = e.target.value; markDirty(); });
$("#api-key").addEventListener("keydown", (e) => {
  const input = e.target;
  // If the value contains bullets (is the preview), clear it on the first keypress of a normal character
  if (input.value.includes("•") && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
    input.value = "";
    apiKeyInput = "";
  }
});
$("#test-key").addEventListener("click", async () => {
  const out = $("#key-test-result");
  out.textContent = "Testing"; out.className = "inline-result";
  try {
    const keyVal = apiKeyInput.trim();
    const body = keyVal && !keyVal.includes("•") ? { api_key: keyVal } : {};
    const res = await api("POST", "/api/test-key", body);
    out.textContent = res.message;
    out.className = "inline-result " + (res.ok ? "ok" : "err");
    if (res.ok) {
      await fetchModels(keyVal);
    }
  } catch (e) {
    out.textContent = e.message; out.className = "inline-result err";
  }
});

$("#refresh-models").addEventListener("click", async () => {
  const btn = $("#refresh-models");
  btn.classList.add("spinning");
  await fetchModels(apiKeyInput.trim());
  setTimeout(() => btn.classList.remove("spinning"), 500);
  toast("Model list refreshed");
});

// SAVE / DISCARD
$("#save").addEventListener("click", async () => {
  const err = validateBeforeSave();
  if (err) { toast(err, "err"); return; }

  const patch = clone(state);
  const keyVal = apiKeyInput.trim();
  if (keyVal && !keyVal.includes("•")) {
    patch.ai.api_key = keyVal;
  }

  try {
    const res = await api("PUT", "/api/config", patch);
    saved = clone(state);
    apiKeyInput = "";
    $("#api-key").value = "";
    fullApiKey = "";
    renderKeyStatus(res.ai.api_key_set, res.ai.api_key_source, res.ai.api_key_preview);
    markDirty();
    toast("Settings saved");
    await fetchModels();
  } catch (e) {
    toast(e.message, "err");
  }
});
$("#discard").addEventListener("click", async () => {
  const isKeyDirty = apiKeyInput.length > 0 && !apiKeyInput.includes("•") && apiKeyInput !== fullApiKey;
  const isDirty = JSON.stringify(state) !== JSON.stringify(saved) || isKeyDirty;
  if (isDirty) {
    const confirmed = await showConfirm(
      "Discard unsaved changes?",
      "Are you sure you want to revert all fields to their last saved state? Your current edits will be lost.",
      false
    );
    if (!confirmed) return;
  }
  state = clone(saved);
  apiKeyInput = "";
  $("#api-key").value = "";
  fullApiKey = "";
  bindStaticInputs();
  renderTypes(); renderWords(); renderPatterns();
  markDirty();
  toast("Reverted to last saved");
});

function validateBeforeSave() {
  const v = state.validation;
  if (!state.ai.prompt_template.includes("{files_summary}") ||
      !state.ai.prompt_template.includes("{diffs}")) {
    $$(".tab").find((t) => t.dataset.tab === "prompt").click();
    $("#prompt-error").textContent = "Prompt must keep {files_summary} and {diffs}.";
    $("#prompt-error").className = "inline-result err";
    return "Prompt is missing a required placeholder.";
  }
  if (!v.allowed_types.length) return "Add at least one allowed commit type.";
  if (v.min_message_length > v.max_subject_length) return "Min length cannot exceed max subject length.";
  return null;
}

// HISTORY & STATS
async function loadHistory() {
  historyLoaded = true;
  try {
    const stats = await api("GET", "/api/stats");
    $("#stat-total").textContent = stats.total;
    $("#stat-accept").textContent = stats.total ? `${stats.acceptance_rate}%` : "0%";
    $("#stat-overrides").textContent = stats.overrides;
    renderDist(stats.by_type);
    renderRecent(stats.recent);
  } catch (e) {
    toast(`Could not load stats: ${e.message}`, "err");
  }
}
function renderDist(byType) {
  const box = $("#type-dist");
  const entries = Object.entries(byType).sort((a, b) => b[1] - a[1]);
  if (!entries.length) { box.innerHTML = `<span class="empty-note">No commits recorded yet.</span>`; return; }
  const max = Math.max(...entries.map(([, n]) => n));
  box.innerHTML = entries.map(([type, n]) => `
    <div class="dist-row">
      <span class="d-type">${type}</span>
      <span class="dist-bar"><span style="width:${(n / max) * 100}%"></span></span>
      <span class="d-count">${n}</span>
    </div>`).join("");
}
function renderRecent(recent) {
  const box = $("#recent-list");
  if (!recent || !recent.length) { box.innerHTML = `<span class="empty-note">Nothing here yet. Make a commit with lazzycommit.</span>`; return; }
  box.innerHTML = recent.map((r) => `
    <div class="recent-item">
      <span class="r-type">${r.type || "."}</span>
      <span class="r-subject">${escapeHtml(r.subject || "")}</span>
      <span class="r-outcome ${r.outcome}">${r.outcome}</span>
      <span class="r-meta">${formatTime(r.timestamp)}</span>
    </div>`).join("");
}
function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}
$("#clear-history").addEventListener("click", async () => {
  const confirmed = await showConfirm(
    "Clear history?",
    "Delete all recorded commit history? This cannot be undone."
  );
  if (!confirmed) return;
  try {
    await api("DELETE", "/api/history");
    historyLoaded = false;
    await loadHistory();
    toast("History cleared");
  } catch (e) { toast(e.message, "err"); }
});

// BOOT
applyTheme(localStorage.getItem("lazzy-theme") || "dark");
window.addEventListener("beforeunload", (e) => {
  const isKeyDirty = apiKeyInput.length > 0 && !apiKeyInput.includes("•");
  if (JSON.stringify(state) !== JSON.stringify(saved) || isKeyDirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});
load().catch((e) => toast(`Failed to load settings: ${e.message}`, "err"));
