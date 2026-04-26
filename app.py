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
        
        # --- PHASE 1: SEMANTIC CONTEXTUAL AUDIT ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_data = [] 
        
        st.subheader(f"🔍 Semantic Forensic Audit ({current_year})")

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                # TIGHT SEARCH: Force 'English Language Teaching' or 'Linguistics'
                search_query = f"ELT linguistics {sent[:40]}"
                discovery_url = f"https://api.crossref.org/works?query={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=2"
                
                try:
                    res = requests.get(discovery_url).json()
                    items = res.get('message', {}).get('items', [])
                    
                    valid_match = None
                    for item in items:
                        abstract = item.get('abstract', '').lower()
                        title = item.get('title', [''])[0].lower()
                        # DOUBLE-CHECK: Does the abstract actually talk about the claim?
                        keywords = ["grammar", "toefl", "test", "english", "linguistic", "syntactic", "writing"]
                        if any(k in abstract for k in keywords) or any(k in title for k in keywords):
                            valid_match = item
                            break
                    
                    if valid_match:
                        new_auth = valid_match.get('author', [{'family': 'Scholar'}])[0].get('family')
                        new_year = valid_match.get('created', {}).get('date-parts', [[2025]])[0][0]
                        doi = valid_match.get('URL', '#')
                        topic = valid_match.get('title', ['Unknown'])[0]
                        
                        audit_data.append({
                            "claim": sent,
                            "new_cite": f"{new_auth} ({new_year})",
                            "link": doi,
                            "topic": topic
                        })
                        st.success(f"🎯 Context Match: {new_auth} ({new_year}) - {topic[:50]}...")
                    else:
                        st.warning(f"⚠️ No contextually valid 2022-2026 match for: {sent[:30]}...")
                except:
                    continue

        # --- PHASE 2: DELTA REPORT & ACCURATE SYNTHESIS ---
        if audit_data:
            audit_report_string = "\n".join([f"CLAIM: {d['claim']} | NEW: {d['new_cite']} | TOPIC: {d['topic']} | LINK: {d['link']}" for d in audit_data])
            
            prompt = f"""
            SYSTEM: You are a Q1 Academic Forensic Editor. 
            DATA: {audit_report_string}
            
            TASK:
            1. Generate a DELTA REPORT Table. If a source (like Farzad 2023) was about psychology but used for a grammar claim, flag it as a 'Hallucinated Match' and find a more general way to state the fact.
            2. Rewrite the text. ONLY use the 'NEW' citations if the 'TOPIC' matches the 'CLAIM' logic. 
            3. Fix the Computer Engineering vs. Applied Linguistics mismatch.
            """
            # ... (Rest of your response = client.chat.completions logic)
