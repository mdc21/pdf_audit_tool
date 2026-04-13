# Product Requirement Document (PRD): Kompare Audit Suite

## 1. Executive Summary
**Kompare** is an institutional-grade PDF verification and forensic analytics platform designed to automate the heavy-lifting of document auditing. By leveraging a multi-threaded technical comparison engine alongside advanced agentic AI, Kompare identifies not just text changes, but structural drift, visual discrepancies, and business-level anomalies. The platform is **Cloud-Ready (v2.1.0)**, supporting seamless transitions between local-first and enterprise-cloud environments.

## 2. Target Audience & Personas
- **Compliance Officers**: Seeking a bulletproof audit trail for document releases.
- **Financial Analysts**: Requiring high-accuracy verification of complex tables and metrics.
- **Technical Managers**: Needing a scalable, multi-threaded solution for high-volume batch processing.
- **Executive Leadership**: Demanding high-stakes summaries and "narrative" reports on portfolio health.

## 3. Functionalities & Core Features

### 3.1. High-Speed Multi-Threaded Comparison
- **Textual Forensic Analysis**: Precise character-level diffing.
- **Structural Detection**: Identifying changes in table layouts and document mapping.
- **Visual Verification**: Comparing rendered pages to detect subtle formatting drift using RMS Pixel-Difference logic.

### 3.2. Hybrid Multi-Provider AI (Cloud-First Orchestration)
Kompare features a robust, multi-provider LLM engine that adapts to the deployment environment.
- **Local Autonomy**: Utilizes **Ollama (Qwen2.5/Llama-3)** for high-privacy, local-only inference.
- **Cloud Performance**: Integrates with **Groq (Llama-3.3-70b)** and **OpenAI-compatible APIs** for sub-second executive narratives and deep data-analysis threads.
- **Auto-Provider Detection**: Intelligent environment sensing to route requests to the most efficient available engine (Cloud vs Local).

### 3.3. Conversational Analyst (Talk to your Data)
A natural language interface that allows users to query their entire audit history without writing SQL or Python.
- **Self-Correcting Logic**: Automatically retries queries with corrected code if a syntax error is detected.

### 3.4. Executive Narrative Reporting
One-click generation of institutional-grade reports that synthesize raw audit failures into high-level risk assessments, powered by high-frequency Cloud LLMs.

---

## 4. Enterprise-Grade Cloud Architecture

### 4.1. Data Governance: Supabase (PostgreSQL)
Transitioned from local storage to **Supabase** for enterprise-scale durability.
- **Persistent History**: All audit scenarios, release contexts, and AI insights are persisted in a hosted PostgreSQL instance.
- **Secure Synchronization**: Relational data integrity ensures a perfect forensic record across multi-squad releases.

### 4.2. Cloud Deployment & Portability
- **Streamlit Cloud Integration**: Fully optimized for cloud deployment, utilizing native **Streamlit Secrets** for secure API and Database credential management.
- **Institutional Sample Whitelisting**: Built-in forensic sample set (26+ PDFs) for an instantaneous "Out-of-the-Box" demonstration in cloud environments.

---

## 5. UI/UX Design & Aesthetics
Kompare features a **Premium Design System** with real-time operational observability.
- **Cloud-Ready Badges**: Interactive header badges displaying live connectivity status (🟢 Cloud-Ready [Groq] vs 🟡 Local-Ollama).
- **Version Stamp**: v2.1.0 Institutional Compliance indicator.
- **Forensic UI Integration**: Side-by-side text forensics and interactive health histograms.

---

## 6. Visual Forensic Intelligence: Visualization Proof

### 🔍 Forensic Discrepancy Detail
![Forensic Discrepancy Overview](/Users/shilpadhall/.gemini/antigravity/brain/f5ba7324-c2a7-4120-95f5-23083425ed6f/media__1776024874458.png)

---

## 7. Non-Functional Requirements

| Requirement | Description |
| :--- | :--- |
| **Performance** | Multi-threaded execution; sub-second AI latency via Groq Llama-3.3. |
| **Durability** | Hosted PostgreSQL (Supabase) for permanent, cross-platform audit retention. |
| **Observability** | Real-time connectivity badges and global forensic logging `[REF-APP-XX]`. |
| **Portability** | Full compatibility with local Mac/Linux environments and Streamlit Cloud. |

---

## 8. Business Benefit & Strategic ROI

1.  **Cloud Agility**: Rapidly deployable across the enterprise without local hardware dependencies.
2.  **Risk Mitigation**: Catching "invisible" structural shifts with 99.9% accuracy.
3.  **Governance Maturity**: Secure, permanent records of institutional document evolution.
4.  **Strategic Scaling**: Supporting hundreds of concurrent squads via hosted cloud resources.
