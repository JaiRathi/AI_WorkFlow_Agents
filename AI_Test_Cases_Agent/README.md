# 🧪 Test Cases Generator Agent

An automated **QA Test Case Generation Agent** built in **Langflow**. It ingests software requirements directly from **Jira REST API v3** or local specification documents via **`LocalDocumentReaderComponent`**, selects the active input stream with **`SourceSelectorComponent`**, and generates comprehensive test suites (Positive, Negative, UI Validation, Security, and Performance) using **Groq (`llama-3.3-70b-versatile`)**, exporting the formatted results via **`RcaExporterComponent`**.

---

## 📐 Workflow Architecture

```
┌───────────────────────────────────┐       ┌───────────────────────────────────┐
│            API Request            │       │      Local Document Reader        │
│       (GET Jira REST API v3)      │       │   (Local Spec / PRD / BRD File)   │
└─────────────────┬─────────────────┘       └─────────────────┬─────────────────┘
                  │                                           │
                  └────────────────────┐ ┌────────────────────┘
                                       ▼ ▼
                           ┌─────────────────────────┐
                           │     Source Selector     │
                           │(Pick active requirement)│
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │    Parser Component     │
                           │ (Format Key & Details)  │
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │     Prompt Template     │
                           │  (Senior QA Engineer)   │
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │        Groq LLM         │
                           │(llama-3.3-70b-versatile)│
                           └────────────┬────────────┘
                                        │
                   ┌────────────────────┴────────────────────┐
                   ▼                                         ▼
     ┌───────────────────────────┐             ┌───────────────────────────┐
     │    Test Cases Exporter    │             │        Chat Output        │
     │  (RcaExporterComponent)   │             │   (Display Test Cases)    │
     └───────────────────────────┘             └───────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Component Class | Parameters & Configurations |
| :--- | :--- | :--- | :--- |
| **API Request** | `APIRequest` | Built-in | **Mode:** `cURL`<br>**URL:** `https://jaivir.atlassian.net/rest/api/3/issue/{key}`<br>**Headers:** `Accept: application/json` |
| **Local Document Reader** | `LocalDocumentReaderComponent` | Custom Component | Ingests requirement specifications directly from disk |
| **Source Selector** | `SourceSelectorComponent` | Custom Component | Dynamically selects requirements stream from API or local document |
| **Parser** | `ParserComponent` | Custom Component | `mode`: `Stringify`<br>`pattern`: `Issue Key: {key}\nDescription: {description}` |
| **Prompt Template** | `PromptTemplate` | Built-in | Instructs 15+ years Senior QA persona to generate strict test scenarios |
| **Groq Model** | `GroqModel` | Built-in | **Model:** `llama-3.3-70b-versatile`<br>**Temperature:** `0.49`<br>**Base URL:** `https://api.groq.com` |
| **Test Cases (Exporter)** | `RcaExporterComponent` | Custom Component | Formats test cases into exportable structure (`Test_Cases`) |
| **Chat Output** | `ChatOutput` | Built-in | Displays generated test case list in chat window |

---

## 📋 Generated Test Suite Categories

The Groq LLM system prompt mandates multi-dimensional coverage for every requirement:
1. **Positive Functional Test Cases** — Happy-path execution flows and expected user behavior.
2. **Negative & Boundary Test Cases** — Invalid inputs, missing parameters, payload limit testing, out-of-range values.
3. **UI & UX Validation** — Layout responsiveness, field validation messages, element state checks.
4. **Security Audit Checks** — Authorization/authentication validation, payload injection checks, token expiration.
5. **Performance & SLA Checks** — Concurrent access impact, API response latency, memory leak indicators.

---

## 🚀 Getting Started

### Prerequisites
- [Langflow](https://github.com/langflow-ai/langflow) framework.
- **Groq API Key** (for `llama-3.3-70b-versatile`).
- Valid **Jira API Token** (if fetching requirement tickets directly from Jira).

### Setup & Execution
1. Open Langflow and click **Import Flow**.
2. Select [`Test Cases Generator.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_Test_Cases_Agent/Test%20Cases%20Generator.json).
3. Insert your **Groq API Key** in the `Groq` node.
4. Input a Jira ticket key (e.g. `QA-1`) in the `API Request` node, OR upload a specification file to `Local Document Reader`.
5. Run the workflow. The generated test cases will be formatted, displayed in chat, and exported via `RcaExporterComponent`.
