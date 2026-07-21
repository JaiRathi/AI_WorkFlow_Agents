# ⚡ Flaky Test Case Generator Agent

An automated **Test Reliability Engineering Agent** built in **Langflow**. It compares test execution logs/JSON reports across two test suite runs (Build 1 vs Build 2), distinguishes non-deterministic flaky tests from real consistent failures, diagnoses root cause hypotheses (timing, selector race conditions, data setup, network latency), and provides actionable rerun/quarantine recommendations using **Mistral AI (`codestral-latest`)**.

---

## 📐 Workflow Architecture

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     Test Execution Result R-1   │       │     Test Execution Result R-2   │
│         (Build 1 JSON/Log)      │       │         (Build 2 JSON/Log)      │
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 │                                         │
                 └───────────────────┐ ┌───────────────────┘
                                     ▼ ▼
                         ┌─────────────────────────┐
                         │     Prompt Template     │
                         │(Reliability Analyzer)   │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │        MistralAI        │
                         │   (codestral-latest)    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │       Chat Output       │
                         │ (Flaky Analysis Report) │
                         └─────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Component ID / Class | Configuration & Key Parameters |
| :--- | :--- | :--- | :--- |
| **Test Execution Result R-1** | `File` | Custom File Component | Uploads test result log/JSON for **Build 1** |
| **Test Execution Result R-2** | `File` | Custom File Component | Uploads test result log/JSON for **Build 2** |
| **Prompt Template** | `PromptTemplate` | Built-in | Formats build outputs and enforces classification rules |
| **MistralAI** | `MistralModel` | `langchain_mistralai` | **Model:** `codestral-latest`<br>**Temperature:** `0.1`<br>**Top P:** `1.0`<br>**Timeout:** `60s` |
| **Chat Output** | `ChatOutput` | Built-in | Renders structured reliability analysis in Markdown format |

---

## 📋 Reliability Classification Logic

The agent enforces strict test reliability definitions:
- **`FLAKY` (Non-Deterministic):** Tests that passed in one build and failed in another, or passed only after a retry. These indicate timing issues, race conditions, dynamic data issues, or network instability. **Action:** Quarantine & Rerun.
- **`CONSISTENT FAILURE` (Real Bug):** Tests that failed in **both** Build 1 and Build 2. These represent deterministic bugs in application code or broken test setup. **Action:** Assign to Engineering for immediate fix.

### Report Output Sections
1. **FLAKY_TESTS** — List of flaky test names + one-line hypothesis (timing, selector, state leak, parallelism).
2. **CONSISTENT_FAILURES** — List of deterministic test failures + probable root cause.
3. **RERUN_RECOMMENDATION** — Actionable list of tests to rerun/quarantine vs tickets to open for dev team.
4. **SUMMARY** — Test counts and overall suite health summary.

---

## 🚀 Getting Started

### Prerequisites
- [Langflow](https://github.com/langflow-ai/langflow) framework installed.
- Valid **Mistral AI API Key**.
- Two Playwright / Jest / Cypress / Selenium test execution JSON result files.

### Setup & Execution
1. Open Langflow and click **Import Flow**.
2. Select [`Flaky_Test_Case_generator.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_Flaky_Test_Cases_Agent/Flaky_Test_Case_generator.json).
3. Set your Mistral API key in the **MistralAI** node (`codestral-latest`).
4. Upload **Build 1 JSON** to Node 1 (`Test Execution Result R-1`) and **Build 2 JSON** to Node 2 (`Test Execution Result R-2`).
5. Run the flow to view the generated flaky test breakdown and recommendations in the chat.
