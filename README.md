AI-Powered Logistics Oracle 🚚

# 📦 Smart Inventory Forecasting & Logistics Insights Engine (Backend)

An asynchronous, production-grade FastAPI backend designed to process warehouse supply chain metrics and stream real-time predictive inventory recommendations. This engine integrates with open-source Large Language Models (LLMs) via an OpenAI-compatible cloud pipeline, optimized with dynamic analytical guardrails to ensure business continuity for logistics teams.

---

## 🚀 Core Features

* **Asynchronous Token Streaming:** Utilizes Server-Sent Events (SSE) and FastAPI's `StreamingResponse` to push real-time, token-by-token advisory copy to the dashboard layout with zero buffering overhead.
* **Dual-Channel AI Guardrails:** Implements a programmatic safety-filter layer that prevents text hallucinations and enforces structural boundaries mid-generation.
* **Critical Operational Overrides:** Automatically triggers an explicit safety override if the system detects passive recommendation keywords while an item runway is sitting at a critical deficit (< 7 days of remaining stock).
* **High-Efficiency Caching Layer:** Features an in-memory execution cache abstraction layer to eliminate redundant API network roundtrips to the cloud LLM cluster for identical data signatures.

---

## 🔒 Integrated Operational Guardrails

To protect supply chain operators from erratic LLM behavior, this architecture bypasses a direct pass-through model and runs an internal security pipeline:

1. **Critical Deficit Interceptor (`llama_service.py`):** When data inputs flag an inventory depletion timeline of less than 7 days, a post-stream evaluator checks the compiled output. If the model accidentally provides passive guidance (*"wait"*, *"monitor"*, *"stable"*), the engine intercepts it and appends a bright, authoritative warning: `⚠️ [Guardrail Override]: Current depletion runway is CRITICAL. Initiate immediate stock procurement procedures.`
2. **Domain Boundary Filter (`stream.py`):** An active, chunk-by-chunk stream supervisor evaluates the text as it is generated. If prohibited tokens or topic drift indicators are caught (*crypto, pricing strategies, stock market equities, marketing*), the backend instantly severs the network line to prevent broken client-side dashboard states: `⚠️ [Stream Terminated]: Content flagged by domain boundary guardrail.`

---

## 🛠️ Tech Stack & Architecture

* **Framework:** FastAPI (Python 3.11+)
* **Asynchronous Client Engine:** HTTPX (Streaming socket configurations)
* **LLM Host Infrastructure:** Groq Cloud API Engine (Running `llama-3.2-3b-preview`)
* **Deployment Context:** Container-ready layout optimized for Render Web Service Free Tiers

---

## 📋 Environment Variables & Configuration

To move away from local hardware restrictions, this project hooks into a cloud runtime provider using an OpenAI-compliant messaging matrix. Add these keys into your local `.env` file or your Render deployment console:

| Variable Key | Deployment Target Value / Template | Purpose |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `gsk_your_live_production_token_here` | Authenticates your web cluster securely with pipelines into external LPUs |

---

## 📡 API Architecture & Endpoints

### 1. Operational Dashboard Runway Stream
Streams execution parameters regarding immediate warehouse reorder strategies and daily depletion thresholds.
* **Endpoint:** `/api/stream`
* **Method:** `GET`
* **Query Parameters:** `sku` (string), `days` (int), `stock` (int)

### 2. Strategic 2026 Distribution Insights
Streams structural recommendations incorporating complex business logic such as regional holiday modifiers (Dubai Ramadan Peaks) and marketing promo multipliers.
* **Endpoint:** `/api/stream/insights`
* **Method:** `GET`
* **Query Parameters:** `sku` (string), `ramadan_factor` (float), `promo_factor` (float), `avg_daily_sales` (float), `data_points` (int)

---

## 💻 Local Installation & Development Runbook

Follow these commands to configure and launch the system in a isolated local environment:

1. **Navigate into the backend project root:**
```bash
   cd backend
  ``` 
2. **Spin up a clean Python virtual environment:**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows terminal use: venv\Scripts\activate
```
3. **Install the required asynchronous dependencies:**
```bash
   pip install -r requirements.txt
```
4. **Boot up the server via Uvicorn with hot-reloading:**
```bash
   uvicorn stream:router --reload --port 8000
   ```

   ---

## 💻 For Projects or Collabration :-
 connect:Gmail - nethmadulasi15@gmail.com 