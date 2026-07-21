# LangFlow Agents — Comprehensive Review

> **Generated:** June 30, 2026  
> **Workspace:** `/Users/jaivirsingh/Downloads/LangFlow/`  
> **Total Agents:** 6

---

## Table of Contents

1. [Bug Triage Agent](#1-bug-triage-agent)
2. [Bug Triage AI Agent](#2-bug-triage-ai-agent)
3. [Flaky Test Case Generator](#3-flaky-test-case-generator)
4. [RCA Bot](#4-rca-bot)
5. [Test Cases Generator](#5-test-cases-generator)
6. [Test Strategy & Test Plan Creator](#6-test-strategy--test-plan-creator)
7. [Summary & Observations](#7-summary--observations)

---

## 1. Bug Triage Agent

**File:** `Bug_Triage_Agent.json`  
**Flow Description:** *"Text Generation Meets Business Transformation."*  
**Total Nodes:** 7

### Flow Diagram

```
ChatInput ──> Prompt Template (JQL) ──> APIRequest (GET Jira) ──> JiraSearchParser ──> Prompt Template (Triage Prompt) ──> MistralAI (codestral-latest) ──> ChatOutput
```

### Components

| Node | Type | Details |
|------|------|---------|
| **Chat Input** | Built-in | Receives issue keys from user |
| **Prompt Template** | Built-in | JQL URL builder: `https://jaivir.atlassian.net/rest/api/3/search/jql?jql=key%20in%20({issue_keys})` |
| **API Request** | Built-in | GET request to Atlassian Jira REST API |
| **Jira Search Parser** | Custom | Parses raw Jira JSON response into structured text |
| **Prompt Template** | Built-in | **Bug Triage Prompt** (624 chars) — instructs LLM to analyze Jira issue and produce: Severity (Blocker/Critical/Major/Minor/Trivial), Priority (P0–P4), Impact Areas, Root Cause Analysis, and Justification |
| **MistralAI** | Built-in | **Model:** `codestral-latest`, **Temperature:** 0.1 |
| **Chat Output** | Built-in | Displays triage result |

### Triage Prompt Summary

The prompt asks the LLM to act as a senior bug triage engineer and analyze a Jira issue in JSON format. It requests:
1. **SEVERITY** — Blocker, Critical, Major, Minor, Trivial
2. **PRIORITY** — P0, P1, P2, P3, P4
3. **IMPACT AREAS** — affected modules/journeys
4. **ROOT CAUSE ANALYSIS** — best hypothesis
5. **JUSTIFICATION** — reasoning for severity/priority

> ⚠️ **Note:** Uses `jaivir.atlassian.net` — different Jira instance than other agents.

---

## 2. Bug Triage AI Agent

**File:** `Bug_Triage_AI_Agent.json`  
**Total Nodes:** 9

### Flow Diagram

```
ChatInput ──> Prompt Template (JQL) ──> APIRequest (GET Jira) ──> JiraSearchParser ──> Prompt Template (Detailed Triage) ──> MistralAI (mistral-large-latest) ──> SaveToFile ──> ChatOutput
```

### Components

| Node | Type | Details |
|------|------|---------|
| **Chat Input** | Built-in | Receives issue keys from user |
| **Prompt Template** | Built-in | JQL URL builder: `https://jaivir.atlassian.net/rest/api/3/search/jql?jql=key%20in%20({issue_keys})` |
| **API Request** | Built-in | GET request to Jira REST API |
| **Jira Search Parser** | Custom | Parses Jira JSON response |
| **Prompt Template** | Built-in | **Comprehensive Triage Prompt** (2,800 chars) — full 12-section triage analysis |
| **MistralAI** | Built-in | **Model:** `mistral-large-latest`, **Temperature:** 0.1 |
| **SaveToFile** | Custom (`SaveToFileComponent`) | Writes triage output to file |
| **Chat Output** | Built-in | Displays result |

### Triage Prompt Sections (12-Step Analysis)

1. **Executive Summary** — 2–4 sentence summary
2. **Issue Classification** — Type, Functional Area, Affected Module(s), Platform
3. **Severity Assessment** — Blocker/Critical/Major/Minor/Trivial with explanation
4. **Priority Assessment** — P0–P4 with business perspective
5. **Customer Impact** — Users affected, workflows, data, revenue, security, compliance
6. **Impact Areas** — Features, Modules, APIs, Database, UI, Auth, Payments, etc.
7. **Root Cause Analysis** — Confirmed Evidence + Possible Root Causes + Confidence level
8. **Risk Assessment** — Regression, Production, Data Loss, Security, Performance risks
9. **Missing Information** — Identifies gaps (steps to reproduce, logs, screenshots, etc.)
10. **Recommended Investigation** — What developers should inspect first
11. **QA Recommendations** — Testing types needed
12. **Final Triage Decision** — Severity, Priority, Impacted Modules, Likely Root Cause, Owner Team, Confidence, Justification

> ⚠️ **Note:** Hardcoded Mistral API key detected in the flow configuration.

---

## 3. Flaky Test Case Generator

**File:** `Flaky_Test_Case_generator.json`  
**Total Nodes:** 5

### Flow Diagram

```
File (Build 1 JSON) ──┐
                       ├──> Prompt Template ──> MistralAI (codestral-latest) ──> ChatOutput
File (Build 2 JSON) ──┘
```

### Components

| Node | Type | Details |
|------|------|---------|
| **File (R-1)** | Built-in (`File`) | Upload Build 1 Playwright test results (JSON) |
| **File (R-2)** | Built-in (`File`) | Upload Build 2 Playwright test results (JSON) |
| **Prompt Template** | Built-in | **Flaky Test Analysis Prompt** (898 chars) |
| **MistralAI** | Built-in | **Model:** `codestral-latest`, **Temperature:** 0.1 |
| **Chat Output** | Built-in | Displays flaky test report |

### Flaky Test Prompt Summary

The prompt instructs the LLM to act as a senior test reliability engineer comparing two Playwright test runs (Build 1 vs Build 2). Key definitions:

- **FLAKY** — Non-deterministic result (passed in one build, failed in the other, OR passed after retry) → needs quarantine, not code fix
- **CONSISTENT FAILURE** — Failed in BOTH builds → real bug, needs a fix

Output sections:
1. **FLAKY_TESTS** — test names + one-line hypothesis of flake cause (timing, data, parallelism, network, etc.)
2. **CONSISTENT_FAILURES** — failing tests with probable root cause
3. **RERUN_RECOMMENDATION** — which to rerun vs send to engineering
4. **SUMMARY** — counts + suite health assessment

> ⚠️ **Note:** No LLM model guardrails in the system message (generic: *"You are a helpful assistant..."*).

---

## 4. RCA Bot

**File:** `RCA-Bot.json`  
**Total Nodes:** 8

### Flow Diagram

```
ChatInput ──> Prompt Template (JQL) ──> APIRequest (GET Jira) ──> JiraSearchParser ──> Prompt Template (RCA Prompt) ──> MistralAI (codestral-latest) ──> RcaExporter ──> ChatOutput
```

### Components

| Node | Type | Details |
|------|------|---------|
| **Chat Input** | Built-in | Receives Jira issue keys from user |
| **Prompt Template** | Built-in | JQL URL builder: `https://jaivir.atlassian.net/rest/api/3/search/jql?jql=key%20in%20({issue_keys})` |
| **API Request** | Built-in | GET request to Jira REST API |
| **Jira Search Parser** | Custom | Parses Jira JSON into structured format |
| **Prompt Template** | Built-in | RCA prompt template — instructs LLM to generate comprehensive RCA |
| **MistralAI** | Built-in | **Model:** `codestral-latest`, **Temperature:** 0.1 |
| **RCA Exporter** | Custom (`RcaExporterComponent`) | Formats RCA Markdown and provides download links for .md and .docx |
| **Chat Output** | Built-in | Displays the generated RCA report |

### RCA System Prompt

The LLM is instructed to act as a **Principal SRE and QA Engineer** and write a comprehensive RCA document in Markdown with the following structure:

1. **Executive Summary**
2. **Event Log & Technical Details**
3. **Root Cause Investigation (5 Whys Analysis)**
4. **Business & System Impact**
5. **Corrective and Preventive Actions (CAPA)**
6. **Automation Guardrails**

> ⚠️ **Note:** The RCA Exporter component generates base64-encoded downloadable .md and .docx files directly in the chat output.

---

## 5. Test Cases Generator

**File:** `Test Cases Generator.json`  
**Total Nodes:** 8

### Flow Diagram

```
                          ┌─────────────────────────┐
APIRequest (GET Jira) ──> │     Parser              │
                          │                         │
LocalDocumentReader ────> │  SourceSelector         │
                          │                         │
                          └─────────┬───────────────┘
                                    │
                                    v
                          Prompt Template ──> Groq (llama-3.3-70b-versatile) ──> RcaExporter ──> ChatOutput
```

### Components

| Node | Type | Details |
|------|------|---------|
| **API Request** | Built-in | GET request to Jira REST API |
| **Parser** | Custom (`ParserComponent`) | Parses API response |
| **Local Document Reader** | Custom (`LocalDocumentReaderComponent`) | Reads PDF, DOCX, TXT, MD, or JSON files locally (100% offline) |
| **Source Selector** | Custom (`SourceSelectorComponent`) | Combines Jira and document inputs |
| **Prompt Template** | Built-in | **Test Case Generation Prompt** (230 chars) |
| **Groq** | Built-in (`GroqModel`) | **Model:** `llama-3.3-70b-versatile` |
| **RCA Exporter** | Custom (`RcaExporterComponent`) | Exports generated test cases |
| **Chat Output** | Built-in | Displays test cases |

> ⚠️ **Note:** This is the only agent using **Groq** (with `llama-3.3-70b-versatile`) instead of MistralAI. It also uniquely supports **local document uploads** as a source alongside Jira.

---

## 6. Test Strategy & Test Plan Creator

**File:** `Test Strategy And Test Plan Creator.json`  
**Total Nodes:** 15 (largest flow)

### Flow Diagram

```
Path 1 (Jira Context):
ChatInput ──> Prompt Template (JQL) ──> APIRequest ──> JiraSearchParser ──┐
                                                                           ├──> Prompt Template ──> MistralAI (mistral-large-latest) ──> MultiFileWriter ──> ChatOutput
Path 2 (Local Document Context):                                          │
LocalDocumentReader ──────────────────────────────────────────────────────┘
```

### Components

| Node | Type | Details |
|------|------|---------|
| **Chat Input** | Built-in | Receives Jira IDs |
| **Prompt Template** | Built-in | JQL URL: `https://jaivir.atlassian.net/rest/api/3/search/jql?jql=key%20in%20({Jira_ID})` |
| **API Request** | Built-in | GET to Jira API |
| **Jira Search Parser** | Custom | Parses Jira JSON response |
| **Local Document Reader** | Custom (`LocalDocumentReaderComponent`) | Reads local files (PDF, DOCX, TXT, MD, JSON) |
| **Prompt Template** | Built-in | **Enterprise Test Documentation Prompt** (2,349 chars) |
| **MistralAI** (×2) | Built-in | **Model:** `mistral-large-latest`, **Temperature:** 0.1 |
| **Multi-File Writer** (×2) | Custom (`MultiFileWriterComponent`) | Parses LLM output and extracts test_plan.md and test_strategy.md files |
| **Chat Output** (×2) | Built-in | Displays status |

### Test Documentation Prompt Summary

The prompt instructs the LLM to act as a **Principal QA Automation Architect** to generate enterprise-grade test documentation. Key features:

- **Hallucination Guardrails:** Use source context ONLY, flag missing details as "Requirement Clarification Needed"
- **Two outputs** generated from a single prompt, delimited by markers:

**test_plan.md:**
1. Introduction & Objectives
2. Scope (In-Scope / Out-of-Scope)
3. Test Strategy & Approach
4. Types of Testing
5. Entry & Exit Criteria
6. Defect Management Process
7. Assumptions & Open Questions

**test_strategy.md:**
1. Testing Levels
2. Test Environment Requirements
3. Automation Strategy & Tools
4. CI/CD Integration
5. Performance & Security Testing Strategy

> ⚠️ **Note:** The Multi-File Writer writes output files to `/app/langflow/exports/` — a container-internal path that requires volume mapping for host access.

---

## 7. Summary & Observations

### Models Used

| Agent | Model | Provider |
|-------|-------|----------|
| Bug Triage Agent | `codestral-latest` | MistralAI |
| Bug Triage AI Agent | `mistral-large-latest` | MistralAI |
| Flaky Test Case Generator | `codestral-latest` | MistralAI |
| RCA Bot | `codestral-latest` | MistralAI |
| Test Cases Generator | `llama-3.3-70b-versatile` | Groq |
| Test Strategy & Test Plan Creator | `mistral-large-latest` | MistralAI |

### Common Patterns

- **Jira Integration:** All agents (except Flaky Test Case Generator) integrate with Atlassian Jira via REST API to fetch issue details
- **Custom Components:** Several agents share custom components like `JiraSearchParserComponent`, `RcaExporterComponent`, and `LocalDocumentReaderComponent`
- **Low Temperature:** All LLM agents use a temperature of 0.1 for deterministic output
- **Prompt Engineering:** All prompts enforce strict hallucination guardrails — "base conclusions only on provided context"

### Issues & Recommendations

| # | Issue | Recommendation |
|---|-------|---------------|
| 1 | **Hardcoded API keys** in MistralAI flows | Move API keys to environment variables or LangFlow secrets management |
| 2 | **Bug Triage Agent** uses `jaivir.atlassian.net` | Standardize Jira instance or document the difference |
| 3 | **Flaky Test Generator** has a generic system message ("You are a helpful assistant") | Strengthen the system message with domain-specific role and guardrails |
| 4 | **Multi-File Writer** writes to `/app/langflow/exports/` (container path) | Document required Docker volume mount or switch to a configurable output path |
| 5 | **No error handling** for missing/invalid Jira keys | Add input validation or retry logic |
| 6 | **Duplicate prompt logic** across multiple agents | Consider creating reusable prompt templates for common patterns (RCA, triage) |
| 7 | **RCA Bot & Bug Triage Agent** both use the same system message for MistralAI | Consolidate shared prompts into a utility library |
| 8 | **Test Strategy Agent** has duplicated subflows (two parallel MistralAI + MultiFileWriter chains) | Evaluate if both paths are needed or if one can be removed |
| 9 | **No authentication** details for Jira API requests | Ensure proper auth tokens/credentials are configured in API Request nodes |

### Security Notes

- API keys are embedded in plaintext within the JSON files
- Jira URLs use different domains across agents
- No encryption or masking of sensitive fields

---

*End of Review*
