const $ = (selector) => document.querySelector(selector);
let selected = null;
let view = "summary";
let busy = false;
const node = (tag, text, className = "") => {
  const el = document.createElement(tag);
  el.textContent = text;
  el.className = className;
  return el;
};
async function api(path, options = {}) {
  const response = await fetch("/api" + path, options);
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Invalid request. Check the fields.",
    );
  return data;
}
async function action(message, fn) {
  if (busy) return;
  busy = true;
  $("#notice").textContent = message;
  document.querySelectorAll("button").forEach((b) => (b.disabled = true));
  try {
    await fn();
    $("#notice").textContent = "";
  } catch (error) {
    $("#notice").textContent = error.message;
  } finally {
    busy = false;
    document.querySelectorAll("button").forEach((b) => (b.disabled = false));
    $("#question button").disabled = !selected;
  }
}
async function refresh() {
  const documents = await api("/documents");
  $("#count").textContent = documents.length;
  $("#library").replaceChildren(
    ...documents.map((doc) => {
      const button = node(
        "button",
        doc.name,
        "library-item" + (selected?.id === doc.id ? " selected" : ""),
      );
      button.append(
        node(
          "small",
          `${doc.pages} pages / ${doc.characters.toLocaleString()} characters`,
        ),
      );
      button.onclick = () => action("Opening document...", () => open(doc.id));
      return button;
    }),
  );
}
async function open(id) {
  selected = await api("/documents/" + id);
  $("#docName").textContent = selected.name;
  $("#meta").textContent =
    `${selected.pages} pages / ${selected.chunks.length} chunks / ${selected.model}`;
  $("#delete").hidden = false;
  $("#answer").replaceChildren(node("p", "No questions yet.", "empty"));
  if (selected.history.length) renderAnswer(selected.history[0]);
  render();
  await refresh();
}
function renderAnswer(item) {
  const target = $("#answer");
  target.replaceChildren(
    node("h3", item.question),
    node("p", item.answer, "prose"),
  );
  target.append(
    node(
      "h3",
      item.sources.length ? "Sources used" : "No supporting sources cited",
    ),
  );
  item.sources.forEach((source) => {
    const detail = node("details", "");
    detail.append(
      node("summary", `Page ${source.page} / chunk ${source.id}`),
      node("p", source.text),
    );
    target.append(detail);
  });
}
function render() {
  const content = $("#content");
  content.replaceChildren();
  if (!selected) {
    content.append(node("p", "Your document library is empty.", "empty"));
    return;
  }
  if (view === "summary") {
    content.append(
      node("p", selected.summary || "No summary generated yet.", "prose"),
    );
    const button = node(
      "button",
      selected.summary ? "Regenerate summary" : "Generate summary",
    );
    button.onclick = () =>
      action("Generating a local summary...", async () => {
        const result = await api(`/documents/${selected.id}/summary`, {
          method: "POST",
        });
        selected.summary = result.summary;
        render();
      });
    content.append(button);
  } else if (view === "text") {
    selected.chunks.forEach((chunk) => {
      const item = node("details", "");
      item.append(
        node("summary", `Page ${chunk.page} / chunk ${chunk.id}`),
        node("p", chunk.text),
      );
      content.append(item);
    });
  } else {
    if (!selected.history.length)
      content.append(node("p", "No questions yet.", "empty"));
    selected.history.forEach((item) => {
      const record = node("div", "", "record");
      const button = node("button", item.question);
      button.onclick = () => renderAnswer(item);
      record.append(
        node("time", new Date(item.created_at).toLocaleString()),
        button,
      );
      content.append(record);
    });
  }
}
document.querySelectorAll("[data-view]").forEach(
  (button) =>
    (button.onclick = () => {
      view = button.dataset.view;
      document
        .querySelectorAll("[data-view]")
        .forEach((b) => b.setAttribute("aria-pressed", b === button));
      render();
    }),
);
$("#sample").onclick = () =>
  action("Indexing sample PDF with local embeddings...", async () => {
    const doc = await api("/documents/sample", { method: "POST" });
    await open(doc.id);
  });
$("#upload").onsubmit = (event) => {
  event.preventDefault();
  action("Extracting and indexing PDF...", async () => {
    const doc = await api("/documents", {
      method: "POST",
      body: new FormData(event.target),
    });
    await open(doc.id);
    event.target.reset();
  });
};
$("#question").onsubmit = (event) => {
  event.preventDefault();
  action("Searching sources and generating an answer...", async () => {
    const item = await api(`/documents/${selected.id}/questions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: $("#prompt").value }),
    });
    selected.history.unshift(item);
    renderAnswer(item);
    render();
  });
};
$("#delete").onclick = () => {
  if (!confirm("Delete this document and its question history?")) return;
  action("Deleting document...", async () => {
    await api("/documents/" + selected.id, { method: "DELETE" });
    selected = null;
    $("#delete").hidden = true;
    $("#docName").textContent = "Select a document";
    $("#meta").textContent = "No document selected";
    $("#answer").replaceChildren();
    render();
    await refresh();
  });
};
action("Loading workspace...", async () => {
  await refresh();
  const health = await api("/health");
  $("#model").textContent = `Ollama / ${health.chat_model}`;
});
