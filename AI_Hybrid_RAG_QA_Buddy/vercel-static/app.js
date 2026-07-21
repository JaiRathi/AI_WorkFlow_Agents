document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const apiBaseInput = document.getElementById('apiBase');
  const apiStatusPill = document.getElementById('apiStatusPill');
  const apiStatusText = document.getElementById('apiStatusText');
  const llmProviderSelect = document.getElementById('llmProvider');
  const llmModelInput = document.getElementById('llmModel');
  const llmApiKeyInput = document.getElementById('llmApiKey');
  const apiKeyLabel = document.getElementById('apiKeyLabel');
  const sourceChips = document.getElementById('sourceChips');
  const topKSlider = document.getElementById('topK');
  const topKValue = document.getElementById('topKValue');
  const statsGrid = document.getElementById('statsGrid');
  const btnRefreshStats = document.getElementById('btnRefreshStats');
  
  const chatThread = document.getElementById('chatThread');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const btnSend = document.getElementById('btnSend');
  const btnNewChat = document.getElementById('btnNewChat');
  const btnQuickDemo = document.getElementById('btnQuickDemo');

  const archModal = document.getElementById('archModal');
  const btnOpenArchitecture = document.getElementById('btnOpenArchitecture');
  const btnBannerArch = document.getElementById('btnBannerArch');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCloseModalBtn = document.getElementById('btnCloseModalBtn');
  
  const btnToggleSidebar = document.getElementById('btnToggleSidebar');
  const sidebar = document.getElementById('sidebar');

  // State
  let activeSources = ['all'];
  let isApiOnline = false;

  // Initial Load from LocalStorage
  if (localStorage.getItem('qabuddy_api_base')) {
    apiBaseInput.value = localStorage.getItem('qabuddy_api_base');
  }
  if (localStorage.getItem('qabuddy_provider')) {
    llmProviderSelect.value = localStorage.getItem('qabuddy_provider');
  }
  if (localStorage.getItem('qabuddy_model')) {
    llmModelInput.value = localStorage.getItem('qabuddy_model');
  }
  if (localStorage.getItem('qabuddy_api_key')) {
    llmApiKeyInput.value = localStorage.getItem('qabuddy_api_key');
  }

  // Update Model defaults based on provider
  const providerModels = {
    openai: { model: 'gpt-4o', label: 'OpenAI API Key', placeholder: 'sk-...' },
    anthropic: { model: 'claude-3-5-sonnet-20241022', label: 'Anthropic API Key', placeholder: 'sk-ant-...' },
    grok: { model: 'grok-2', label: 'xAI API Key', placeholder: 'xai-...' },
    groq: { model: 'llama3-70b-8192', label: 'Groq API Key', placeholder: 'gsk_...' },
    mistral: { model: 'mistral-large-latest', label: 'Mistral API Key', placeholder: '...' },
    ollama: { model: 'llama3', label: 'Ollama Base URL', placeholder: 'http://localhost:11434/v1' },
  };

  function updateProviderUI() {
    const provider = llmProviderSelect.value;
    const config = providerModels[provider] || providerModels.openai;
    apiKeyLabel.textContent = config.label;
    llmApiKeyInput.placeholder = config.placeholder;
    if (!localStorage.getItem(`qabuddy_model_${provider}`)) {
      llmModelInput.value = config.model;
    } else {
      llmModelInput.value = localStorage.getItem(`qabuddy_model_${provider}`);
    }
  }

  llmProviderSelect.addEventListener('change', () => {
    updateProviderUI();
    localStorage.setItem('qabuddy_provider', llmProviderSelect.value);
  });

  llmModelInput.addEventListener('input', () => {
    localStorage.setItem(`qabuddy_model_${llmProviderSelect.value}`, llmModelInput.value);
    localStorage.setItem('qabuddy_model', llmModelInput.value);
  });

  llmApiKeyInput.addEventListener('input', () => {
    localStorage.setItem('qabuddy_api_key', llmApiKeyInput.value);
  });

  apiBaseInput.addEventListener('change', () => {
    localStorage.setItem('qabuddy_api_base', apiBaseInput.value);
    checkApiHealth();
  });

  // Source Chips Filter
  sourceChips.addEventListener('click', (e) => {
    if (!e.target.classList.contains('chip')) return;
    const src = e.target.dataset.source;
    if (src === 'all') {
      activeSources = ['all'];
      sourceChips.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      e.target.classList.add('active');
    } else {
      const allChip = sourceChips.querySelector('[data-source="all"]');
      allChip.classList.remove('active');
      if (activeSources.includes('all')) {
        activeSources = [];
      }
      
      if (activeSources.includes(src)) {
        activeSources = activeSources.filter(s => s !== src);
        e.target.classList.remove('active');
      } else {
        activeSources.push(src);
        e.target.classList.add('active');
      }

      if (activeSources.length === 0) {
        activeSources = ['all'];
        allChip.classList.add('active');
      }
    }
  });

  // Slider Top K
  topKSlider.addEventListener('input', () => {
    topKValue.textContent = topKSlider.value;
  });

  // Check Backend Health
  async function checkApiHealth() {
    const apiBase = apiBaseInput.value.trim().replace(/\/$/, '');
    try {
      const res = await fetch(`${apiBase}/health`, { method: 'GET', signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        isApiOnline = true;
        apiStatusPill.style.background = 'rgba(16, 185, 129, 0.15)';
        apiStatusPill.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        apiStatusPill.style.color = '#10b981';
        apiStatusText.textContent = 'API Connected';
        refreshStats();
        return;
      }
    } catch (err) {
      // Offline fallback
    }
    isApiOnline = false;
    apiStatusPill.style.background = 'rgba(245, 158, 11, 0.15)';
    apiStatusPill.style.borderColor = 'rgba(245, 158, 11, 0.3)';
    apiStatusPill.style.color = '#f59e0b';
    apiStatusText.textContent = 'Demo Mode (Local API Offline)';
  }

  // Refresh Stats
  async function refreshStats() {
    const apiBase = apiBaseInput.value.trim().replace(/\/$/, '');
    if (!isApiOnline) return;
    try {
      const res = await fetch(`${apiBase}/api/stats`);
      if (res.ok) {
        const data = await res.json();
        const collections = data.collections || {};
        let totalDocs = 0;
        let totalCols = 0;
        for (const [k, v] of Object.entries(collections)) {
          totalCols++;
          totalDocs += v;
        }
        statsGrid.innerHTML = `
          <div class="stat-card"><span class="stat-num">${totalCols}</span><span class="stat-lbl">Collections</span></div>
          <div class="stat-card"><span class="stat-num">${totalDocs}</span><span class="stat-lbl">Documents</span></div>
          <div class="stat-card"><span class="stat-num">768d</span><span class="stat-lbl">BGE Vector</span></div>
          <div class="stat-card"><span class="stat-num">RRF</span><span class="stat-lbl">BM25 + Dense</span></div>
        `;
      }
    } catch (e) {}
  }

  btnRefreshStats.addEventListener('click', () => {
    checkApiHealth();
  });

  // Auto-resize textarea
  chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
  });

  // Handle Suggested Query Buttons
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('query-btn')) {
      const q = e.target.dataset.query;
      chatInput.value = q;
      chatInput.dispatchEvent(new Event('input'));
      submitQuery(q);
    }
  });

  btnQuickDemo.addEventListener('click', () => {
    const demoQ = "How do I set up retry logic for flaky tests in Playwright?";
    chatInput.value = demoQ;
    chatInput.dispatchEvent(new Event('input'));
    submitQuery(demoQ);
  });

  btnNewChat.addEventListener('click', () => {
    chatThread.innerHTML = `
      <div class="welcome-card">
        <div class="welcome-icon">🛡️</div>
        <h2>New QABuddy.ai Session</h2>
        <p>Ask any QA question grounded in your 10 ingested knowledge repositories.</p>
      </div>
    `;
  });

  // Chat Submission
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;
    submitQuery(query);
  });

  async function submitQuery(query) {
    // Hide welcome card if present
    const welcome = chatThread.querySelector('.welcome-card');
    if (welcome) welcome.remove();

    // Append User Message
    appendMessage('user', query);
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Append Loading Assistant Message
    const assistantRow = appendMessage('assistant', '<div class="typing-dots"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>');
    const msgTextElement = assistantRow.querySelector('.message-text');

    const apiBase = apiBaseInput.value.trim().replace(/\/$/, '');
    const payload = {
      query: query,
      top_k: parseInt(topKSlider.value, 10),
    };
    if (!activeSources.includes('all')) {
      payload.source_filter = activeSources;
    }
    if (llmApiKeyInput.value.trim()) {
      payload.llm_provider = llmProviderSelect.value;
      payload.llm_model = llmModelInput.value;
      payload.llm_api_key = llmApiKeyInput.value.trim();
    }

    if (isApiOnline) {
      try {
        const res = await fetch(`${apiBase}/api/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const data = await res.json();
          renderResponse(msgTextElement, data.answer, data.sources);
          return;
        } else {
          const errText = await res.text();
          msgTextElement.innerHTML = `⚠️ <strong>API Error ${res.status}:</strong> ${escapeHtml(errText.substring(0, 200))}`;
          return;
        }
      } catch (err) {
        // Fallback to offline demo mode
      }
    }

    // Offline / Vercel Demo Simulation Mode
    setTimeout(() => {
      const demoData = generateMockQAResponse(query, activeSources);
      renderResponse(msgTextElement, demoData.answer, demoData.sources);
    }, 1200);
  }

  function renderResponse(container, answerMarkdown, sources) {
    let htmlContent = marked.parse(answerMarkdown || 'No response returned.');
    container.innerHTML = htmlContent;

    if (sources && sources.length > 0) {
      const sourcesBox = document.createElement('div');
      sourcesBox.className = 'sources-box';
      let sourcesHtml = `<div class="sources-header">📎 Cited Sources (${sources.length})</div>`;
      sources.forEach(src => {
        const citation = src.citation || '[Source]';
        const file = src.source_file || src.collection || 'Document';
        const snippet = src.text_snippet ? src.text_snippet.substring(0, 140) + '...' : '';
        sourcesHtml += `
          <div class="source-item">
            <span class="source-tag">${escapeHtml(citation)}</span> — <strong>${escapeHtml(file)}</strong>
            ${snippet ? `<div class="source-snippet">"${escapeHtml(snippet)}"</div>` : ''}
          </div>
        `;
      });
      sourcesBox.innerHTML = sourcesHtml;
      container.appendChild(sourcesBox);
    }

    chatThread.scrollTop = chatThread.scrollHeight;
  }

  function appendMessage(role, content) {
    const row = document.createElement('div');
    row.className = `message-row ${role}-row`;
    row.innerHTML = `
      <div class="message-avatar">${role === 'user' ? '👤' : '🛡️'}</div>
      <div class="message-body">
        <div class="message-sender">${role === 'user' ? 'You' : 'QABuddy AI'}</div>
        <div class="message-text">${content}</div>
      </div>
    `;
    chatThread.appendChild(row);
    chatThread.scrollTop = chatThread.scrollHeight;
    return row;
  }

  // Mock QA Response Generator for Vercel Static Demo Mode
  function generateMockQAResponse(query, filters) {
    const qLower = query.toLowerCase();
    
    if (qLower.includes('playwright') || qLower.includes('retry')) {
      return {
        answer: `### Playwright Test Retry & Flaky Test Handling ` + "`[1], [2]`\n\n" +
          `To configure automatic retry logic for flaky tests in Playwright, update your **\`playwright.config.ts\`** configuration file:\n\n` +
          "```typescript\nimport { defineConfig } from '@playwright/test';\n\nexport default defineConfig({\n  retries: process.env.CI ? 2 : 1, // Retry twice on CI, once locally\n  use: {\n    trace: 'on-first-retry', // Collect trace zip file on first retry\n    screenshot: 'only-on-failure',\n  },\n});\n```\n\n" +
          `#### Key Best Practices from \`02_playwright_framework\`:\n` +
          `1. **Isolate Test State:** Always use fresh page contexts between test retries.\n` +
          `2. **Soft Assertions:** Use \`expect.soft()\` for non-blocking UI validations.\n` +
          `3. **Trace Viewer Integration:** Download trace artifacts from Jenkins for failing runs.`,
        sources: [
          { citation: "[1]", source_file: "data/02_playwright_framework/playwright.config.ts", text_snippet: "export default defineConfig({ retries: process.env.CI ? 2 : 1, use: { trace: 'on-first-retry' } })" },
          { citation: "[2]", source_file: "data/05_company_docs/flaky_test_handbook.md", text_snippet: "Flaky tests must be configured with trace capture on retry to isolate timing issues." }
        ]
      };
    }

    if (qLower.includes('jenkins') || qLower.includes('log') || qLower.includes('build')) {
      return {
        answer: `### Jenkins Build #412 Log Analysis ` + "`[1]`\n\n" +
          `The failure in **Jenkins Job #412** was caused by a **\`TimeoutError\`** during step \`API_Integration_Suite\`.\n\n` +
          "```text\n[ERROR] 2026-07-21 14:22:01 - requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='api.staging.internal'): Read timed out.\n[FATAL] Test execution aborted after 30000ms.\n```\n\n" +
          `#### Root Cause & Action Items:\n` +
          `- **Primary Root Cause:** Staging payment gateway sandbox returned HTTP 504 Gateway Timeout.\n` +
          `- **Resolution:** Restart the mock payment service docker container or verify JIRA issue **QA-884**.`,
        sources: [
          { citation: "[1]", source_file: "data/10_jenkins_logs/build_412_console.log", text_snippet: "requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='api.staging.internal'): Read timed out." }
        ]
      };
    }

    if (qLower.includes('jira') || qLower.includes('qa-884') || qLower.includes('test case')) {
      return {
        answer: `### JIRA Ticket QA-884 & Test Case Coverage ` + "`[1], [2]`\n\n" +
          `**JIRA Ticket QA-884**: *"Checkout Payment Fallback Failure on Timeout"*\n\n` +
          `#### Mapped Automated & Manual Test Cases:\n` +
          `1. **\`TC_PAY_042\`** — *Verify fallback to secondary payment gateway on 504 response.* (Automated - Selenium)\n` +
          `2. **\`TC_PAY_043\`** — *User notification banner on payment gateway timeout.* (Automated - Playwright)\n` +
          `3. **\`TC_PAY_044\`** — *Idempotency token check during payment retry.* (Manual Test Suite)`,
        sources: [
          { citation: "[1]", source_file: "data/04_jira_tickets/QA-884.json", text_snippet: "Issue Summary: Checkout Payment Fallback Failure. Status: In Progress. Priority: High." },
          { citation: "[2]", source_file: "data/03_test_cases/checkout_suite.xlsx", text_snippet: "TC_PAY_042: Verify fallback to secondary payment gateway on timeout." }
        ]
      };
    }

    return {
      answer: `### QA Knowledge Retrieval Answer ` + "`[1]`\n\n" +
        `Based on your query *"_${escapeHtml(query)}_"*, QABuddy searched across the **10 knowledge repositories** (Selenium, Playwright, Test Cases, JIRA, Company Docs, PRDs, Jenkins Logs):\n\n` +
        `- **Search Retrieval Strategy:** Dense Vector Search (BGE 768d) + Sparse Vector Search (BM25) fused via RRF.\n` +
        `- **Result Grounding:** All requirements and test steps are cross-referenced with your internal specifications.\n\n` +
        `> **Note:** To connect live to your Python vector store, start your local FastAPI server (\`make dev\`) and update the **Backend API URL** in the sidebar.`,
      sources: [
        { citation: "[1]", source_file: "data/09_prd_srs_brd_frd/PRD_System_Architecture.md", text_snippet: "All automated QA assertions must provide full traceability back to PRD acceptance criteria." }
      ]
    };
  }

  // Helpers
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Modal handlers
  function openModal() {
    archModal.classList.add('active');
  }
  function closeModal() {
    archModal.classList.remove('active');
  }

  btnOpenArchitecture.addEventListener('click', openModal);
  btnBannerArch.addEventListener('click', openModal);
  btnCloseModal.addEventListener('click', closeModal);
  btnCloseModalBtn.addEventListener('click', closeModal);
  archModal.addEventListener('click', (e) => {
    if (e.target === archModal) closeModal();
  });

  // Mobile sidebar toggle
  btnToggleSidebar.addEventListener('click', () => {
    sidebar.classList.toggle('active');
  });

  // Initial Health Check
  updateProviderUI();
  checkApiHealth();
});
