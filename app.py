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
        
        # --- PHASE 1: FORENSIC DISCOVERY WITH LINKS ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_report = "" 
        
        st.subheader(f"🔍 Discovery & Pivot Analysis ({current_year})")

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                search_query = f"applied linguistics {obj} {sent[:35]}"
                discovery_url = f"https://api.crossref.org/works?query={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=1"
                
                try:
                    res = requests.get(discovery_url).json()
                    items = res.get('message', {}).get('items', [])
                    
                    if items:
                        top = items[0]
                        new_auth = top.get('author', [{'family': 'Scholar'}])[0].get('family')
                        new_year = top.get('created', {}).get('date-parts', [[2025]])[0][0]
                        new_title = top.get('title', ['Unknown Title'])[0]
                        doi = top.get('URL', '#') # Scrapes the direct DOI link
                        
                        report_entry = f"Claim: {sent} | NEW: {new_auth} ({new_year}) | Topic: {new_title} | Link: {doi}"
                        audit_report += report_entry + "\n"
                        
                        with st.expander(f"📌 Pivot: {new_auth} ({new_year})"):
                            st.markdown(f"**Actual Paper:** [{new_title}]({doi})")
                            st.write(f"**Forensic Note:** Replacing outdated/hallucinated logic with current 2022-2026 data.")
                except:
                    continue

        # --- PHASE 2: DELTA REPORT & SYNTHESIS ---
        st.divider()
        if audit_report:
            with st.spinner("Analyzing Hallucinations & Synthesizing..."):
                prompt = f"""
                SYSTEM: You are a Forensic Academic Editor.
                DATA: {audit_report}
                ORIGINAL TEXT: {text_input}
                
                TASK:
                1. Provide a 'DELTA REPORT' table: Column 1: Original Hallucination/Outdated Claim. Column 2: 2026 Updated Fact. Column 3: The New Source Link.
                2. Provide the 'Q1 REWRITE' integrating these pivots.
                3. Ensure no placeholders. Cite the actual authors found in the DATA.
                """
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500,
                    temperature=0.1
                )
                st.write(response.choices[0].message.content)
