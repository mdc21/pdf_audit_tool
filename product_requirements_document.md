# Product Requirement Document (PRD): Kompare Audit Suite

## 1. Executive Summary
**Kompare** is an institutional-grade PDF verification and forensic analytics platform designed to automate the heavy-lifting of document auditing. By leveraging a multi-threaded technical comparison engine alongside advanced agentic AI, Kompare identifies not just text changes, but structural drift, visual discrepancies, and business-level anomalies that traditional diff tools miss.

## 2. Target Audience & Personas
- **Compliance Officers**: Seeking a bulletproof audit trail for document releases.
- **Financial Analysts**: Requiring high-accuracy verification of complex tables and metrics.
- **Technical Managers**: Needing a scalable, multi-threaded solution for high-volume batch processing.
- **Executive Leadership**: Demanding high-stakes summaries and "narrative" reports on portfolio health.

## 3. Functionalities & Core Features

### 3.1. High-Speed Multi-Threaded Comparison
The "Run Audit" engine is the heart of the system, capable of processing hundreds of documents in parallel.
- **Textual Forensic Analysis**: Precise character-level diffing.
- **Structural Detection**: Identifying changes in table layouts and document mapping.
- **Visual Verification**: Comparing rendered pages to detect subtle formatting drift.

### 3.2. Asynchronous Agentic AI (Lazy-Loading)
Unlike other tools that block the user while waiting for LLM responses, Kompare uses a **Decoupled Background Worker System**.
- **Instant Audits**: Technical diffs are calculated in milliseconds.
- **Parallel Insights**: Configurable background "AI Workers" process business insights in the background.
- **Backfilling Logic**: AI insights are persisted into the database as they complete, updating the dashboard in real-time.

### 3.3. Conversational Analyst (Talk to your Data)
A natural language interface that allows users to query their entire audit history without writing SQL or Python.
- **Self-Correcting Logic**: If the AI's first attempt at a data query fails, it automatically analyzes the error and retries a corrected version.
- **Secure Sandbox**: All data analysis occurs in an isolated, pre-loaded execution environment.

### 3.4. Executive Narrative Reporting
One-click generation of institutional-grade reports that synthesize raw audit failures into high-level risk assessments.

---

## 4. Enterprise-Grade Portfolio Governance
Kompare is built for complex, multi-functional organizations where speed must be balanced with strict accountability.

### 4.1. Multi-Squad Parallel Orchestration
The system supports the concurrent operation of multiple **Squads** (e.g., Alpha, Beta, Quant) working on independent document streams and releases.
- **Isolated Team Contexts**: Each squad manages its own "Audit Packs" and "Release Contexts" to prevent data collision.
- **Unified Governance Dashboards**: Centralized oversight allowing leadership to monitor cross-squad performance and pass/fail rates in real-time.

### 4.2. Release-Cycle Hierarchy & Retention
Audits are structured within a permanent hierarchy to ensure multi-year forensic durability.
- **Hierarchy**: `Release -> Squad -> Audit Pack -> Comparison Scenario`.
- **Historical Drift Analysis**: Tagging every audit with a Release ID (e.g., April_2026) enables year-over-year regression detection.

### 4.3. Template Governance (The Golden Copy)
Institutional accuracy is maintained through **Template Management**.
- **Benchmark Auditing**: Comparisons are performed against an "Approved Institutional Template" (Golden Copy).
- **Automated Regression**: Instantly detecting if a software update has accidentally shifted the layout or logic of a critical regulatory filing.

---

## 5. UI/UX Design & Aesthetics
Kompare features a **Premium Design System** built on Streamlit with custom CSS.
- **Aesthetic**: Glassmorphic elements with vibrant blue/slate accents.
- **Responsive Layout**: Sidebar-driven configuration for parallel workers and release context.
- **Interactive Histograms**: Visual health metrics for pass rates and quality scores.

---

## 6. Visual Forensic Intelligence: Visualization Proof

### 🔍 Forensic Discrepancy Detail
The orchestration engine provides a high-resolution breakdown of discrepancies, highlighting textual shifts, structural warnings, and table layout changes in real-time.
![Forensic Discrepancy Overview](/Users/shilpadhall/.gemini/antigravity/brain/f5ba7324-c2a7-4120-95f5-23083425ed6f/media__1776024874458.png)

### 📊 Side-by-Side Text Forensics
For high-stakes document review, Kompare provides a side-by-side "Character-Correct" reconstruction, allowing auditors to see exactly what changed in the fine print (e.g., pension values, interest rates, or policy terms).
![Side-by-Side Text Diff](/Users/shilpadhall/.gemini/antigravity/brain/f5ba7324-c2a7-4120-95f5-23083425ed6f/media__1776024952857.png)

---

## 7. Agentic Decision Intelligence: Conversational Analyst

### 🤖 Talk to your Audit Data
The **Agentic AI Analyst** allows auditors to ask complex questions of their global audit history using natural language.
- **Headline Findings**: AI automatically identifies the most frequent technical failures.
- **Strategic Recommendations**: The model provides actionable advice on where to focus remediation efforts (e.g., "Prudent to conduct a detailed review of the th_doc_1 template in pack test_1").
![Conversational Analyst Insight](/Users/shilpadhall/.gemini/antigravity/brain/f5ba7324-c2a7-4120-95f5-23083425ed6f/media__1776025108718.png)

### 🛡️ Forensic AI Transparency (Chain-of-Reasoning)
Every AI-generated insight is backed by a verifiable 5-step logic path, ensuring full compliance and "Black Box" auditability.
1.  **Step 1: Data Source**: Querying the Kompare Audit History table across all releases.
2.  **Step 2: Filter**: Isolating failure records (`Status == 'FAIL'`).
3.  **Step 3: Group & Count**: Aggregating failures by Pack and Template to identify hotspots.
4.  **Step 4: Column Renaming**: Ensuring technical output is human-readable.
5.  **Step 5: Output Optimization**: Ranking and limiting the data to the most critical "Top 50" issues.
![AI Analysis Reasoning](/Users/shilpadhall/.gemini/antigravity/brain/f5ba7324-c2a7-4120-95f5-23083425ed6f/media__1776025159048.png)

---

## 8. Non-Functional Requirements

| Requirement | Description |
| :--- | :--- |
| **Performance** | Parallel multi-threaded execution; decoupled background LLM processing for 90% faster UI responsiveness. |
| **Stability** | Memory-optimized localized inference (`qwen2.5:7b`) for sub-second latency. |
| **Observability** | Global Forensic Logging with `[file:func]` metadata for every system action. |
| **Governance** | Persistent PostgreSQL backend with relational data integrity for audit preservation. |

---

## 9. Business Benefit & Strategic ROI

1.  **Enterprise Efficiency**: Automates **90% of bulk audit tasks**, reducing manual labor by thousands of hours across parallel squads.
2.  **Risk Mitigation**: Catches "invisible" structural shifts in tables that traditional text-diffs overlook, preventing multi-million dollar regulatory fines.
3.  **Governance Maturity**: Provides a permanent, searchable record of *why* every decision was made, fulfilling the most stringent institutional requirements.
4.  **Strategic Agility**: Leadership can pivot resources by identifying failing squads or templates in real-time.
