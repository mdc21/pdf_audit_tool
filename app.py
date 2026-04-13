import streamlit as st
import os
import json
from engine import PDFAuditor, get_openai_client
from models import SessionLocal, Scenario, Release, Pack, Squad, Template, Base, engine as db_engine
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from concurrent.futures import ThreadPoolExecutor
import logging
import difflib
import pandas as pd
import numpy as np
import altair as alt
import ollama
from datetime import datetime

# Configure Logging (Force reset for metadata visibility)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='pdf_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s] - %(message)s'
)
logging.info("--- Application Started (Forensic Logging Enabled) ---")

@st.cache_resource
def get_ai_executor(max_workers):
    """Provides a persistent ThreadPool for background LLM tasks."""
    logging.info(f"Initializing/Updating AI ThreadPoolExecutor with {max_workers} workers.")
    return ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AI_Analyst")

def call_analyst_llm(messages, temperature=0.2, max_tokens=1000, model_override=None):
    """Unified LLM caller for the Analyst features."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key and hasattr(st, 'secrets') and "LLM_API_KEY" in st.secrets:
        api_key = st.secrets["LLM_API_KEY"]
        
    base_url = os.getenv("LLM_BASE_URL")
    local_model = os.getenv("LLM_MODEL", "qwen2.5:7b")
    
    try:
        if api_key:
            client = get_openai_client(api_key, base_url)
            if not client: return "Error: 'openai' missing. Run 'pip install openai' locally."
            
            cloud_model = os.getenv("LLM_CLOUD_MODEL") or (local_model if base_url and local_model != "qwen2.5:7b" else "llama-3.3-70b-versatile")
            model = model_override if model_override else cloud_model
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        else:
            response = ollama.chat(
                model=local_model,
                messages=messages,
                options={"temperature": temperature, "num_predict": max_tokens}
            )
            return response['message']['content'].strip()
    except Exception as e:
        provider = "Cloud API" if api_key else "Local Ollama"
        logging.error(f"Analyst LLM failed via {provider}: {e}")
        if not api_key:
            return "Narrative failed: Failed to connect to Ollama. Running in the Cloud? Add LLM_API_KEY to Secrets."
        return f"AI Error ({provider}): {str(e)}"

def background_ai_insight(scenario_id, diff_text, filename):
    """Isolated worker for asynchronous LLM analysis and DB persistence."""
    logging.info(f"Background AI task started for Scenario ID {scenario_id} ({filename})")
    try:
        from engine import PDFAuditor
        # Using a minimal auditor instance for the shared summarizing logic
        temp_auditor = PDFAuditor()
        insight = temp_auditor.summarize_diff_with_llm(diff_text, filename)
        
        # Fresh DB session for thread safety
        from models import SessionLocal, Scenario
        db = SessionLocal()
        try:
            scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
            if scenario:
                scenario.llm_insight = insight
                db.commit()
                logging.info(f"Background insight successfully persisted for Scenario ID {scenario_id}")
            else:
                logging.error(f"Background Error: Scenario {scenario_id} missing from DB.")
        except Exception as db_e:
            logging.error(f"Background DB Update failed for scenario {scenario_id}: {db_e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Background AI process failed for {filename}: {e}")

SETTINGS_FILE = 'settings.json'

def load_settings():
    defaults = {
        'src_dir': 'data/reference',
        'tgt_dir': 'data/newtool',
        'last_release': 'April_2026',
        'last_squad': 'alpha',
        'last_pack': 'test_1'
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
                # Merge saved with defaults to handle partial files
                defaults.update(saved)
                return defaults
        except:
            return defaults
    return defaults

def save_settings(src, tgt, release, squad, pack):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({
                'src_dir': src, 
                'tgt_dir': tgt,
                'last_release': release,
                'last_squad': squad,
                'last_pack': pack
            }, f)
    except Exception as e:
        logging.error(f"Failed to save settings: {e}")

saved_prefs = load_settings()

# Database Resilience Check
try:
    # Initialize DB tables safely
    Base.metadata.create_all(bind=db_engine)
    
    db_check = SessionLocal()
    db_check.execute(text("SELECT 1"))
    db_check.close()
    db_connected = True
    logging.info("Database connection established successfully.")
except Exception as e:
    db_connected = False
    error_msg = str(e)
    st.sidebar.error(f"⚠️ Database Offline:\n{error_msg}")
    logging.error(f"Database connection failed: {error_msg}")

if db_connected:
    pass

# Branding Assets (Institutional SVG)
LOGO_PATH = os.path.join(os.path.dirname(__file__), "brand_logo.svg")

st.set_page_config(page_title="Kompare PDF Audit", page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🛡️", layout="wide")

# Official Streamlit Logo Integration
if os.path.exists(LOGO_PATH):
    st.logo(LOGO_PATH)

# Premium CSS Injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* Font */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* Main area text */
[data-testid="stAppViewContainer"] h1 { font-size: 26px !important; font-weight: 800 !important; }
[data-testid="stAppViewContainer"] h2 { font-size: 20px !important; font-weight: 700 !important; }
[data-testid="stAppViewContainer"] h3 { font-size: 16px !important; font-weight: 600 !important; }

/* Sidebar section headers - Electric Blue on light bg */
[data-testid="stSidebar"] h3 {
    color: #4361ee !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-top: 1px solid #c7d2fe;
    padding-top: 8px !important;
    margin-top: 12px !important;
    margin-bottom: 4px !important;
}

/* Compact sidebar */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.25rem !important;
}

/* ─── Diff Comparison Table ───────────────────────────── */
.kdiff-wrap {
    max-height: 420px;
    overflow-y: auto;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    margin-bottom: 8px;
}
.kdiff table.diff {
    font-family: 'Courier New', monospace;
    font-size: 11px;
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
}
.kdiff td.diff_header, .kdiff th.diff_header {
    background: #f6f8fa;
    width: 40px !important;
    max-width: 40px !important;
    text-align: right;
    padding: 3px 6px;
    color: #57606a;
    border-right: 1px solid #d0d7de;
    font-size: 10px;
    user-select: none;
}
.kdiff td {
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    vertical-align: top;
    padding: 3px 8px;
    color: #24292f;
}
.kdiff .diff_sub { background: #ffebe9; }
.kdiff .diff_add { background: #e6ffec; }
.kdiff .diff_chg { background: #fcf09f; font-weight: bold; }

/* Active tab */
[aria-selected="true"][data-baseweb="tab"] {
    background-color: #4361ee !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}

/* Buttons */
div.stButton > button {
    background-color: #4361ee !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
div.stButton > button:hover { background-color: #3451d1 !important; }

/* Alert text */
div.stAlert p { color: #1b263b !important; }

/* Images - no horizontal scroll */
[data-testid="stImage"] img {
    max-width: 100% !important;
    height: auto !important;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

# Main Branding Header
col1, col2 = st.columns([1, 6])
with col1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
    else:
        st.title("🛡️")
with col2:
    st.title("Kompare Audit Suite")
    # Dynamic Version & Secret Badge for deployment verification
    has_api_key = "LLM_API_KEY" in os.environ or (hasattr(st, 'secrets') and "LLM_API_KEY" in st.secrets)
    badge = "🟢 Cloud-Ready" if has_api_key else "🟡 Local-Ollama"
    st.markdown(f"**{badge}** | *Institutional-Grade PDF Verification & Analytics (v2.1.0)*")

tab_audit, tab_dashboard, tab_analytics = st.tabs(["🚀 Run Audit", "📊 History Dashboard", "📈 Advanced Analytics"])

with tab_audit:
    # Sidebar Config
    threads = st.sidebar.slider("Parallel Threads (Audit)", 1, 8, 4)
    ai_threads = st.sidebar.slider("Parallel AI Workers", 1, 4, 1, help="Concurrent LLM threads for background analysis.")
    ai_executor = get_ai_executor(ai_threads)
    st.sidebar.subheader("Release Context")
    release_name = st.sidebar.text_input("Release Name", saved_prefs.get('last_release', 'April_2026'))
    release_date_input = st.sidebar.date_input("Release Date (Optional)", value=None)
    
    st.sidebar.subheader("Team Context")
    squad_name = st.sidebar.text_input("Your Squad *", saved_prefs.get('last_squad', ''))
    pack_name = st.sidebar.text_input("Audit Pack Name *", saved_prefs.get('last_pack', ''))
    
    st.sidebar.subheader("Audit Engine Settings")
    audit_mode = st.sidebar.selectbox("Audit Mode", ["Text & Tables", "Visual Layout"])
    rms_tol = 0.01
    if audit_mode == "Visual Layout":
        rms_tol = st.sidebar.slider("Visual RMS Tolerance", 0.0, 0.5, 0.01, format="%.3f", help="Threshold for pixel divergence. Lower is stricter.")

    st.sidebar.subheader("Discovery Settings")
    fuzzy_threshold = st.sidebar.slider("Fuzzy Match Sensitivity (%)", 50, 100, 85, help="Threshold for Levenshtein-style name pairing.")

    # Main UI
    src_dir = st.text_input("Source Directory (Shared Drive)", value=saved_prefs.get('src_dir', ''))
    tgt_dir = st.text_input("Target Directory (New Output)", value=saved_prefs.get('tgt_dir', ''))

    import re

    # --- Initialization ---
    auditor = PDFAuditor()

    def get_release_from_filename(filename):
        """Extracts numeric ID from filenames like 'th_doc_1.pdf' or 'much_doc_1.pdf'"""
        match = re.search(r'(\d+)', filename)
        return match.group(1) if match else None

    def get_doc_id(filename):
        """
        Extracts document identifier from filenames for pairing.
        Strips common noise-words (orig, mod, ref, test) and joins prefix with ID.
        E.g., 'payslip_orig_1.pdf' -> 'payslip_1'
        """
        # Strip common noise segments
        clean = re.sub(r'(_orig|_mod|_ref|_test|_v\d+)', '', filename, flags=re.IGNORECASE)
        # Extract prefix and numeric ID (e.g. 'payslip_1')
        match = re.search(r'([a-zA-Z_-]+)(\d+)', clean)
        if match:
            # Clean up the prefix by removing trailing separators
            prefix = match.group(1).strip('_')
            id_val = match.group(2)
            return f"{prefix}_{id_val}"
        
        # Fallback to simple number if no prefix structure found
        match = re.search(r'(\d+)', filename)
        return match.group(1) if match else None

    def process_file(src_name, tgt_name, auditor, src_dir, tgt_dir, pack_id, mode, tolerance):
        logging.info(f"Picking up file pair for comparison: {src_name} <-> {tgt_name}")
        logs = []
        src_path = os.path.join(src_dir, src_name)
        tgt_path = os.path.join(tgt_dir, tgt_name)
        
        logs.append(f"Processing Pair: {src_name} <-> {tgt_name}")

        try:
            with open(src_path, "rb") as f:
                src_bytes = f.read()
            with open(tgt_path, "rb") as f:
                tgt_bytes = f.read()
            
            engine_mode = "TEXT_TABLE" if mode == "Text & Tables" else "VISUAL"
            result = auditor.compare(src_bytes, tgt_bytes, mode=engine_mode, rms_threshold=tolerance, filename=src_name)
            logs.append(f"✅ Comparison result: {result['status']} (Score: {result['score']})")
            
            # Log to DB
            if db_connected:
                db = SessionLocal()
                try:
                    # Best-match Template by source filename
                    t_name_clean = src_name.split('.')[0]
                    template_obj = db.query(Template).filter(Template.template_name == t_name_clean).first()

                    new_scenario = Scenario(
                        name=f"{src_name} vs {tgt_name}", 
                        status=result["status"],
                        score=result["score"],
                        diff_summary=result.get("diff", ""),
                        llm_insight=None, # Will be backfilled by background worker
                        comparison_mode=engine_mode,
                        pack_id=pack_id,
                        template_id=template_obj.id if template_obj else None
                    )
                    db.add(new_scenario)
                    db.commit()
                    db.refresh(new_scenario) # Ensure we have the ID for background worker
                    
                    # --- Queue Background AI Analysis ---
                    if result["status"] in ["FAIL", "WARNING"]:
                        ai_executor.submit(
                            background_ai_insight, 
                            new_scenario.id, 
                            result.get("diff", ""), 
                            src_name
                        )
                        logs.append("🕒 AI Insight: Queued for background processing")
                    
                    logs.append("💾 Database: Insert Successful")
                except Exception as db_err:
                    logs.append(f"❌ Database Error: {str(db_err)}")
                finally:
                    db.close()
            
            logging.info(f"Comparison completed for {src_name}. Status: {result['status']}")
            return src_name, result["status"], result["score"], logs, result.get("diff", ""), result.get("html_diff", ""), result.get("visual_pairs", []), None
        except Exception as e:
            logging.error(f"Error processing pair {src_name} <-> {tgt_name}: {str(e)}")
            logs.append(f"⚠️ Error: {str(e)}")
            return src_name, f"ERROR: {str(e)}", 0.0, logs, "", "", []

    def get_analysis_code(prompt, grounding_info, error_context=None):
        """Phase 1: Generates ONLY the Pandas/Python code to extract requested data."""
        schema_info = "Columns in df_all: ID, Status, Score, Timestamp, Diff, File, Pack, Template, Squad, AI_Insight"
        squads = ", ".join(grounding_info.get('squads', []))
        packs = ", ".join(grounding_info.get('packs', []))
        templates = ", ".join(grounding_info.get('templates', []))
        
        system_prompt = f"""
        You are 'Kompare Data Engine', a specialist in writing Python/Pandas code for PDF audit analysis.
        You have a DataFrame 'df_all' with schema: {schema_info}
        
        GROUNDING (Use ONLY these real categories):
        - Squads: {squads}
        - Packs: {packs}
        - Templates: {templates}
        - Statuses: 'PASS', 'FAIL', 'WARNING'.
        
        TASK:
        Generate a Python snippet to answer the user's question.
        - IMPORTANT: Do not include 'import' statements. All libraries (pd, np, alt) are already pre-loaded.
        - The dataset is available as a DataFrame named 'df_all'.
        - Snippet MUST assign results to 'result_data' (Data/Metric) or 'result_chart' (Altair Chart).
        - Important: You can query 'AI_Insight' for qualitative questions about error descriptions.
        - Use '.empty' checks. Avoid division by 0.
        - Important: The 'Timestamp' column contains actual Python datetime objects.
        - Use .head(50) for large tables to keep results concise.
        
        OUTPUT FORMAT:
        - Output ONLY the python code block. No explanation.
        """
        
        if error_context:
            system_prompt += f"\n\nRETRY: Your previous code raised this error:\n{error_context}\nFix the issue and output corrected code only."
        
        logging.info(f"AI ANALYST (Phase 1: Code Gen) - Prompt: {prompt}")
        try:
            generated_code = call_analyst_llm(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Generate code for: {prompt}"},
                ],
                temperature=0.0 # Deterministic
            )
            logging.info(f"AI ANALYST (Phase 1: Code Gen) - Output Code:\n{generated_code}")
            return generated_code
        except Exception as e:
            logging.error(f"AI ANALYST (Phase 1: Code Gen) - Error: {e}")
            return f"Code Generation failed: {str(e)}"

    def get_analysis_narrative(prompt, results_summary, conversation_context=None):
        """Phase 2: Generates a professional business narrative based on REAL computed results."""
        
        system_prompt = """
        ROLE: You are the Chief Audit Officer for a global financial institution. 
        AUDIENCE: The Board of Directors and the CEO. 
        STRICT COMPLIANCE: You are forbidden from sounding like an AI or a computer.
        
        BOARDROOM DIRECTIVE:
        1. START with the direct answer to the user's question. No 'introductory' fluff about what you were provided.
        2. NEVER mention technical structures.
           - FORBIDDEN WORDS: JSON, Dictionary, Key, List, Code, Column, DataFrame, Output, Cluster, Dataset, Algorithm, Model.
           - FORBIDDEN PHRASES: "In the data provided", "The output contains", "According to the JSON", "This section shows".
        3. TONE: Decisive, professional, and business-focused.
        4. STRUCTURE: 
           - Headline finding (Direct Answer).
           - Supporting metrics (Bulleted).
           - Strategic recommendation or "Area of Focus".
        5. FORMATTING: Use bold text for key metrics. NO TRIPLE BACKTICKS (```).
        """
        
        context = f"""
        USER QUESTION: {prompt}
        REAL COMPUTED RESULTS:
        {results_summary}
        
        FACTUAL NARRATIVE ONLY:
        """
        
        logging.info(f"AI ANALYST (Phase 2: Narrative) - Results Summary:\n{results_summary}")
        try:
            narrative = call_analyst_llm(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': context},
                ],
                temperature=0.1
            )
            logging.info(f"AI ANALYST (Phase 2: Narrative) - Output:\n{narrative}")
            return narrative
        except Exception as e:
            logging.error(f"AI ANALYST (Phase 2: Narrative) - Error: {e}")
            return f"Narrative synth failed: {str(e)}"

    def explain_analysis_reasoning(question, code, results_summary):
        """Phase 3: Translates generated code into plain-English reasoning steps."""
        system_prompt = """You are an AI Transparency Officer. Your job is to explain EXACTLY how an analytics query was answered, step by step, so a non-technical auditor can verify the logic.

DATASET SCHEMA (this is the data the system queried):
- Table: Kompare Audit History (all PDF comparison results)
- Columns:
  • ID — unique record identifier
  • Status — audit outcome: 'PASS', 'FAIL', or 'WARNING'
  • Score — quality score from 0.0 (no match) to 1.0 (perfect match)
  • Timestamp — when the audit was performed
  • Diff — text summary of discrepancies found
  • File — filename of the audited PDF document
  • Pack — the audit batch (group of documents processed together)
  • Template — the document type / golden reference copy
  • Squad — the team responsible for the documents

FOR EACH STEP, YOU MUST EXPLAIN:
1. **What was done** — the specific action (filter, group, count, sort, calculate)
2. **Which columns** — name the exact column(s) involved
3. **What criteria** — the specific filter values or conditions applied
4. **Why** — the business reason this step was needed to answer the question

EXAMPLE — If the question was "Which packs have the most failures?" and the code filtered Status=='FAIL' then grouped by Pack:

**Step 1: Data Source**
Queried the Kompare Audit History table containing all PDF comparison results across all releases, squads, and packs.

**Step 2: Filter — Isolate Failures**
Filtered the **Status** column to include only records where Status = 'FAIL'. This narrows the dataset from all audit outcomes to only the documents that did not match their golden reference copy.

**Step 3: Group & Count — Failures by Pack**
Grouped the filtered failure records by the **Pack** column (audit batch name) and counted the number of failures in each pack. This reveals which audit batches contain the most problematic documents.

**Step 4: Rank — Top 3**
Sorted the packs by failure count in descending order and selected the top 3. This focuses attention on the highest-risk audit batches.

**Step 5: Validation**
Checked that the filtered dataset was not empty before performing the grouping. If no failures existed, an empty result would be returned rather than an error.

**Result**: The output is a ranked list of the 3 audit batches (Packs) with the highest number of failed document comparisons.

---

RULES:
- NEVER include code, variable names, function names, or technical syntax.
- ALWAYS name the specific columns and filter values used.
- Use bold for column names and key values.
- Minimum 3 steps, maximum 7 steps.
- End with a 'Result' line explaining what the output represents."""

        prompt = f"""USER QUESTION: {question}

ANALYSIS CODE THAT WAS EXECUTED:
{code}

RESULT PRODUCED:
{results_summary[:500]}

Provide detailed step-by-step reasoning:"""

        logging.info(f"AI ANALYST (Phase 3: Reasoning) - Question: {question}")
        try:
            reasoning = call_analyst_llm(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.1,
                max_tokens=600
            )
            logging.info(f"AI ANALYST (Phase 3: Reasoning) - Output:\n{reasoning}")
            return reasoning
        except Exception as e:
            logging.error(f"AI ANALYST (Phase 3: Reasoning) - Error: {e}")
            return f"Reasoning explanation unavailable: {str(e)}"

    def generate_release_report(results_df, clusters_df, release_name):
        """Generates a structured executive narrative for a release using the LLM."""
        
        # Aggregate stats
        total = len(results_df)
        passes = (results_df["Status"] == "PASS").sum()
        fails = (results_df["Status"] == "FAIL").sum()
        warnings = (results_df["Status"] == "WARNING").sum()
        avg_score = results_df["Score"].mean() * 100
        
        # Get failing files details — EXCLUDE raw diff content (contains binary/technical data that poisons the prompt)
        failing_files = results_df[results_df["Status"] == "FAIL"][["File", "Pack"]].head(15)
        failing_summary = "\n".join(
            f"        - {row['File']} (Pack: {row['Pack']})" for _, row in failing_files.iterrows()
        ) if not failing_files.empty else "        - None"
        
        # Grounding context
        packs_list = ", ".join(results_df["Pack"].unique().tolist())
        
        # Pre-format clusters into human-readable text (avoid raw dict/binary injection)
        cluster_text = "No major systemic issues detected."
        if not clusters_df.empty:
            cluster_lines = []
            for _, row in clusters_df.head(5).iterrows():
                impact = row.get("Impact", row.get("ID", "?"))
                example = row.get("Example_File", row.get("File", "unknown"))
                cluster_lines.append(f"        - Issue affecting {impact} files (e.g. {example})")
            cluster_text = "\n".join(cluster_lines)
        
        # Prompt
        system_prompt = f"""ROLE: You are the Chief Audit Officer for a global financial institution.
AUDIENCE: The Board of Directors and the CEO.
STRICT COMPLIANCE: You are forbidden from sounding like an AI or a computer.

REPORTING DIRECTIVE:
1. Write a high-stakes executive summary for the release: {release_name}.
2. NEVER mention technical data structures, binary data, code, JSON, or machine learning.
3. TONE: Decisive, professional, and insight-driven.
4. GROUNDING: Use ONLY these active audit batches (Packs): {packs_list}.

REQUIRED SECTIONS:
# Kompare Portfolio Audit: Release Executive Summary - {release_name}

## Governance & Quality Health
Summarize the overall pass rate and average quality scores. State whether institutional benchmarks are being met.

## Strategic Risk Areas
Call out specific document batches (Packs) showing significant drift. Reference REAL file names from the failure list.

## Root Cause Analysis & Recommended Actions
Provide business-level explanations for the failures and clear next steps for remediation."""
        
        snapshot = f"""RELEASE DATA SNAPSHOT:
- Total Files Audited: {total}
- Pass Rate: {(passes/max(total,1))*100:.1f}%
- Average Score: {avg_score:.1f}%
- Failures: {fails}
- Warnings: {warnings}

FAILING DOCUMENTS:
{failing_summary}

SYSTEMIC ISSUES:
{cluster_text}"""
        
        logging.info(f"REPORT GENERATOR - Release Snapshot Context:\n{snapshot}")
        try:
            report = call_analyst_llm(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': snapshot},
                ],
                temperature=0.3,
                max_tokens=1500
            )
            logging.info(f"REPORT GENERATOR - Final Report Character Count: {len(report)}")
            return report
        except Exception as e:
            logging.error(f"REPORT GENERATOR - Error: {e}")
            return f"Report Generation failed: {str(e)}"

    def discover_pairs_and_orphans(src_dir, tgt_dir, threshold):
        src_files = sorted([f for f in os.listdir(src_dir) if f.endswith('.pdf')])
        tgt_files = sorted([f for f in os.listdir(tgt_dir) if f.endswith('.pdf')])
        
        pairs = []
        matched_src = set()
        matched_tgt = set()
        
        # 1. Exact Match
        for s in src_files:
            if s in tgt_files:
                pairs.append((s, s))
                matched_src.add(s)
                matched_tgt.add(s)
                
        # 2. Context-Aware ID Match (Noise-word stripped Prefix + ID)
        remaining_src = [s for s in src_files if s not in matched_src]
        remaining_tgt = [t for t in tgt_files if t not in matched_tgt]
        
        for s in remaining_src:
            s_id = get_doc_id(s)
            if not s_id: continue
            for t in remaining_tgt:
                if t in matched_tgt: continue
                if get_doc_id(t) == s_id:
                    pairs.append((s, t))
                    matched_src.add(s)
                    matched_tgt.add(t)
                    break
                    
        # 3. Numeric Fallback (Legacy support for th_doc_1 -> much_doc_1)
        remaining_src = [s for s in src_files if s not in matched_src]
        remaining_tgt = [t for t in tgt_files if t not in matched_tgt]
        
        for s in remaining_src:
            match = re.search(r'(\d+)', s)
            if not match: continue
            sid = match.group(1)
            for t in remaining_tgt:
                if t in matched_tgt: continue
                tmatch = re.search(r'(\d+)', t)
                if tmatch and tmatch.group(1) == sid:
                    pairs.append((s, t))
                    matched_src.add(s)
                    matched_tgt.add(t)
                    break

        # 4. Fuzzy Match (Remaining orphans with high similarity)
        remaining_src = [s for s in src_files if s not in matched_src]
        remaining_tgt = [t for t in tgt_files if t not in matched_tgt]
        
        for s in remaining_src:
            best_match = None
            highest_ratio = 0
            for t in remaining_tgt:
                if t in matched_tgt: continue
                ratio = difflib.SequenceMatcher(None, s, t).ratio()
                if ratio > highest_ratio:
                    highest_ratio = ratio
                    best_match = t
            
            if highest_ratio >= (threshold / 100.0):
                pairs.append((s, best_match))
                matched_src.add(s)
                matched_tgt.add(best_match)
                
        # 4. Orphans
        orphan_src = [s for s in src_files if s not in matched_src]
        orphan_tgt = [t for t in tgt_files if t not in matched_tgt]
        
        return pairs, orphan_src, orphan_tgt

    if st.button("Start Bulk Comparison"):
        if not src_dir or not tgt_dir:
            st.error("Please provide both Source and Target directories.")
        elif not squad_name or not pack_name:
            st.error("Please provide both Squad Name and Audit Pack Name.")
        elif not os.path.isdir(src_dir) or not os.path.isdir(tgt_dir):
            st.error("One or both directories do not exist.")
        else:
            # Save settings for next run
            save_settings(src_dir, tgt_dir, release_name, squad_name, pack_name)
            
            pairs, orphan_src, orphan_tgt = discover_pairs_and_orphans(src_dir, tgt_dir, fuzzy_threshold)
            
            if not pairs and not orphan_src and not orphan_tgt:
                st.warning("No PDF files found to process.")
            else:
                # auditor is now initialized at top level
                
                # Setup Release, Squad, and Pack in DB
                pack_id = None
                if db_connected:
                    db = SessionLocal()
                    # 1. Ensure Release exists
                    release = db.query(Release).filter(Release.name == release_name).first()
                    if not release:
                        release = Release(name=release_name, release_date=release_date_input)
                        db.add(release)
                        db.commit()
                        db.refresh(release)
                    
                    # 2. Ensure Squad exists
                    squad = db.query(Squad).filter(Squad.name == squad_name).first()
                    if not squad:
                        squad = Squad(name=squad_name)
                        db.add(squad)
                        db.commit()
                        db.refresh(squad)

                    # 3. Ensure Pack exists (scoped to Release and Squad)
                    pack = db.query(Pack).filter(
                        Pack.name == pack_name, 
                        Pack.release_id == release.id,
                        Pack.squad_id == squad.id
                    ).first()
                    if not pack:
                        pack = Pack(name=pack_name, release_id=release.id, squad_id=squad.id)
                        db.add(pack)
                        db.commit()
                        db.refresh(pack)
                    pack_id = pack.id
                    db.close()

                st.write(f"🚀 Found **{len(pairs)}** pairs and **{len(orphan_src) + len(orphan_tgt)}** orphans.")
                progress_bar = st.progress(0)
                results = []
                all_logs = []

                # Handle Orphans First (Fast)
                for os_name in orphan_src:
                    logs = [f"ORPHAN_SOURCE: {os_name} found only in source directory."]
                    results.append({"File": os_name, "Status": "ORPHAN_SOURCE", "Score": 0.0, "Diff": "File missing in target.", "VisualDiff": ""})
                    if db_connected:
                        db = SessionLocal()
                        try:
                            # Log orphan source to DB
                            db.add(Scenario(name=os_name, status="ORPHAN_SOURCE", score=0.0, diff_summary="File missing in target", pack_id=pack_id))
                            db.commit()
                        finally: db.close()

                for ot_name in orphan_tgt:
                    logs = [f"ORPHAN_TARGET: {ot_name} found only in target directory."]
                    results.append({"File": ot_name, "Status": "ORPHAN_TARGET", "Score": 0.0, "Diff": "Extra file in target.", "VisualDiff": ""})
                    if db_connected:
                        db = SessionLocal()
                        try:
                            # Log orphan target to DB
                            db.add(Scenario(name=ot_name, status="ORPHAN_TARGET", score=0.0, diff_summary="Extra file in target", pack_id=pack_id))
                            db.commit()
                        finally: db.close()

                # Handle Pairs (Parallel)
                if pairs:
                    with ThreadPoolExecutor(max_workers=threads) as executor:
                        futures = [executor.submit(process_file, p[0], p[1], auditor, src_dir, tgt_dir, pack_id, audit_mode, rms_tol) for p in pairs]
                        for i, future in enumerate(futures):
                            filename, status, score, logs, diff, html_diff, visual_pairs, insight = future.result()
                            results.append({"File": filename, "Status": status, "Score": score, "Diff": diff, "VisualDiff": html_diff, "VisualPairs": visual_pairs, "Insight": insight})
                            all_logs.extend(logs)
                            progress_bar.progress((i + 1) / len(pairs))

                st.success("Comparison Complete!")
                
                # Display results summary table (RESTORATION)
                st.subheader("📋 Audit Execution Summary")
                summary_df = pd.DataFrame([{"File": r["File"], "Status": r["Status"], "Score": f"{r['Score']*100:.2f}%"} for r in results])
                st.dataframe(summary_df, width='stretch')
                failures = [r for r in results if r["Status"] == "FAIL"]
                if failures:
                    st.subheader("⚠️ Discrepancy Details")
                    for f in failures:
                        with st.expander(f"Identify Differences: {f['File']}", expanded=True):
                            if f["VisualDiff"]:
                                # st.html renders arbitrary HTML inline - no sanitization,
                                # no fixed-height iframe, auto-sizes to content
                                st.html(f["VisualDiff"])
                            
                            if f["Status"] in ["FAIL", "WARNING"]:
                                st.info("🕒 **AI Business Insight**: Processing in background (see Dashboard for updates).")
                            if f.get("VisualPairs"):
                                st.subheader("🖼️ Layout Discrepancies (Top Divergent Pages)")
                                for pair in f["VisualPairs"]:
                                    st.write(f"**Page {pair['page']}** (RMS Variance: {pair['rms']:.5f})")
                                    col1, col2 = st.columns(2)
                                    col1.image(f"data:image/png;base64,{pair['src']}", caption="Source (Reference)", width="stretch")
                                    col2.image(f"data:image/png;base64,{pair['tgt']}", caption="Target (New)", width="stretch")
                                st.write("---")
                            
                            st.markdown("**Raw Text Summary (Saved to DB)**")
                            st.code(f["Diff"])
                
                # Display raw debug logs
                with st.expander("🔍 View Detailed Debug Logs"):
                    for log in all_logs:
                        st.write(log)

with tab_dashboard:
    st.header("🕵️ Audit History Dashboard")
    if db_connected:
        db = SessionLocal()
        try:
            # 1. Filters at the top
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            releases = [r[0] for r in db.query(Release.name).distinct().all()]
            squads = [s[0] for s in db.query(Squad.name).distinct().all()]
            
            sel_release = f_col1.selectbox("Filter by Release", ["All"] + releases)
            sel_squad = f_col2.selectbox("Filter by Squad", ["All"] + squads)
            
            from datetime import timedelta, date
            date_from = f_col3.date_input("From", date.today() - timedelta(days=30))
            date_to = f_col4.date_input("To", date.today())

            # 2. Query with Joins and Eager Loading
            query = db.query(Scenario).options(
                joinedload(Scenario.template),
                joinedload(Scenario.pack).joinedload(Pack.squad),
                joinedload(Scenario.pack).joinedload(Pack.release)
            ).join(Pack).join(Release).join(Squad)
            if sel_release != "All": query = query.filter(Release.name == sel_release)
            if sel_squad != "All": query = query.filter(Squad.name == sel_squad)
            
            # Application of Date Filter
            query = query.filter(Scenario.created_at >= date_from, Scenario.created_at <= date_to + timedelta(days=1))
                
            scenarios = query.order_by(Scenario.created_at.desc()).limit(200).all()

            if scenarios:
                df = pd.DataFrame([{
                    "ID": s.id,
                    "Mode": s.comparison_mode,
                    "Release": s.pack.release.name,
                    "Squad": s.pack.squad.name,
                    "Pack": s.pack.name,
                    "Scenario": s.name,
                    "Status": s.status,
                    "Score": s.score,
                    "Timestamp": s.created_at,
                    "AI_Insight": s.llm_insight
                } for s in scenarios])
                
                # Metrics
                pass_rate = len(df[df["Status"] == "PASS"]) / len(df) * 100
                col1, col2 = st.columns(2)
                col1.metric("Pass Rate", f"{pass_rate:.1f}%")
                col2.metric("Fails", len(df[df["Status"] == "FAIL"]))
                
                st.subheader(f"Results View: {sel_release} | Team: {sel_squad}")
                st.caption("💡 Click any row to view its discrepancy details below.")

                # Interactive row selection — click a row to inspect it
                event = st.dataframe(
                    df,
                    on_select="rerun",
                    selection_mode="single-row",
                    width='stretch',
                    key="history_table"
                )

                # ── On-demand Discrepancy Viewer ───────────────────────
                selected_rows = event.selection.rows if event else []
                fail_scenarios = [s for s in scenarios if s.status == "FAIL"]

                if selected_rows:
                    idx = selected_rows[0]
                    sel = scenarios[idx]
                    st.divider()
                    status_badge = "🔴 FAIL" if sel.status == "FAIL" else "🟢 PASS"
                    st.markdown(
                        f"**{status_badge} &nbsp; `{sel.name}`** &nbsp;|&nbsp; "
                        f"Pack: **{sel.pack.name}** &nbsp;|&nbsp; "
                        f"Release: **{sel.pack.release.name}** &nbsp;|&nbsp; "
                        f"Score: **{sel.score*100:.1f}%** &nbsp;|&nbsp; "
                        f"Mode: {sel.comparison_mode} &nbsp;|&nbsp; "
                        f"Audited: {sel.created_at.strftime('%d %b %Y %H:%M')}",
                        unsafe_allow_html=True
                    )
                    if sel.status == "FAIL":
                        # Async/On-Demand AI Insight Generation
                        if not sel.llm_insight:
                            with st.spinner("🤖 AI Analyst is generating forensic insight..."):
                                try:
                                    # Trigger the LLM call that was removed from the synchronous path
                                    new_insight = auditor.summarize_diff_with_llm(sel.diff_summary, sel.name)
                                    
                                    # Update Database with the new insight for persistence
                                    sel.llm_insight = new_insight
                                    db.commit()
                                    st.success(f"🤖 **AI Business Insight (Generated)**\n\n{new_insight}")
                                except Exception as llm_err:
                                    st.error(f"AI Insight generation failed: {llm_err}")
                        else:
                            st.success(f"🤖 **AI Business Insight**\n\n{sel.llm_insight}")
                        
                        if sel.diff_summary:
                            st.markdown("**Technical Diff Summary**")
                            st.code(sel.diff_summary, language=None)
                        else:
                            st.info("No technical diff summary stored.")
                    else:
                        st.success("This scenario passed — no discrepancies recorded.")
                elif fail_scenarios:
                    st.info(f"ℹ️ {len(fail_scenarios)} failure{'s' if len(fail_scenarios) != 1 else ''} in this view — click a row to inspect its diff.")
                else:
                    st.success("✅ All scenarios in the selected range passed.")

                # ── Trend Chart ───────────────────────────────────────
                st.subheader("Performance Trend (Daily Volume)")
                df["Date"] = pd.to_datetime(df["Timestamp"]).dt.date
                trend_data = df.groupby("Date").count()["ID"]
                
                # Fill missing dates in the selected range to show 0s
                idx = pd.date_range(date_from, date_to)
                trend_data.index = pd.DatetimeIndex(trend_data.index)
                trend_data = trend_data.reindex(idx, fill_value=0)
                
                if len(df["Date"].unique()) <= 1:
                    st.bar_chart(trend_data)
                else:
                    st.area_chart(trend_data)
            else:
                st.info("No matching records found for the selected filters.")
        finally:
            db.close()
    else:
        st.warning("History Dashboard unavailable (Database Offline).")

with tab_analytics:
    st.header("📈 Advanced Failure Analytics")
    if db_connected:
        db = SessionLocal()
        try:
            # ── Talk to your Data (LLM Analyst) ────────────────────────
            with st.expander("💬 🤖 Talk to your Audit Data (Conversational Analyst)", expanded=True):
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []

                # Display history
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
                        if "data" in msg:
                            if isinstance(msg["data"], pd.DataFrame):
                                st.dataframe(msg["data"], width='stretch')
                            elif isinstance(msg["data"], (int, float, str)):
                                st.metric("Result", msg["data"])
                        if "chart" in msg:
                            st.altair_chart(msg["chart"], width='stretch')

                # Query Input
                if user_input := st.chat_input("Ask about your audit history (e.g. 'Show top 3 failing packs this week')"):
                    # Add user message
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    with st.chat_message("user"):
                        st.write(user_input)

                    with st.chat_message("assistant"):
                        with st.spinner("AI Analyst is crunching numbers..."):
                            # Get all data for analysis scope
                            # (query from dashboard context is already applied to 'scenarios' list)
                            df_analytics = pd.DataFrame([{
                                "ID": s.id, "Status": s.status, "Score": s.score,
                                "Timestamp": s.created_at, "Diff": s.diff_summary,
                                "File": s.name, "Pack": s.pack.name,
                                "Template": s.template.template_name if s.template else "Fuzzy Match Required",
                                "Squad": s.pack.squad.name if s.pack and s.pack.squad else "Unknown",
                                "AI_Insight": s.llm_insight
                            } for s in scenarios])

                            # Phase 1: Get AI Code with Grounding
                            grounding = {
                                "squads": df_analytics["Squad"].unique().tolist(),
                                "packs": df_analytics["Pack"].unique().tolist(),
                                "templates": df_analytics["Template"].unique().tolist(),
                                "date_range": f"{date_from} to {date_to}"
                            }
                            try:
                                grounding["squads"] = list(set([s.pack.squad.name for s in scenarios if s.pack and s.pack.squad]))
                            except: pass

                            # ── Agentic Self-Correcting Loop ──────────────────
                            BLOCKED_PATTERNS = ['import os', 'import sys', 'import subprocess',
                                                'open(', '__import__', 'eval(', 'compile(']
                            SAFE_BUILTINS = {
                                "len": len, "range": range, "str": str, "int": int,
                                "float": float, "bool": bool, "list": list, "dict": dict,
                                "tuple": tuple, "set": set, "max": max, "min": min,
                                "sum": sum, "abs": abs, "round": round, "sorted": sorted,
                                "enumerate": enumerate, "zip": zip, "map": map,
                                "filter": filter, "isinstance": isinstance, "type": type,
                                "print": print, "True": True, "False": False, "None": None,
                            }
                            MAX_RETRIES = 3
                            res_data, res_chart = None, None
                            code = ""
                            error_context = None

                            for attempt in range(MAX_RETRIES):
                                response_code_raw = get_analysis_code(user_input, grounding, error_context)

                                # Parse code block
                                code_match = re.search(r"```python\n(.*?)\n```", response_code_raw, re.DOTALL)
                                if not code_match:
                                    code_match = re.search(r"```\n(.*?)\n```", response_code_raw, re.DOTALL)
                                if not code_match:
                                    cleaned = response_code_raw.strip()
                                    if cleaned and not cleaned.startswith("Code Generation failed"):
                                        code = cleaned
                                    else:
                                        error_context = "No valid Python code block was generated. Wrap output in ```python ... ```."
                                        continue
                                else:
                                    code = code_match.group(1)

                                # Security pre-scan
                                if any(p in code for p in BLOCKED_PATTERNS):
                                    st.error("⛔ Security: blocked dangerous operation in generated code.")
                                    break

                                try:
                                    local_vars = {"pd": pd, "np": np, "alt": alt, "df_all": df_analytics}
                                    exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
                                    res_data = local_vars.get("result_data")
                                    res_chart = local_vars.get("result_chart")
                                    if attempt > 0:
                                        st.caption(f"✅ Self-corrected on attempt {attempt + 1}")
                                    break  # Success — exit retry loop
                                except Exception as exec_e:
                                    error_context = f"{type(exec_e).__name__}: {str(exec_e)}"
                                    if attempt == MAX_RETRIES - 1:
                                        st.error(f"Analysis failed after {MAX_RETRIES} attempts: {str(exec_e)}")
                                        with st.expander("🛠️ Debug: Final Attempt", expanded=True):
                                            st.code(code, language="python")

                            # Phase 2: Factual Narrative from computed results
                            results_summary = "No matching audit records were found for this query."
                            if res_data is not None:
                                if isinstance(res_data, pd.DataFrame):
                                    results_summary = res_data.head(20).to_string()
                                    if len(res_data) > 20:
                                        results_summary += f"\n... (Total Rows: {len(res_data)})"
                                else:
                                    results_summary = str(res_data)

                            # Structured conversation context
                            conversation_context = None
                            if len(st.session_state.chat_history) > 1:
                                recent_qs = [m["content"] for m in st.session_state.chat_history[-4:] if m["role"] == "user"]
                                if recent_qs:
                                    conversation_context = "Recent questions:\n" + "\n".join(f"- {q}" for q in recent_qs)

                            explanation_raw = get_analysis_narrative(user_input, results_summary, conversation_context)

                            # Safety: Strip any code blocks the LLM might have included
                            explanation = re.sub(r"```python.*?```", "", explanation_raw, flags=re.DOTALL).strip()
                            explanation = re.sub(r"```.*?```", "", explanation, flags=re.DOTALL).strip()

                            # --- UI Rendering ---
                            # Display Narrative Primary
                            st.write(explanation)
                            
                            if res_data is not None:
                                if isinstance(res_data, pd.DataFrame):
                                    st.dataframe(res_data, width='stretch')
                                elif isinstance(res_data, (int, float)):
                                    st.metric("Result", res_data)
                                elif isinstance(res_data, str):
                                    if len(res_data) < 20: st.metric("Result", res_data)
                                    else: st.info(res_data)
                            
                            if res_chart is not None:
                                st.altair_chart(res_chart, width='stretch')
                            
                            # Phase 3: Generate reasoning trace (compute BEFORE expander to avoid rendering issues)
                            reasoning = ""
                            if code:
                                try:
                                    reasoning = explain_analysis_reasoning(user_input, code, results_summary)
                                    if not reasoning or reasoning.isspace():
                                        reasoning = "_Reasoning trace could not be generated for this query._"
                                except Exception as reason_e:
                                    logging.error(f"Reasoning generation failed: {reason_e}")
                                    reasoning = f"_Reasoning unavailable: {str(reason_e)}_"

                            # Display reasoning in expander
                            if code:
                                with st.expander("🔍 View Analysis Reasoning", expanded=False):
                                    st.markdown(reasoning)
                                    with st.expander("🛠️ Raw Code (Debug)", expanded=False):
                                        st.code(code, language="python")
                            
                            # Save to history
                            msg_entry = {"role": "assistant", "content": explanation}
                            if res_data is not None: msg_entry["data"] = res_data
                            if res_chart is not None: msg_entry["chart"] = res_chart
                            st.session_state.chat_history.append(msg_entry)

            st.divider()
            
            # Re-use filters from dashboard for consistency
            query = db.query(Scenario).join(Pack).join(Release).join(Squad)
            if sel_release != "All": query = query.filter(Release.name == sel_release)
            if sel_squad != "All": query = query.filter(Squad.name == sel_squad)
            query = query.filter(Scenario.created_at >= date_from, Scenario.created_at <= date_to + timedelta(days=1))
            
            scenarios = query.all()
            if scenarios:
                df_all = pd.DataFrame([{
                    "ID": s.id,
                    "Status": s.status,
                    "Score": s.score,
                    "Timestamp": s.created_at,
                    "Diff": s.diff_summary,
                    "File": s.name,
                    "Pack": s.pack.name,
                    "AI_Insight": s.llm_insight
                } for s in scenarios])
                
                # Dynamic Toggle for Granularity
                col_t1, col_t2 = st.columns([2, 2])
                analysis_lvl = col_t1.radio("View Analytics Level", ["Pack", "Template"], horizontal=True, help="Shift analytics between high-level Packs or individual Document Templates.")
                group_col = "Pack" if analysis_lvl == "Pack" else "File"
                
                # 1. Failure Clustering (Usability Requirement)
                st.subheader("🧩 Failure Clustering (Top Unique Issues)")
                failures = df_all[df_all["Status"].isin(["FAIL", "WARNING"])]
                if not failures.empty:
                    # Group by the first 200 chars of diff to cluster similar issues
                    failures["Issue_Signature"] = failures["Diff"].str[:200]
                    clusters = failures.groupby("Issue_Signature").agg({
                        "ID": "count",
                        "File": "first",
                        "Score": "mean"
                    }).rename(columns={"ID": "Impact (Files)", "File": "Example File", "Score": "Avg Severity"}).sort_values("Impact (Files)", ascending=False).head(10)
                    
                    st.write("Identified issues affecting multiple files. Fix these to clear large volumes of failures.")
                    st.dataframe(clusters, width='stretch')
                
                # 2. Dual-Axis Volume vs Quality
                st.subheader("📊 Quality vs. Volume Trend")
                df_all["Date"] = pd.to_datetime(df_all["Timestamp"]).dt.date
                trend = df_all.groupby("Date").agg({
                    "ID": "count",
                    "Status": lambda x: (x == "PASS").mean() * 100
                }).rename(columns={"ID": "Volume", "Status": "Pass Rate %"})
                
                # Fill gaps
                idx = pd.date_range(date_from, date_to)
                trend.index = pd.DatetimeIndex(trend.index)
                trend = trend.reindex(idx, fill_value=0)
                
                import altair as alt
                trend_reset = trend.reset_index().rename(columns={"index": "Date"})
                
                # Create True Dual-Axis Chart
                base = alt.Chart(trend_reset).encode(
                    x=alt.X('Date:T', title='Execution Date')
                )
                
                # Volume - Bars (Left Axis)
                bar = base.mark_bar(opacity=0.4, color='#5276A7').encode(
                    y=alt.Y('Volume:Q', title='Audit Volume (Qty)')
                )
                
                # Pass Rate - Line (Right Axis)
                line = base.mark_line(strokeWidth=3, color='#F35B5B').encode(
                    y=alt.Y('Pass Rate %:Q', title='Pass Rate (%)', scale=alt.Scale(domain=[0, 100]))
                )
                
                # Combined Chart
                dual_axis_chart = alt.layer(bar, line).resolve_scale(
                    y='independent'
                ).properties(height=350)
                
                st.altair_chart(dual_axis_chart, width='stretch')
                
                # 3. Pareto Impact Analysis
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.subheader(f"📉 Pareto: Volume Impact ({analysis_lvl})")
                    fail_vol = failures.groupby(group_col).count()["ID"].sort_values(ascending=False).head(10)
                    st.bar_chart(fail_vol)
                
                with col_p2:
                    st.subheader(f"🔥 Pareto: Severity Impact ({analysis_lvl})")
                    # Lowest score = highest severity impact
                    fail_sev = failures.groupby(group_col)["Score"].mean().sort_values(ascending=True).head(10)
                    st.bar_chart(fail_sev)
                
                # 4. Detailed Audit Breakdown Table (Requirement)
                st.subheader(f"📋 Detailed Audit Breakdown (By {analysis_lvl})")
                breakdown = df_all.groupby(group_col).agg(
                    Total_Executed=('ID', 'count'),
                    Passes=('Status', lambda x: (x == 'PASS').sum()),
                    Fails=('Status', lambda x: (x == 'FAIL').sum()),
                    Pass_Rate=('Status', lambda x: f"{(x == 'PASS').mean()*100:.1f}%"),
                    Avg_Score=('Score', lambda x: f"{x.mean()*100:.1f}%")
                ).sort_values("Total_Executed", ascending=False)
                
                st.dataframe(breakdown, width='stretch')
                
                # 5. Automated Release Narrative Report (Phase 3)
                st.write("---")
                st.subheader("📄 One-Click Executive Reporting")
                st.write("Generate a comprehensive, branded PDF/Markdown summary narrative for this release selection.")
                
                if st.button("Generate Executive Narrative Report", type="primary"):
                    with st.spinner(f"Synthesizing report for {sel_release}..."):
                        # Prepare data for report
                        df_report = pd.DataFrame([{
                            "ID": s.id, "Status": s.status, "Score": s.score,
                            "Timestamp": s.created_at, "Diff": s.diff_summary,
                            "File": s.name, "Pack": s.pack.name,
                            "AI_Insight": s.llm_insight
                        } for s in scenarios])
                        
                        # Use existing clusters logic
                        df_fails = df_report[df_report["Status"].isin(["FAIL", "WARNING"])]
                        df_clusters = pd.DataFrame()
                        if not df_fails.empty:
                            df_fails["Issue_Signature"] = df_fails["Diff"].str[:200]
                            df_clusters = df_fails.groupby("Issue_Signature").agg({
                                "ID": "count", "File": "first", "Score": "mean"
                            }).rename(columns={"ID": "Impact", "File": "Example_File"}).sort_values("Impact", ascending=False)
                        
                        report_md = generate_release_report(df_report, df_clusters, sel_release)
                        
                        st.markdown("---")
                        st.markdown(report_md)
                        st.download_button(
                            label="Download Report as Markdown",
                            data=report_md,
                            file_name=f"Kompare_Audit_Report_{sel_release}_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown"
                        )
                
                st.info(f"💡 **Efficiency Tip**: Grouping by **{analysis_lvl}** helps you pinpoint exactly which {'Batch' if analysis_lvl == 'Pack' else 'Document Type'} is drifting the most from the Golden Copy.")
            else:
                st.info("No data available for analytics in the selected range.")
        finally:
            db.close()
    else:
        st.warning("Analytics unavailable (Database Offline).")
