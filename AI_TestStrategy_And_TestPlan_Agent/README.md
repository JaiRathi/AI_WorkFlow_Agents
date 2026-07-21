# 📄 Test Strategy & Test Plan Creator Agent

An enterprise-grade **QA Strategy & Master Test Plan Generator Agent** built in **Langflow**. It ingests project requirements either live via **Jira REST API v3 JQL searches** or through local specification documents via **`LocalDocumentReaderComponent`**. Using **Mistral AI (`mistral-large-latest`)**, it generates a comprehensive Master Test Plan and Enterprise Test Strategy with strict anti-hallucination guardrails, automatically writing the output to separate Markdown files using **`MultiFileWriterComponent`**.

---

## 📐 Workflow Architecture

```
┌───────────────────────────────────┐       ┌───────────────────────────────────┐
│            Chat Input             │       │      Local Document Reader        │
│          (Jira ID / Query)        │       │   (Local Spec / PRD / BRD File)   │
└─────────────────┬─────────────────┘       └─────────────────┬─────────────────┘
                  │                                           │
                  ▼                                           │
┌───────────────────────────────────┐                         │
│    Prompt Template (JQL Builder)  │                         │
└─────────────────┬─────────────────┘                         │
                  │                                           │
                  ▼                                           │
┌───────────────────────────────────┐                         │
│            API Request            │                         │
│       (GET Jira REST API v3)      │                         │
└─────────────────┬─────────────────┘                         │
                  │                                           │
                  ▼                                           │
┌───────────────────────────────────┐                         │
│        Jira Search Parser         │                         │
└─────────────────┬─────────────────┘                         │
                  │                                           │
                  └────────────────────┐ ┌────────────────────┘
                                       ▼ ▼
                           ┌─────────────────────────┐
                           │     Prompt Template     │
                           │(Principal Architect RAG)│
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │        MistralAI        │
                           │ (mistral-large-latest)  │
                           └────────────┬────────────┘
                                        │
                   ┌────────────────────┴────────────────────┐
                   ▼                                         ▼
     ┌───────────────────────────┐             ┌───────────────────────────┐
     │    Multi-File Writer      │             │        Chat Output        │
     │ (Master_Test_Plan.md &    │             │ (Render Strategy & Plan)  │
     │ Enterprise_Test_Strategy) │             └───────────────────────────┘
     └───────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Component Class | Parameters & Configurations |
| :--- | :--- | :--- | :--- |
| **Chat Input** | `ChatInput` | Built-in | Accepts input parameters (Jira Issue ID or manual requirements prompt) |
| **Local Document Reader** | `LocalDocumentReaderComponent` | Custom Component | Reads project specifications (PRD, SRS, BRD) directly from local file storage |
| **Prompt Template (JQL)** | `PromptTemplate` | Built-in | Formats JQL REST query endpoint: `https://jaivir.atlassian.net/rest/api/3/search/jql?jql=key%20in%20({Jira_ID})` |
| **API Request** | `APIRequest` | Built-in | Executes HTTP `GET` request to Jira REST API v3 |
| **Jira Search Parser** | `JiraSearchParserComponent` | Custom Component | Parses raw Jira JSON payload into structured summary, acceptance criteria, and details |
| **Prompt Template (Architect)** | `PromptTemplate` | Built-in | Enterprise architecture prompt (2,349 characters) with anti-hallucination rules |
| **MistralAI** | `MistralModel` | `langchain_mistralai` | **Model:** `mistral-large-latest`<br>**Temperature:** `0.1`<br>**Timeout:** 100s |
| **Multi-File Writer** | `MultiFileWriterComponent` | Custom Component | Parses output sections and writes `Master_Test_Plan.md` and `Enterprise_Test_Strategy.md` |
| **Chat Output** | `ChatOutput` | Built-in | Displays final rendered Markdown documents in chat interface |

---

## 🛡️ Anti-Hallucination Guardrails & Standards

The Principal QA Architect prompt enforces enterprise-grade constraints:
- **Strict Requirement Tracing:** Documentation is generated based **ONLY** on the provided project context.
- **Explicit Ambiguity Flags:** If a critical requirement or endpoint is missing, the agent outputs *"Requirement Clarification Needed"* rather than inventing specs.
- **Tech Stack Recommendations:** Recommends modern test automation tech stacks (e.g. Playwright + TypeScript, GitHub Actions, Docker) only when context permits, explicitly tagging default assumptions.

### Generated Document Sections
1. **Enterprise Test Strategy:** Scope, Automation Framework Architecture, Test Data Management, Environment Strategy, CI/CD Pipeline Integration, Risk Mitigation Strategy.
2. **Master Test Plan:** Objectives, In-Scope / Out-of-Scope Features, Entrance & Exit Criteria, Resource & Milestone Scheduling, Defect Management Lifecycle.

---

## 🚀 Getting Started

### Prerequisites
- [Langflow](https://github.com/langflow-ai/langflow) framework.
- **Mistral AI API Key**.
- Valid **Jira API Token** (if pulling directly from Jira REST API).

### Setup & Execution
1. Open Langflow and click **Import Flow**.
2. Select [`Test Strategy And Test Plan Creator.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_TestStrategy_And_TestPlan_Agent/Test%20Strategy%20And%20Test%20Plan%20Creator.json).
3. Configure credentials in the **MistralAI** node (`mistral-large-latest`) and **API Request** node.
4. Run the flow by providing a Jira ID (e.g., `QA-19`) or selecting a local document in **Local Document Reader**.
5. Generated files (`Master_Test_Plan.md`, `Enterprise_Test_Strategy.md`) will be written to disk and displayed in chat.
