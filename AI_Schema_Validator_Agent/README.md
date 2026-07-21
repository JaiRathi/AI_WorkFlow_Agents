# 📋 AI3X API Contract Validator Agent

An automated **API Contract & JSON Schema Validation Agent** built in **Langflow**. It triggers live HTTP requests to API endpoints, parses JSON response payloads, compares payloads against target JSON Schema definitions (Draft-04 / Draft-07), and leverages **OpenRouter DeepSeek (`deepseek/deepseek-v4-flash`)** to generate comprehensive Pass/Fail validation reports highlighting schema compliance, missing keys, field type mismatches, and contract drift.

---

## 📐 Workflow Architecture

```
┌─────────────────────────┐
│       API Request       │
│  (Live GET HTTP Endpoint│
│   e.g. gorest.co.in)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    Parser Component     │
│  (Format Raw JSON Body) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Prompt Template     │
│ (Response + JSON Schema)│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  OpenRouter / DeepSeek  │
│ (deepseek/deepseek-v4)  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│       Chat Output       │
│  (Pass / Fail Report)   │
└─────────────────────────┘
```

---

## 🧩 Component Breakdown

| Node Name | Node Type | Component Class | Parameters & Configurations |
| :--- | :--- | :--- | :--- |
| **API Request** | `APIRequest` | Built-in | **Method:** `GET`<br>**Target URL:** `https://gorest.co.in/public/v2/users`<br>**Headers:** `User-Agent: Langflow/1.0`<br>**Timeout:** 30s |
| **Parser** | `ParserComponent` | Custom Component | Parses HTTP response stream into plain string representation |
| **Prompt Template** | `PromptTemplate` | Built-in | Combines `{input_response}` and target `{json_schema}` contract definition |
| **OpenRouter** | `OpenRouterComponent` | Custom OpenRouter Component | **Model:** `deepseek/deepseek-v4-flash`<br>**Temperature:** `0.7`<br>**System Message:** *"After validation of schema then print the pass and failed report"* |
| **Chat Output** | `ChatOutput` | Built-in | Renders formatted Pass/Fail validation report |

---

## 📊 Validation & Contract Checking Logic

The agent compares live API responses against JSON schema criteria:
- **Type Validation:** Verifies exact data types (`string`, `integer`, `boolean`, `array`, `object`).
- **Required Fields:** Checks for missing mandatory fields or unexpected `null` values.
- **Structural Integrity:** Verifies nested array items and object property hierarchies.
- **Contract Drift Alerting:** Flags added, modified, or removed fields compared to the contract standard.

### Report Output Standard
- **Status:** Overall PASS or FAIL verdict.
- **Passed Assertions:** List of fields adhering to the JSON schema.
- **Failed Assertions:** Detailed breakdown of field-level mismatches (e.g., expected `integer`, got `string`).
- **Schema Drift Summary:** Recommendations for updating API contracts or fixing backend serialization.

---

## 🚀 Getting Started

### Prerequisites
- [Langflow](https://github.com/langflow-ai/langflow) environment.
- **OpenRouter API Key** (with access to `deepseek/deepseek-v4-flash`).

### Setup & Execution
1. Open Langflow and click **Import Flow**.
2. Select [`AI3X API Contract Validator.json`](file:///Users/jaivirsingh/Downloads/AI_WorkFlow_Agents/AI_Schema_Validator_Agent/AI3X%20API%20Contract%20Validator.json).
3. Set your OpenRouter API key in the **OpenRouter** node.
4. Modify the target URL in the **API Request** node to test your microservice/API endpoint.
5. Update the target JSON schema inside the **Prompt Template** node if testing custom contracts.
6. Run the flow to generate the validation audit in chat.
