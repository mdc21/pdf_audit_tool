import fitz, pdfplumber, re, hashlib, io, math, base64, os
import pandas as pd
import difflib
import logging
import ollama

def get_openai_client(api_key, base_url=None):
    """Dynamically import and initialize OpenAI client ONLY when needed."""
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=base_url)
    except ImportError:
        logging.error("OpenAI library not found. Run 'pip install openai' to use Cloud LLM features.")
        return None

class PDFAuditor:
    def __init__(self, config):
        self.config = config

    def get_hash(self, file_bytes):
        return hashlib.md5(file_bytes).hexdigest()

    def normalize(self, text):
        # Normalize whitespace but keep it readable for diffs
        text = re.sub(r'\s+', ' ', text).strip().lower()
        # Masking dynamic fields
        text = re.sub(r'\d{2}[/-]\d{2}[/-]\d{4}', '[DATE]', text)
        text = re.sub(r'\d{2}:\d{2}(:\d{2})?', '[TIME]', text)
        # Added: Policy/Account Num masking
        text = re.sub(r'[A-Z]{2,}-\d{5,}', '[ID]', text)
        text = re.sub(r'(policy|account)\s*#?\s*\d+', r'\1 [ID]', text)
        return text

    def get_lines(self, doc):
        """Extracts text preserving physical blocks for robust line detection."""
        all_lines = []
        for page in doc:
            blocks = page.get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                if text:
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    all_lines.extend(lines)
        return all_lines

    def summarize_diff_with_llm(self, diff_text, filename):
        """Generates a business-oriented summary of discrepancies using local LLM or Cloud API."""
        if not diff_text or diff_text.strip() == "":
            return "No significant text discrepancies found."
            
        system_prompt = """
        You are a senior business analyst reviewing discrepancies between two versions of a PDF document.
        TASK:
        Summarize the technical changes provided by the user in 2-3 concise bullet points focusing on the BUSINESS IMPACT.
        - Mention specific monetary value changes, policy numbers, dates, or address changes.
        - Do not use technical jargon like 'diff', '[-] ', or '[+] '.
        - Instead of saying "Text changed from X to Y", say "X was updated to Y".
        - If multiple values changed, group them logically.
        Focus on accuracy and clarity for a non-technical stakeholder.
        """
        
        user_content = f"Document: {filename}\nTechnical Diff:\n{diff_text[:2000]}"
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL", "qwen2.5:7b")
        base_url = os.getenv("LLM_BASE_URL") # Optional for custom endpoints
        
        logging.info(f"LLM Processing Request for {filename} (Model: {model})")
        
        try:
            if api_key:
                # Cloud-Ready Path: OpenAI Compatible (Groq, OpenRouter, etc.)
                client = get_openai_client(api_key, base_url)
                if not client:
                    return "Cloud Analysis Error: 'openai' library missing. Run 'pip install openai' locally."
                
                response = client.chat.completions.create(
                    model=os.getenv("LLM_CLOUD_MODEL", "llama-3.3-70b-versatile") if not base_url else model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.2,
                    max_tokens=400
                )
                llm_response = response.choices[0].message.content.strip()
            else:
                # Local Path: Ollama
                response = ollama.chat(
                    model=model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_content},
                    ],
                    options={"temperature": 0.2, "num_predict": 400}
                )
                llm_response = response['message']['content'].strip()
            
            if not llm_response:
                logging.warning(f"LLM returned an empty response for {filename}.")
                return "Analysis pending (LLM returned no content)."
                
            logging.info(f"LLM OUTPUT (Response for {filename}):\n{llm_response}")
            return llm_response
        except Exception as e:
            provider = "Cloud API" if api_key else "Local Ollama"
            logging.error(f"LLM Summarization via {provider} failed for {filename}: {e}")
            if not api_key:
                return f"Narrative synth failed: Failed to connect to Ollama. Running in the Cloud? Please add 'LLM_API_KEY' to your Streamlit Secrets."
            return f"AI Insight unavailable (Cloud API Error): {str(e)}"

    def compare_tables(self, src_bytes, tgt_bytes):
        """Returns True if structural table shapes match."""
        try:
            with pdfplumber.open(io.BytesIO(src_bytes)) as src_p:
                src_tabs = [p.extract_tables() for p in src_p.pages]
            with pdfplumber.open(io.BytesIO(tgt_bytes)) as tgt_p:
                tgt_tabs = [p.extract_tables() for p in tgt_p.pages]
            return src_tabs == tgt_tabs
        except Exception as e:
            logging.error(f"Table extraction failed: {e}")
            return False

    def compare_visual(self, src_bytes, tgt_bytes, max_snapshots=3):
        """Calculates RMS error and captures top divergent page snapshots."""
        doc_s = fitz.open(stream=src_bytes, filetype="pdf")
        doc_t = fitz.open(stream=tgt_bytes, filetype="pdf")
        
        total_rms = 0
        pages = min(len(doc_s), len(doc_t))
        divergences = [] # List of (rms, page_index, pix_s, pix_t)
        
        for i in range(pages):
            pix_s = doc_s[i].get_pixmap(dpi=72)
            pix_t = doc_t[i].get_pixmap(dpi=72)
            
            if pix_s.width != pix_t.width or pix_s.height != pix_t.height:
                rms = 1.0
            else:
                s_buf, t_buf = pix_s.samples, pix_t.samples
                if s_buf == t_buf:
                    rms = 0
                else:
                    sum_sq, count = 0, 0
                    for j in range(0, len(s_buf), 10):
                        sum_sq += (int(s_buf[j]) - int(t_buf[j]))**2
                        count += 1
                    rms = math.sqrt(sum_sq / count) / 255.0
            
            total_rms += rms
            if rms > 0:
                divergences.append((rms, i, pix_s, pix_t))
            
        avg_rms = total_rms / max(pages, 1)
        
        # Collect top snapshots
        visual_pairs = []
        divergences.sort(key=lambda x: x[0], reverse=True)
        for rms, p_idx, p_s, p_t in divergences[:max_snapshots]:
            img_s = base64.b64encode(p_s.tobytes("png")).decode("utf-8")
            img_t = base64.b64encode(p_t.tobytes("png")).decode("utf-8")
            visual_pairs.append({"page": p_idx + 1, "rms": rms, "src": img_s, "tgt": img_t})
            
        return avg_rms, visual_pairs

    def compare(self, src_bytes, tgt_bytes, mode="TEXT_TABLE", rms_threshold=0.01, filename="document"):
        logging.info(f"Starting PDF comparison in {mode} mode...")
        
        if mode == "VISUAL":
            rms_score, visual_pairs = self.compare_visual(src_bytes, tgt_bytes)
            status = "PASS" if rms_score <= rms_threshold else "FAIL"
            return {
                "status": status,
                "score": 1.0 - rms_score,
                "diff": f"Avg Visual Divergence (RMS): {rms_score:.5f}",
                "html_diff": "",
                "visual_pairs": visual_pairs
            }

        # DEFAULT: TEXT & TABLE
        doc_src = fitz.open(stream=src_bytes, filetype="pdf")
        doc_tgt = fitz.open(stream=tgt_bytes, filetype="pdf")
        
        txt_src_norm = self.normalize(" ".join([p.get_text() for p in doc_src]))
        txt_tgt_norm = self.normalize(" ".join([p.get_text() for p in doc_tgt]))
        
        text_match = (txt_src_norm == txt_tgt_norm)
        table_match = self.compare_tables(src_bytes, tgt_bytes)
        
        status = "PASS"
        if not text_match: status = "FAIL"
        elif not table_match: status = "WARNING"
            
        text_diff, html_diff = "", ""
        if status != "PASS":
            lines_src = self.get_lines(doc_src)
            lines_tgt = self.get_lines(doc_tgt)
            html_engine = difflib.HtmlDiff(tabsize=4)
            # Use make_table() not make_file() - returns just the <table>,
            # so we can embed it inline with st.markdown (no fixed-height iframe needed)
            table_html = html_engine.make_table(
                lines_src, lines_tgt, context=True, numlines=10
            )

            # Strip diff_next columns AND colgroup - removes blank ghost columns
            import re as _re
            table_html = _re.sub(r'<td class="diff_next"[^>]*>.*?</td>', '', table_html, flags=_re.DOTALL)
            table_html = _re.sub(r'<th class="diff_next"[^>]*>.*?</th>', '', table_html, flags=_re.DOTALL)
            table_html = _re.sub(r'<colgroup>.*?</colgroup>', '', table_html, flags=_re.DOTALL)

            # Wrap in a div - CSS is injected globally in app.py
            html_diff = f'<div class="kdiff-wrap"><div class="kdiff">{table_html}</div></div>'

            
            src_words, tgt_words = txt_src_norm.split(), txt_tgt_norm.split()
            matcher = difflib.SequenceMatcher(None, src_words, tgt_words)
            diff_parts = [f"[-] {' '.join(src_words[i1:i2])} / [+] {' '.join(tgt_words[j1:j2])}" 
                          for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != 'equal']
            text_diff = "\n".join(diff_parts[:20])
            if not table_match:
                text_diff = "[STRUCTURAL WARNING] Table layout changed.\n" + text_diff

            # Note: LLM Insight generation removed from synchronous path for speed.
            # It is now triggered on-demand via the UI.
            llm_insight = None
        else:
            llm_insight = None

        return {
            "status": status, 
            "score": 1.0 if status == "PASS" else (0.8 if status == "WARNING" else 0.0),
            "diff": text_diff,
            "html_diff": html_diff,
            "llm_insight": llm_insight
        }
