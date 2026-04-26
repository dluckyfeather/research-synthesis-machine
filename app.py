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
        
        # --- PHASE 1: PRECISION DISCOVERY ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_report = "" # FIX: Initializing the variable
        
        st.subheader(f"🔍 Discovery & Pivot Suggestions ({current_year})")

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                
                # TIGHTENED SEARCH: Adding 'applied linguistics' to force relevancy
                search_query = f"applied linguistics {obj} {sent[:30]}"
                discovery_url = f"https://api.crossref.org/works?query={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=1"
                
                try:
                    res = requests.get(discovery_url).json()
                    items = res.get('message', {}).get('items', [])
                    
                    if items:
                        top = items[0]
                        new_auth = top.get('author', [{'family': 'Scholar'}])[0].get('family')
                        new_year = top.get('created', {}).get('date-parts', [[2025]])[0][0]
                        new_title = top.get('title', ['Research'])[0]
                        
                        # Add to the report that Phase 2 will read
                        report_entry = f"Original: {sent} | REPLACE WITH: {new_auth} ({new_year}) - Topic: {new_title}"
                        audit_report += report_entry + "\n"
                        
                        with st.expander(f"Pivot: {new_auth} ({new_year})"):
                            st.write(f"**Found Paper:** {new_title}")
                            st.info(f"**Machinery Action:** Pivoting claim to match '{new_auth}' findings.")
                except:
                    continue

        # --- PHASE 2: THE SYNCED REWRITE ---
        st.divider()
        st.subheader("🧠 Q1 Neural Manuscript Synthesis")
        
        if audit_report == "":
            st.warning("No citations found to audit. Proceeding with stylistic rewrite only.")

        with st.spinner("Synthesizing final draft with 2026 Discovery data..."):
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system", 
                            "content": f"You are a Q1 Editor. OBJECTIVE: {obj}. AUDIT REPORT: {audit_report}. REWRITE RULES: 1. You MUST use the new authors/years from the Audit Report. 2. Change the claim's wording to match the 'Topic' found in the report. 3. Ensure a seamless Q1 flow."
                        },
                        {
                            "role": "user", 
                            "content": f"Rewrite this text using the discovery data: {text_input}"
                        }
                    ],
                    max_tokens=1200,
                    temperature=0.2
                )
                
                q1_output = response.choices[0].message.content
                st.success("Synthesis Complete")
                st.write(q1_output)
            except Exception as e:
                st.error(f"Synthesis Engine Error: {e}")
