/* Loaded only by scripts/local_preview.py, never by the published website. */
document.addEventListener("DOMContentLoaded", () => {
  const config = JSON.parse(document.getElementById("local-editor-config").textContent);
  const fields = new Map();
  let editing = false;
  let saving = false;

  function bind(element, file, id, rich = true) {
    if (!element || element.querySelector("mjx-container, svg, math")) return;
    element.dataset.localEditable = "true";
    fields.set(element, { file, id, rich, original: rich ? element.innerHTML : element.textContent });
  }

  document.querySelectorAll("[data-local-field]").forEach(el => bind(el, config.file, el.dataset.localField));
  if (config.content) {
    const { personal, publications, projects, posts } = config.content.data;
    const dataBind = (selector, id, rich = false) => bind(document.querySelector(selector), "content.js", id, rich);
    dataBind(".hero-info h1", "personal.name");
    dataBind(".hero-info h5", "personal.title");
    document.querySelectorAll(".about-content > p").forEach((el, i) => {
      bind(el, "content.js", ["personal.currentPosition", "personal.researchFocus"][i], true);
    });
    const lists = document.querySelectorAll(".about-content > ul");
    lists[0]?.querySelectorAll("li").forEach((li, i) => {
      const education = personal.education[i];
      li.replaceChildren();
      function part(key) {
        const span = document.createElement("span");
        span.textContent = education[key];
        li.append(span);
        bind(span, "content.js", `personal.education.${i}.${key}`, false);
      }
      part("degree"); li.append(", "); part("institution"); li.append(" ("); part("years"); li.append(")");
      if (education.honors) { li.append(", "); part("honors"); }
    });
    ["teaching", "awards"].forEach((name, i) => {
      lists[i + 1]?.querySelectorAll("li").forEach((el, j) => bind(el, "content.js", `personal.${name}.${j}`, false));
    });
    document.querySelectorAll(".publication").forEach((el, i) => {
      if (!publications[i]) return;
      bind(el.querySelector("h4"), "content.js", `publications.${i}.title`, false);
      bind(el.querySelector("p"), "content.js", `publications.${i}.conference`, false);
    });
    document.querySelectorAll(".project").forEach((el, i) => {
      if (!projects[i]) return;
      bind(el.querySelector("h4"), "content.js", `projects.${i}.name`, false);
      bind(el.querySelector("p"), "content.js", `projects.${i}.description`, false);
    });
    document.querySelectorAll(".posts .post").forEach(el => {
      // The homepage sorts posts; use their links to retain the source indices.
      const i = posts.findIndex(post => post.link === el.querySelector("a").getAttribute("href"));
      if (i < 0) return;
      bind(el.querySelector("h4"), "content.js", `posts.${i}.title`, false);
      bind(el.querySelector("p"), "content.js", `posts.${i}.snippet`, false);
    });
  }

  const style = document.createElement("style");
  style.textContent = `
    body { padding-bottom: 100px !important; }
    #local-editor-bar { position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%); z-index: 2147483647;
      width: max-content; max-width: calc(100% - 24px); display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
      padding: 12px 16px; background: #172033; color: #f3f4f6; border: 1px solid #64748b; border-radius: 12px;
      box-shadow: 0 8px 32px #0008; font: 14px/1.5 system-ui, sans-serif; }
    #local-editor-bar button { border: 1px solid #94a3b8; border-radius: 6px; padding: 7px 12px;
      background: #26354d; color: #fff; font: inherit; cursor: pointer; }
    #local-editor-bar button:disabled { opacity: .45; cursor: default; }
    #local-editor-bar button[data-save] { background: #2563eb; border-color: #60a5fa; }
    #local-editor-status { max-width: 420px; }
    body.local-editing [data-local-editable] { outline: 1px dashed #60a5fa88; outline-offset: 4px; cursor: text; }
    body.local-editing [data-local-editable]:focus { outline: 2px solid #60a5fa; }
    body.local-editing [data-local-dirty] { outline-color: #fbbf24; }
    @media (max-width: 600px) { #local-editor-status { flex-basis: 100%; max-width: 100%; } }
  `;
  document.head.append(style);
  const bar = document.createElement("div");
  bar.id = "local-editor-bar";
  bar.setAttribute("role", "region");
  bar.setAttribute("aria-label", "Local text editor");
  bar.innerHTML = `<strong>Local editor</strong><button type="button" data-toggle>Edit text</button>
    <button type="button" data-save disabled>Save</button><button type="button" data-discard disabled>Discard</button>
    <span id="local-editor-status" role="status" aria-live="polite">Edit text, then save to your website files.</span>`;
  document.body.append(bar);
  const toggle = bar.querySelector("[data-toggle]");
  const saveButton = bar.querySelector("[data-save]");
  const discard = bar.querySelector("[data-discard]");
  const status = bar.querySelector("[role=status]");
  const valueOf = (el, field) => field.rich ? el.innerHTML : el.textContent;
  const changed = () => [...fields].filter(([el, field]) => valueOf(el, field) !== field.original);

  function update(message) {
    const count = changed().length;
    for (const [el, field] of fields) el.toggleAttribute("data-local-dirty", valueOf(el, field) !== field.original);
    saveButton.disabled = saving || !count;
    discard.disabled = saving || !count;
    toggle.disabled = saving;
    status.textContent = message || (count ? `${count} unsaved ${count === 1 ? "change" : "changes"}` : editing ? "Click any outlined text to edit it." : "Edit text, then save to your website files.");
  }

  toggle.addEventListener("click", () => {
    editing = !editing;
    document.body.classList.toggle("local-editing", editing);
    for (const el of fields.keys()) {
      el.contentEditable = editing ? "true" : "false";
      el.spellcheck = editing;
    }
    toggle.textContent = editing ? "Done editing" : "Edit text";
    toggle.setAttribute("aria-pressed", String(editing));
    update();
  });

  discard.addEventListener("click", () => {
    for (const [el, field] of fields) {
      if (field.rich) el.innerHTML = field.original;
      else el.textContent = field.original;
    }
    update("Unsaved changes discarded.");
  });

  function insertText(text) {
    const selection = window.getSelection();
    if (!selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    range.deleteContents();
    const fragment = document.createDocumentFragment();
    text.split(/\r?\n/).forEach((line, i) => {
      if (i) fragment.append(document.createElement("br"));
      fragment.append(document.createTextNode(line));
    });
    const last = fragment.lastChild;
    range.insertNode(fragment);
    if (last) { range.setStartAfter(last); range.collapse(true); selection.removeAllRanges(); selection.addRange(range); }
    update();
  }

  for (const [el, field] of fields) {
    el.addEventListener("input", () => update());
    el.addEventListener("paste", event => {
      if (!editing) return;
      event.preventDefault();
      const text = event.clipboardData.getData("text/plain");
      insertText(field.rich ? text : text.replace(/\s*\n\s*/g, " "));
    });
    el.addEventListener("drop", event => { if (editing) event.preventDefault(); });
    el.addEventListener("keydown", event => {
      if (editing && event.key === "Enter") {
        event.preventDefault();
        insertText(field.rich ? "\n" : " ");
      }
    });
  }
  document.addEventListener("click", event => {
    if (editing && event.target.closest("[data-local-editable] a")) event.preventDefault();
  }, true);
  window.addEventListener("beforeunload", event => {
    if (changed().length) { event.preventDefault(); event.returnValue = ""; }
  });

  async function save() {
    const pending = changed();
    if (!pending.length || saving) return;
    saving = true;
    for (const el of fields.keys()) el.contentEditable = "false";
    update("Saving…");
    try {
      const groups = new Map();
      for (const [el, field] of pending) {
        if (!groups.has(field.file)) groups.set(field.file, []);
        groups.get(field.file).push({ id: field.id, value: valueOf(el, field), element: el, field });
      }
      for (const [file, edits] of groups) {
        const response = await fetch("/__local-editor/save", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Local-Editor": config.token },
          body: JSON.stringify({ file, revision: file === "content.js" ? config.content.revision : config.revision,
            edits: edits.map(({id, value}) => ({id, value})) }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Could not save changes.");
        if (file === "content.js") config.content.revision = result.revision;
        else config.revision = result.revision;
        for (const edit of edits) edit.field.original = valueOf(edit.element, edit.field);
      }
      update("Saved to your website files.");
    } catch (error) {
      update(error.message);
    } finally {
      saving = false;
      for (const el of fields.keys()) el.contentEditable = editing ? "true" : "false";
      const message = status.textContent;
      update(message);
    }
  }
  saveButton.addEventListener("click", save);
  document.addEventListener("keydown", event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      save();
    }
  });
});
