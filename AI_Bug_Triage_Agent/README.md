# 🐛 Bug Triage AI Agent

An autonomous QA & SRE bug triage workflow built in **Langflow**. It fetches live ticket data from the Jira REST API via JQL queries, parses issue details, conducts a comprehensive 12-step bug triage analysis using **Mistral AI (`mistral-large-latest`)**, exports the generated triage report to a local Markdown file, and outputs the result in chat.

---

## 📐 Workflow Architecture

```
                               ┌─────────────────────────┐
                               │       Chat Input        │
                               │   (Jira Issue Keys)     │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │     Prompt Template     │
                               │     (JQL URL Builder)   │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │       API Request       │
                               │   (GET Jira REST API)   │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │   Jira Search Parser    │
                               │  (Extract Issue Fields) │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │     Prompt Template     │
                               │  (12-Step Triage Prompt)│
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │        MistralAI        │
                               │ (mistral-large-latest)  │
                               └───────┬─────────┬───────┘
                                       │         │
                   ┌───────────────────┘         └───────────────────┐
                   ▼                                                 ▼
     ┌───────────────────────────┐                     ┌───────────────────────────┐
     │        Write File         │                     │        Chat Output        │
     │  (Save to Markdown File)  │                     │   (Display Triage Report) │
     └───────────────────────────┘                     └───────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Component ID / Class | Configuration & Key Parameters |
| :--- | :--- | :--- | :--- |
| **Chat Input** | `ChatInput` | Built-in | Accepts issue keys input from user (e.g. `PROJ-101`) |
| **Prompt Template (JQL)** | `PromptTemplate` | Built-in | Constructs Jira JQL search query URL format |
| **API Request** | `APIRequest` | Built-in | `GET` request to Jira REST API v3 endpoint |
| **Jira Search Parser** | `JiraSearchParserComponent` | Custom Component | Parses raw JSON response into structured summary, description, priority, and status |
| **Prompt Template (Triage)** | `PromptTemplate` | Built-in | System prompt defining 12 analysis sections (2,800 characters) |
| **MistralAI** | `MistralModel` | `langchain_mistralai` | **Model:** `mistral-large-latest`<br>**Temperature:** `0.1`<br>**Top P:** `1.0`<br>**Timeout:** `100s` |
| **Write File** | `SaveToFile` | Custom Component | Formats and exports report as `BugTriage.md` |
| **Chat Output** | `ChatOutput` | Built-in | Displays the final Markdown triage response to user |

---

## 📋 12-Step Bug Triage Analysis Framework

The triage prompt instructs the LLM to act as a Principal SRE & QA Lead, analyzing the Jira payload across 12 specific sections:

1. **Executive Summary** — 2–4 sentence high-level summary of the bug and operational impact.
2. **Issue Classification** — Type (Bug/Regression/Flaky/Data Error), Functional Area, Affected Modules, Platform.
3. **Severity Assessment** — Blocker, Critical, Major, Minor, or Trivial with technical justification.
4. **Priority Assessment** — P0, P1, P2, P3, or P4 based on business and customer impact.
5. **Customer Impact** — Affected user segments, workflows, revenue loss, data corruption, or security risks.
6. **Impact Areas** — Impacted sub-components (APIs, UI, Database, Authentication, Payments, Infrastructure).
7. **Root Cause Analysis** — Confirmed evidence, potential root cause hypotheses, and confidence level.
8. **Risk Assessment** — Secondary regression risks, production data loss, security exposure, performance degradation.
9. **Missing Information** — Gaps in bug report (missing steps to reproduce, logs, environment context, stack traces).
10. **Recommended Investigation** — First steps for software engineers (specific logs, code files, endpoints).
11. **QA Recommendations** — Test types required (Regression, API, Load, Edge-case validation).
12. **Final Triage Decision** — Actionable summary table with Severity, Priority, Owner Team, and Target SLA.

---

## 🚀 Getting Started

### Prerequisites
- [Langflow](https://github.com/langflow-ai/langflow) installed and running (`langflow run`).
- Valid **Jira API Token** and Jira user email.
- Valid **Mistral AI API Key**.

### Setup & Execution
1. Open your Langflow dashboard.
2. Click **Import Flow** and select [`Bug_Triage_AI_Agent.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_Bug_Triage_Agent/Bug_Triage_AI_Agent.json).
3. Configure credentials:
   - In the **API Request** node, update the `Authorization` Basic Header (`base64(email:api_token)`).
   - In the **MistralAI** node, input your `MISTRAL_API_KEY`.
4. Run the flow:
   - Open **Playground** / Chat interface.
   - Enter Jira Issue Key(s) (e.g. `QA-42` or `PAY-101`).
   - The agent will fetch Jira ticket data, process the 12-step triage analysis, save `BugTriage.md` locally, and display the report in the chat.
