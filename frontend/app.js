import { api } from "./api.js";

const $ = (id) => document.getElementById(id);
const STORAGE_KEY = "technova-conversations-v1";
const state = {
  view: "assistant",
  active: null,
  conversations: loadHistory(),
  status: null,
  busy: null,
  libraryRequest: 0,
  documentRequest: 0,
};
let toastTimer;
let searchTimer;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#i-${name}`);
  svg.setAttribute("aria-hidden", "true");
  svg.append(use);
  return svg;
}
function action(label, className, onClick, iconName) {
  const button = element("button", className);
  button.type = "button";
  if (iconName) button.append(icon(iconName));
  if (label) button.append(document.createTextNode(label));
  button.addEventListener("click", onClick);
  return button;
}
function toast(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    $("toast").hidden = true;
  }, 4000);
}
function loadHistory() {
  try {
    const history = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    if (!Array.isArray(history)) return [];
    return history
      .filter(
        (c) =>
          c &&
          typeof c.id === "string" &&
          typeof c.title === "string" &&
          Array.isArray(c.messages),
      )
      .slice(0, 30)
      .map((c) => ({
        ...c,
        messages: c.messages.filter(
          (m) =>
            m &&
            ["user", "assistant", "error"].includes(m.role) &&
            typeof m.text === "string",
        ),
      }));
  } catch {
    return [];
  }
}
function saveHistory() {
  state.conversations = state.conversations.slice(0, 30);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.conversations));
  } catch {
    toast(
      "Browser storage is full or unavailable. Export this conversation to keep a copy.",
    );
  }
  renderHistory();
}
function activeConversation() {
  return state.conversations.find((c) => c.id === state.active);
}
function setSidebar(open) {
  $("sidebar").classList.toggle("open", open);
  $("sidebar-backdrop").hidden = !open;
  $("menu-toggle").setAttribute("aria-expanded", String(open));
}
function setView(view) {
  state.view = view;
  const library = view === "library";
  $("home-view").hidden = library || Boolean(state.active);
  $("conversation-view").hidden = library || !state.active;
  $("library-view").hidden = !library;
  $("composer-area").hidden = library;
  $("page-label").textContent = library ? "Knowledge library" : "AI Assistant";
  $("nav-assistant").classList.toggle("active", !library);
  $("nav-library").classList.toggle("active", library);
  setSidebar(false);
  if (library) loadDocuments();
  else renderConversation();
}
function newChat() {
  state.active = null;
  $("question").value = "";
  updateComposer();
  setView("assistant");
  renderHistory();
  $("question").focus();
}
function renderHistory() {
  const root = $("recent-chats");
  root.replaceChildren();
  if (!state.conversations.length) {
    root.append(
      element(
        "p",
        "history-empty",
        "A little curiosity goes a long way. Your conversations will appear here.",
      ),
    );
    return;
  }
  for (const conversation of state.conversations) {
    const row = element(
      "div",
      `recent-item${state.active === conversation.id ? " current" : ""}`,
    );
    const open = action(
      "",
      "recent-open",
      () => {
        state.active = conversation.id;
        setView("assistant");
        renderHistory();
      },
      "chat",
    );
    open.append(element("span", "", conversation.title));
    open.title = conversation.title;
    if (state.active === conversation.id)
      open.setAttribute("aria-current", "true");
    const remove = action(
      "",
      "recent-delete",
      () => {
        if (state.busy === conversation.id) {
          toast(
            "Please wait for this answer before deleting the conversation.",
          );
          return;
        }
        state.conversations = state.conversations.filter(
          (c) => c.id !== conversation.id,
        );
        if (state.active === conversation.id) newChat();
        saveHistory();
        toast("Conversation deleted.");
      },
      "trash",
    );
    remove.setAttribute(
      "aria-label",
      `Delete conversation: ${conversation.title}`,
    );
    row.append(open, remove);
    root.append(row);
  }
}
function renderConversation() {
  const conversation = activeConversation();
  if (!conversation) return;
  $("conversation-title").textContent = conversation.title;
  const root = $("messages");
  root.replaceChildren();
  for (const message of conversation.messages) {
    const row = element(
      "article",
      `message ${message.role === "user" ? "user" : "assistant"}`,
    );
    const avatar = element(
      "div",
      "message-avatar",
      message.role === "user" ? "TN" : undefined,
    );
    avatar.setAttribute("aria-hidden", "true");
    if (message.role !== "user") avatar.append(icon("spark"));
    const content = element("div", "message-content");
    const label = element(
      "div",
      "message-label",
      message.role === "user" ? "You" : "TechNova",
    );
    if (message.mode)
      label.append(
        element(
          "span",
          "message-time",
          message.mode === "local" ? "Local search" : "AI Assistant",
        ),
      );
    content.append(label);
    if (message.role === "error") {
      const error = element("div", "error-message", message.text);
      error.append(
        action("Try again", "", () => {
          if (state.busy) return;
          conversation.messages = conversation.messages.filter(
            (m) => m !== message,
          );
          sendQuestion(message.query, false);
        }),
      );
      content.append(error);
    } else {
      content.append(element("div", "message-body", message.text));
      if (message.role === "assistant") renderAnswerExtras(content, message);
    }
    row.append(avatar, content);
    root.append(row);
  }
  if (state.busy === conversation.id) {
    const loading = element("div", "message assistant");
    loading.setAttribute("role", "status");
    const avatar = element("div", "message-avatar");
    avatar.append(icon("spark"));
    const thinking = element("div", "thinking");
    const dots = element("span", "thinking-dots");
    dots.append(element("i"), element("i"), element("i"));
    thinking.append(
      dots,
      document.createTextNode("Finding answers in your knowledge base…"),
    );
    loading.append(avatar, thinking);
    root.append(loading);
  }
}
function renderAnswerExtras(content, message) {
  const meta = element("div", "answer-meta");
  const badge = element("span", "grounded-badge");
  badge.append(
    icon(message.grounded ? "check" : "search"),
    document.createTextNode(
      message.grounded
        ? message.mode === "local"
          ? "From your documents"
          : "Verified against sources"
        : "No verified answer",
    ),
  );
  badge.title = message.verification_reason || "";
  meta.append(badge);
  if (typeof message.latency_ms === "number")
    meta.append(
      element("span", "", `${(message.latency_ms / 1000).toFixed(2)}s`),
    );
  content.append(meta);
  if (Array.isArray(message.sources) && message.sources.length) {
    content.append(
      element("div", "source-label", `SOURCES · ${message.sources.length}`),
    );
    const sources = element("div", "sources");
    message.sources.forEach((source, index) => {
      const card = action("", "source-card", () =>
        openDocument(source.document_id),
      );
      const label = element("span");
      label.append(
        element("strong", "", `${index + 1}. ${source.title}`),
        element("small", "", `${source.department} · v${source.version}`),
      );
      card.append(icon("file"), label, icon("chevron"));
      sources.append(card);
    });
    content.append(sources);
  }
  const actions = element("div", "answer-actions");
  actions.append(
    action(
      "Copy answer",
      "answer-action",
      async () => {
        try {
          await navigator.clipboard.writeText(message.text);
          toast("Answer copied.");
        } catch {
          toast("Clipboard unavailable. Select and copy the answer text.");
        }
      },
      "copy",
    ),
  );
  content.append(actions);
}
function updateComposer() {
  $("send-question").disabled =
    Boolean(state.busy) || !$("question").value.trim();
  $("question").style.height = "auto";
  $("question").style.height = `${Math.min($("question").scrollHeight, 150)}px`;
}
async function sendQuestion(value, appendUser = true) {
  const query = value?.trim();
  if (!query || state.busy) return;
  if (query.length > 2000) {
    toast("Please keep your question under 2,000 characters.");
    return;
  }
  let conversation = activeConversation();
  if (!conversation) {
    conversation = {
      id: crypto.randomUUID(),
      title: query.slice(0, 75),
      messages: [],
      created: Date.now(),
    };
    state.conversations.unshift(conversation);
    state.active = conversation.id;
  }
  if (appendUser) conversation.messages.push({ role: "user", text: query });
  state.busy = conversation.id;
  $("question").value = "";
  updateComposer();
  setView("assistant");
  saveHistory();
  $("composer-area").scrollIntoView({ behavior: "smooth", block: "end" });
  try {
    const result = await api.query(query);
    conversation.messages.push({
      role: "assistant",
      text: result.answer,
      ...result,
    });
    if (!state.status) connect();
  } catch (error) {
    conversation.messages.push({ role: "error", text: error.message, query });
    if (error.status === 401) showSettings();
  } finally {
    state.busy = null;
    saveHistory();
    updateComposer();
    if (state.active === conversation.id && state.view === "assistant") {
      renderConversation();
      $("composer-area").scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }
}
async function connect() {
  try {
    state.status = await api.status();
    const data = state.status;
    $("connection-status").className = "connection-pill connected";
    $("connection-status").replaceChildren(
      element("span", "status-dot"),
      document.createTextNode("Knowledge connected"),
    );
    $("nav-doc-count").textContent = data.document_count;
    $("knowledge-summary").textContent =
      `${data.document_count} documents across ${Object.keys(data.departments).length} departments, ready when you are.`;
    $("mode-label").textContent =
      data.mode === "local" ? "Local search" : "TechNova AI";
    $("profile-role").textContent = data.access_level
      .toLowerCase()
      .replaceAll("_", " ");
    const selected = $("department-filter").value;
    $("department-filter").replaceChildren(new Option("All departments", ""));
    Object.keys(data.departments).forEach((dept) =>
      $("department-filter").append(new Option(dept, dept)),
    );
    $("department-filter").value = selected;
    $("settings-details").textContent =
      `Mode: ${data.mode === "local" ? "Local document search" : "Groq AI with grounding verification"} · Access: ${data.access_level} · ${data.document_count} available documents. Mode and access are configured on the workspace server.`;
    if (state.view === "library") loadDocuments();
  } catch (error) {
    state.status = null;
    $("connection-status").className = "connection-pill offline";
    $("connection-status").replaceChildren(
      element("span", "status-dot"),
      document.createTextNode(
        error.status === 401 ? "Key required" : "Connection unavailable",
      ),
    );
    $("settings-details").textContent = error.message;
    if (error.status === 401) showSettings();
    else toast(error.message);
  }
}
const departments = {
  HR: ["people", "peach"],
  Engineering: ["code", "violet"],
  Security: ["shield", "mint"],
  DevOps: ["layers", "blue"],
  "AI & ML": ["spark", "violet"],
};
async function loadDocuments() {
  const requestId = ++state.libraryRequest;
  const root = $("document-grid");
  $("library-count").textContent = "Loading documents…";
  root.replaceChildren(
    element("div", "empty-state", "Opening your knowledge library…"),
  );
  try {
    const result = await api.documents(
      $("document-search").value.trim(),
      $("department-filter").value,
    );
    if (requestId !== state.libraryRequest) return;
    root.replaceChildren();
    $("library-count").textContent =
      `${result.documents.length} document${result.documents.length === 1 ? "" : "s"}`;
    if (!result.documents.length) {
      const empty = element("div", "empty-state");
      empty.append(
        icon("search"),
        element("strong", "", "No documents found"),
        document.createTextNode(
          "Try another keyword or choose a different department.",
        ),
      );
      root.append(empty);
    }
    for (const doc of result.documents) {
      const card = action("", "document-card", () =>
        openDocument(doc.document_id),
      );
      const top = element("div", "document-card-top");
      const [iconName, color] = departments[doc.department] || [
        "file",
        "violet",
      ];
      const topic = element("span", `topic-icon ${color}`);
      topic.append(icon(iconName));
      top.append(topic, element("span", "", `v${doc.version}`));
      const bottom = element("div", "document-card-bottom", doc.department);
      bottom.append(icon("chevron"));
      card.append(
        top,
        element("h2", "", doc.title),
        element("p", "", doc.preview.replace(doc.title, "").trim()),
        bottom,
      );
      root.append(card);
    }
  } catch (error) {
    if (requestId !== state.libraryRequest) return;
    $("library-count").textContent = "Library unavailable";
    const errorBox = element("div", "empty-state", error.message);
    errorBox.append(action("Try again", "primary-button", loadDocuments));
    root.replaceChildren(errorBox);
    if (error.status === 401) showSettings();
  }
}
/** Render the small Markdown subset used by the repository without injecting HTML. */
function renderDocument(text) {
  const root = element("div", "document-body");
  let paragraph = [];
  let code = null;
  const flush = () => {
    if (paragraph.length) root.append(element("p", "", paragraph.join("\n")));
    paragraph = [];
  };
  for (const line of text.split("\n")) {
    if (line.startsWith("```")) {
      flush();
      if (code !== null) {
        root.append(element("pre", "", code.join("\n")));
        code = null;
      } else code = [];
      continue;
    }
    if (code !== null) {
      code.push(line);
      continue;
    }
    const heading = /^(#{1,3})\s+(.+)$/.exec(line);
    if (heading) {
      flush();
      root.append(element(`h${heading[1].length}`, "", heading[2]));
    } else if (!line.trim()) flush();
    else paragraph.push(line);
  }
  flush();
  if (code !== null) root.append(element("pre", "", code.join("\n")));
  return root;
}
async function openDocument(id) {
  const requestId = ++state.documentRequest;
  const dialog = $("document-dialog");
  $("document-content").replaceChildren(
    element("p", "empty-state", "Opening document…"),
  );
  if (!dialog.open) dialog.showModal();
  try {
    const doc = await api.document(id);
    if (requestId !== state.documentRequest) return;
    const meta = element("div", "document-meta");
    [doc.department, `Version ${doc.version}`, doc.document_type].forEach(
      (value) => meta.append(element("span", "", value)),
    );
    const ask = element("div", "document-ask");
    ask.append(
      action(
        "Ask about this topic",
        "primary-button",
        () => {
          dialog.close();
          setView("assistant");
          $("question").value =
            `What should I know about ${doc.title.toLowerCase()}?`;
          updateComposer();
          $("question").focus();
        },
        "spark",
      ),
    );
    $("document-content").replaceChildren(
      element("h1", "", doc.title),
      meta,
      renderDocument(doc.content),
      ask,
    );
  } catch (error) {
    if (requestId === state.documentRequest)
      $("document-content").replaceChildren(
        element("p", "error-message", error.message),
      );
  }
}
function showSettings() {
  $("api-key").value = sessionStorage.getItem("technova-api-key") || "";
  if (!$("settings-dialog").open) $("settings-dialog").showModal();
}
function exportConversation() {
  const conversation = activeConversation();
  if (!conversation) return;
  const messages = conversation.messages.map(
    (m) =>
      `## ${m.role === "user" ? "You" : "TechNova"}\n\n${m.text}\n\n${(m.sources || []).map((s) => `- ${s.title} (${s.document_id}, v${s.version})`).join("\n")}`,
  );
  const blob = new Blob(
    [`# ${conversation.title}\n\n${messages.join("\n\n")}\n`],
    { type: "text/markdown" },
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "technova-conversation.md";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast("Conversation exported.");
}

$("question-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendQuestion($("question").value);
});
$("question").addEventListener("input", updateComposer);
$("question").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    sendQuestion($("question").value);
  }
});
document
  .querySelectorAll("[data-prompt]")
  .forEach((button) =>
    button.addEventListener("click", () => sendQuestion(button.dataset.prompt)),
  );
$("new-chat").addEventListener("click", newChat);
$("nav-assistant").addEventListener("click", () => setView("assistant"));
for (const id of ["nav-library", "explore-library", "browse-documents"])
  $(id).addEventListener("click", () => setView("library"));
$("document-search").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadDocuments, 220);
});
$("department-filter").addEventListener("change", loadDocuments);
$("menu-toggle").addEventListener("click", () =>
  setSidebar(!$("sidebar").classList.contains("open")),
);
$("sidebar-backdrop").addEventListener("click", () => setSidebar(false));
$("help").addEventListener("click", () => {
  setSidebar(false);
  $("help-dialog").showModal();
});
for (const id of ["settings", "top-settings"])
  $(id).addEventListener("click", () => {
    setSidebar(false);
    showSettings();
  });
$("export-chat").addEventListener("click", exportConversation);
$("settings-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const key = $("api-key").value.trim();
  if (key) sessionStorage.setItem("technova-api-key", key);
  else sessionStorage.removeItem("technova-api-key");
  $("settings-dialog").close();
  connect();
});
document
  .querySelectorAll("[data-close]")
  .forEach((button) =>
    button.addEventListener("click", () => $(button.dataset.close).close()),
  );
document.querySelectorAll("dialog").forEach((dialog) =>
  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom
    )
      dialog.close();
  }),
);
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setSidebar(false);
  const inDialog = Boolean(document.querySelector("dialog[open]"));
  if ((event.metaKey || event.ctrlKey) && event.key === "k" && !inDialog) {
    event.preventDefault();
    newChat();
  }
  if (
    event.key === "/" &&
    state.view === "library" &&
    !inDialog &&
    !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)
  ) {
    event.preventDefault();
    $("document-search").focus();
  }
});
renderHistory();
connect();
