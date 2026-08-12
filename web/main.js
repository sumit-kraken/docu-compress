document.addEventListener("DOMContentLoaded", () => {
  // Initialize Mermaid.js
  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    themeVariables: {
      darkMode: true,
      background: '#0d1117',
      primaryColor: '#7F00FF',
      primaryTextColor: '#F0F4F8',
      primaryBorderColor: '#00F2FE',
      lineColor: '#00F2FE',
      secondaryColor: '#121620',
      tertiaryColor: '#1a202c'
    }
  });

  // DOM Elements
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const scanBtn = document.getElementById("scanBtn");
  const runPipelineBtn = document.getElementById("runPipelineBtn");
  const repoPathInput = document.getElementById("repoPathInput");
  const liveLogs = document.getElementById("liveLogs");

  const reductionPctEl = document.getElementById("reductionPct");
  const compressionRatioEl = document.getElementById("compressionRatio");
  const savedTokensEl = document.getElementById("savedTokens");
  const mcpCallsEl = document.getElementById("mcpCalls");

  const fullRepoSkeletonText = document.getElementById("fullRepoSkeletonText");
  const wikiMarkdownText = document.getElementById("wikiMarkdownText");

  const stepExplorer = document.getElementById("stepExplorer");
  const stepDeepDive = document.getElementById("stepDeepDive");
  const stepWiki = document.getElementById("stepWiki");

  function switchTab(tabId) {
    tabBtns.forEach(b => b.classList.remove("active"));
    tabContents.forEach(c => c.classList.remove("active"));

    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if (btn) btn.classList.add("active");
    const content = document.getElementById(tabId);
    if (content) content.classList.add("active");
  }

  // Tab Navigation
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      switchTab(btn.getAttribute("data-tab"));
    });
  });

  function addLog(agent, msg, type = "info") {
    const div = document.createElement("div");
    div.className = `log-line ${type}`;
    div.textContent = `[${agent}] ${msg}`;
    liveLogs.appendChild(div);
    liveLogs.scrollTop = liveLogs.scrollHeight;
  }

  function updateKPIs(summary) {
    if (!summary) return;
    if (summary.reduction_pct !== undefined) reductionPctEl.textContent = `${summary.reduction_pct}%`;
    if (summary.compression_ratio !== undefined) compressionRatioEl.textContent = summary.compression_ratio;
    if (summary.saved_tokens !== undefined) savedTokensEl.textContent = (summary.saved_tokens || 0).toLocaleString();
    if (summary.total_files_scanned !== undefined) {
      mcpCallsEl.textContent = `${summary.total_files_scanned} files`;
    }
  }

  async function renderMermaidDiagram(diagramCode) {
    if (!diagramCode) return;
    const container = document.getElementById("mermaidContainer");
    try {
      const renderId = "mermaid_svg_" + Math.floor(Math.random() * 10000);
      const { svg } = await mermaid.render(renderId, diagramCode);
      container.innerHTML = svg;
    } catch (err) {
      console.warn("Mermaid render fallback", err);
      // Fallback pre code display if SVG rendering throws error
      container.innerHTML = `<pre class="mermaid-fallback"><code>${escapeHtml(diagramCode)}</code></pre>`;
    }
  }

  function renderMarkdownWiki(markdownText) {
    if (!markdownText) return;
    
    // Remove raw mermaid block from markdown body (rendered in SVG section above)
    let cleanText = markdownText.replace(/```mermaid[\s\S]*?```/g, '');

    let html = cleanText
      .replace(/^# (.*$)/gim, '<h1 style="color:var(--text-primary); margin-bottom:0.5rem;">$1</h1>')
      .replace(/^## (.*$)/gim, '<h2 style="color:var(--accent-cyan); margin-top:1rem; margin-bottom:0.5rem;">$1</h2>')
      .replace(/^### (.*$)/gim, '<h3 style="color:var(--text-secondary); margin-top:0.8rem;">$1</h3>')
      .replace(/^#### (.*$)/gim, '<h4 style="color:var(--accent-green); margin-top:0.6rem;">$1</h4>')
      .replace(/^- (.*$)/gim, '<li style="margin-left:1.5rem;">$1</li>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/gim, '<em>$1</em>')
      .replace(/`([^`]+)`/gim, '<code style="background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:4px;">$1</code>')
      .replace(/\n\n/gim, '<br>');

    wikiMarkdownText.innerHTML = html;
  }

  const engineModeSelect = document.getElementById("engineModeSelect");
  const apiKeyGroup = document.getElementById("apiKeyGroup");

  if (engineModeSelect && apiKeyGroup) {
    engineModeSelect.addEventListener("change", () => {
      if (engineModeSelect.value === "gemini") {
        apiKeyGroup.style.display = "block";
      } else {
        apiKeyGroup.style.display = "none";
      }
    });
  }

  async function executePipeline(path) {
    const mode = engineModeSelect ? engineModeSelect.value : "local";
    const apiKeyInput = document.getElementById("apiKeyInput");
    const apiKey = apiKeyInput ? apiKeyInput.value.trim() : "";

    addLog("Orchestrator", `Initiating 3-Agent Orchestration Pipeline [Mode: ${mode.toUpperCase()}] for target '${path}'...`, "info");
    
    stepExplorer.classList.add("active");
    stepDeepDive.classList.remove("active");
    stepWiki.classList.remove("active");

    const res = await fetch("/api/run_pipeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path, mode: mode, apiKey: apiKey })
    });
    const data = await res.json();

    if (data.logs) {
      data.logs.forEach(l => addLog(l.agent, l.message, "success"));
    }

    stepExplorer.classList.add("active");
    stepDeepDive.classList.add("active");
    stepWiki.classList.add("active");

    if (data.sample_file && data.sample_file.original) {
      const origEl = document.getElementById("originalCode");
      const skelEl = document.getElementById("skeletonCode");
      const origTitle = document.getElementById("originalCodeTitle");
      const skelTitle = document.getElementById("skeletonCodeTitle");

      if (origEl) origEl.textContent = data.sample_file.original;
      if (skelEl) skelEl.textContent = data.sample_file.skeleton;
      if (origTitle) origTitle.innerHTML = `<i class="fa-solid fa-file-lines"></i> Original Source Code (${data.sample_file.filename} - ~${data.sample_file.raw_tokens || 0} Tokens)`;
      if (skelTitle) skelTitle.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Compressed AST Skeleton (${data.sample_file.filename} - ~${data.sample_file.skeleton_tokens || 0} Tokens)`;
    }

    fullRepoSkeletonText.textContent = data.skeleton_output;
    
    renderMarkdownWiki(data.markdown_wiki);
    updateKPIs(data.metrics);

    if (data.mermaid_diagram) {
      await renderMermaidDiagram(data.mermaid_diagram);
    }

    switchTab("wikiView");
    addLog("Wiki Publisher Agent", `Pipeline finished! Generated documentation & diagram for '${data.repo_name || path}'.`, "success");
    return data;
  }

  // Scan Repository Button Handler (Scans & Executes Pipeline end-to-end)
  scanBtn.addEventListener("click", async () => {
    const path = repoPathInput.value.trim() || ".";
    scanBtn.disabled = true;
    runPipelineBtn.disabled = true;

    try {
      await executePipeline(path);
    } catch (err) {
      addLog("System", `Error executing pipeline: ${err.message}`, "info");
    } finally {
      scanBtn.disabled = false;
      runPipelineBtn.disabled = false;
    }
  });

  // Run Agent Pipeline Handler
  runPipelineBtn.addEventListener("click", async () => {
    const path = repoPathInput.value.trim() || ".";
    scanBtn.disabled = true;
    runPipelineBtn.disabled = true;

    try {
      await executePipeline(path);
    } catch (err) {
      addLog("Orchestrator", `Pipeline failure: ${err.message}`, "info");
    } finally {
      scanBtn.disabled = false;
      runPipelineBtn.disabled = false;
    }
  });

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initial Fetch of Metrics
  fetch("/api/metrics")
    .then(r => r.json())
    .then(data => updateKPIs(data))
    .catch(() => {});
});
