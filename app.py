import streamlit as st
import requests
import re
import os
from huggingface_hub import InferenceClient

st.set_page_config(page_title="CitaGuard Q1-Engine", layout="wide")

# UI Styling
st.markdown("""<style>.proof-box {background-color: #f0f2f6; border-left: 5px solid #2ecc71; padding: 15px; margin-bottom: 10px;}</style>""", unsafe_allow_html=True)

st.title("🤖 CitaGuard: HF-Native Research Engine")

with st.sidebar:
    st.header("⚙️ Machine Settings")
    # MANUAL TOKEN BYPASS
    user_token = st.text_input("HF Token (Paste here if secret fails)", type="password")
    
    # Logic to choose the token
    hf_token = user_token if user_token else os.environ.get("HF_TOKEN")
    
    obj = st.sidebar.text_area("Research Objective", "Analyze psychometric validity.")
    model_id = st.text_input("Model ID", "meta-llama/Meta-Llama-3-8B-Instruct")

text_input = st.text_area("Paste Literature Review Segment", height=250)

if st.button("EXECUTE SYNTHESIS"):
    if not hf_token:
        st.error("🔑 Token Required: Paste your HF Write Token in the sidebar to begin.")
    else:
        # Initialize Client with the found token
        client = InferenceClient(model_id, token=hf_token)
        
        # --- PHASE 1: FORENSIC AUDIT + AUTO-DISCOVERY ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_report = ""
        
        st.subheader(f"🔍 Forensic Integrity Audit & Discovery ({current_year})")

        for sentence in sentences:
            citation_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sentence)
            if citation_match:
                author, year = citation_match.groups()
                year_int = int(year)
                
                # 1. Check existing source
                query = f"{author} {year}"
                res = requests.get(f"https://api.crossref.org/works?query.bibliographic={query}&rows=1").json()
                items = res.get('message', {}).get('items', [])
                
                status_msg = ""
                replacement_info = ""

                if items and year_int >= cutoff_year:
                    # Source is VALID and RECENT
                    title = items[0].get('title', ['Unknown'])[0]
                    status_msg = f"✅ VALID: {author} ({year})"
                    audit_report += f"Source {author} ({year}) is valid.\n"
                else:
                    # Source is OUTDATED or MISSING -> Find Replacement
                    st.warning(f"🔄 Finding replacement for outdated/invalid source: {author} ({year})")
                    
                    # NEW DISCOVERY SEARCH: Keyword-based, filtered by year
                    search_keywords = f"{obj} {sentence[:30]}"
                    discovery_url = f"https://api.crossref.org/works?query={search_keywords}&filter=from-pub-date:{cutoff_year}-01-01&rows=1"
                    
                    try:
                        discovery_res = requests.get(discovery_url).json()
                        new_items = discovery_res.get('message', {}).get('items', [])
                        
                        if new_items:
                            new_paper = new_items[0]
                            new_title = new_paper.get('title', ['Unknown Title'])[0]
                            new_author = new_paper.get('author', [{'family': 'Recent Scholar'}])[0].get('family')
                            new_year = new_paper.get('created', {}).get('date-parts', [[2025]])[0][0]
                            
                            replacement_info = f"💡 RECOMMENDED REPLACEMENT: {new_author} ({new_year}) - '{new_title}'"
                            audit_report += f"REPLACE {author} ({year}) WITH {new_author} ({new_year}). Title: {new_title}\n"
                        else:
                            replacement_info = "⚠️ No recent 2022-2026 matches found for this specific claim."
                    except:
                        replacement_info = "Discovery engine connection error."

                # UI Display
                st.markdown(f"""
                <div style="background-color: #f9f9f9; border-left: 5px solid {'#2ecc71' if not replacement_info else '#e74c3c'}; padding: 10px; margin-bottom: 10px;">
                    <strong>Claim:</strong> "{sentence}"<br>
                    <strong>Status:</strong> {status_msg if not replacement_info else '❌ Outdated/Invalid'}<br>
                    <span style="color: blue;">{replacement_info}</span>
                </div>
                """, unsafe_allow_html=True)
                
          # --- PHASE 2: NEURAL SYNTHESIS (The Executive Editor) ---
        st.divider()
        st.subheader("🧠 Q1 Neural Manuscript Synthesis")
        
        with st.spinner("Executing final synthesis and citation replacement..."):
            try:
                # The 'brain' now receives the audit as a set of instructions
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""You are a Q1 Academic Editor. 
                            GOAL: {obj}
                            
                            INSTRUCTIONS:
                            1. Read the AUDIT REPORT: {audit_report}
                            2. If a citation was flagged as OUTDATED or MISINTERPRETED, REPLACE it in the text with the 'RECOMMENDED REPLACEMENT' provided in the report.
                            3. If no replacement was found for an old source, remove the citation and frame the claim as a 'historically established' or 'foundational' concept.
                            4. Ensure all new citations are integrated naturally (e.g., 'As demonstrated by NewAuthor (2025)...').
                            5. Use sophisticated academic transitions (e.g., 'Synthetically,' 'Conversely,' 'Building upon the neuro-linguistic framework...')."""
                        },
                        {
                            "role": "user", 
                            "content": f"Apply these structural and factual fixes to the following text: {text_input}"
                        }
                    ],
                    max_tokens=1200,
                    temperature=0.2
                )
                
                final_manuscript = response.choices[0].message.content
                
                st.success("Q1 Synthesis Complete")
                st.markdown("### 📄 Revised Manuscript")
                st.write(final_manuscript)
                
                st.download_button(
                    label="Download Q1-Ready Draft",
                    data=final_manuscript,
                    file_name=f"Q1_Research_Draft_{current_year}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Synthesis Engine Error: {e}")
