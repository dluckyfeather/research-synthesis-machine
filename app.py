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
        
        # --- PHASE 1: LINGUISTICS-LOCKED AUDIT ---
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
                # PRECISION QUERY: Restricted to Education and Linguistics domains
                search_query = f"container-title:linguistics education testing {sent[:35]}"
                discovery_url = f"https://api.crossref.org/works?query={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=3"
                
                try:
                    res = requests.get(discovery_url).json()
                    items = res.get('message', {}).get('items', [])
                    
                    valid_match = None
                    for item in items:
                        # FILTER: Ensure the paper is actually about language/testing
                        subject = str(item.get('subject', [])).lower()
                        title = item.get('title', [''])[0].lower()
                        abstract = item.get('abstract', '').lower()
                        
                        if any(k in title or k in subject or k in abstract for k in ["english", "toefl", "language", "grammar", "syntactic", "pedagogy"]):
                            valid_match = item
                            break
                    
                    if valid_match:
                        new_auth = valid_match.get('author', [{'family': 'Scholar'}])[0].get('family')
                        new_year = valid_match.get('created', {}).get('date-parts', [[2025]])[0][0]
                        doi = valid_match.get('URL', '#')
                        topic = valid_match.get('title', ['Unknown'])[0]
                        
                        audit_data.append({
                            "claim": sent,
                            "old_cite": f"{auth} ({year})",
                            "new_cite": f"{new_auth} ({new_year})",
                            "link": doi,
                            "topic": topic,
                            "match_quality": "High" if "toefl" in title or "english" in title else "Partial"
                        })
                        st.success(f"🎯 Match: {new_auth} ({new_year}) - {topic[:50]}...")
                except: continue

        # --- PHASE 2: FORENSIC DELTA REPORT ---
        if audit_data:
            st.divider()
            audit_string = "\n".join([f"OLD: {d['old_cite']} | CLAIM: {d['claim']} | NEW: {d['new_cite']} | TOPIC: {d['topic']} | LINK: {d['link']}" for d in audit_data])
            
            prompt = f"""
            SYSTEM: You are a Q1 Forensic Editor.
            DATA: {audit_string}
            
            TASK:
            1. Generate a 'DELTA & HALLUCINATION REPORT' Table. 
               - Column 1: Original Hallucination (Identify if the source was fake or just outdated).
               - Column 2: 2026 Updated Linguistic Fact (Based on the 'TOPIC' in the data).
               - Column 3: The New Source Link.
            2. Q1 REWRITE: Integrate the 'NEW' citations. If a topic (like 'Apathy') doesn't match a grammar claim, flag it and do not use it in the rewrite.
            """
            # ... [Response logic continues here]
