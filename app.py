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
        
        # --- PHASE 1: COLLABORATIVE AUDIT & DATA MATCHING ---
import datetime
current_year = datetime.datetime.now().year
cutoff_year = current_year - 4

sentences = re.split(r'(?<=[.!?]) +', text_input)
audit_results = []

for sent in sentences:
    cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
    if cit_match:
        auth, year = cit_match.groups()
        # LIVE DISCOVERY: Search for the newest 2024-2026 data related to this claim
        search_query = f"{obj} {sent[:40]}"
        res = requests.get(f"https://api.crossref.org/works?query={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=1").json()
        items = res.get('message', {}).get('items', [])
        
        if items:
            top = items[0]
            new_auth = top.get('author', [{'family': 'Scholar'}])[0].get('family')
            new_year = top.get('created', {}).get('date-parts', [[2026]])[0][0]
            new_title = top.get('title', ['Research'])[0]
            
            # THE COLLABORATION: Machine proposes a change
            audit_results.append({
                "original_claim": sent,
                "found_source": f"{new_auth} ({new_year})",
                "source_context": new_title,
                "action": "MATCH & UPDATE" if int(year) < cutoff_year else "VERIFIED"
            })

# --- UI DISPLAY FOR YOUR APPROVAL ---
st.subheader("🔍 Discovery & Pivot Suggestions")
for r in audit_results:
    with st.expander(f"Claim: {r['original_claim'][:50]}..."):
        st.write(f"**Current Status:** {r['action']}")
        st.write(f"**Found Relevant 2026 Source:** {r['found_source']}")
        st.write(f"**Paper Topic:** {r['source_context']}")
        st.info("The AI will now 'Pivot' your claim to match this specific research.")
                
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
