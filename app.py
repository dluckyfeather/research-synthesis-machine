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
        
        # --- PHASE 1 & 2: INTEGRATED FORENSIC SYNC ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_entries = [] 
        
        st.subheader(f"🔍 Forensic Audit & Discovery ({current_year})")

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                # TIGHT SEARCH: Force linguistic context
                search_query = f"linguistics testing grammar {sent[:30]}"
                discovery_url = f"https://api.crossref.org/works?query={search_query}&filter=from-pub-date:{cutoff_year}-01-01&rows=2"
                
                try:
                    res = requests.get(discovery_url).json()
                    item = res.get('message', {}).get('items', [{}])[0]
                    
                    if item:
                        new_auth = item.get('author', [{'family': 'Scholar'}])[0].get('family')
                        new_year = item.get('created', {}).get('date-parts', [[2025]])[0][0]
                        doi = item.get('URL', '#')
                        title = item.get('title', ['Unknown'])[0]
                        
                        # LOGIC: Is this actually about the claim?
                        is_relevant = any(k in title.lower() for k in ["english", "grammar", "toefl", "test", "writing", "linguistic"])
                        
                        audit_entries.append({
                            "old": f"{auth} ({year})",
                            "new": f"{new_auth} ({new_year})",
                            "link": doi,
                            "topic": title,
                            "relevant": is_relevant,
                            "claim": sent
                        })
                        
                        icon = "🎯" if is_relevant else "⚠️"
                        st.write(f"{icon} **Found:** {new_auth} ({new_year}) - *{title[:60]}...*")
                except: continue

        # --- FINAL PHASE: THE DELTA REPORT & REWRITE ---
        if audit_entries:
            st.divider()
            report_context = "\n".join([f"CLAIM: {d['claim']} | NEW_SOURCE: {d['new']} | TOPIC: {d['topic']} | RELEVANT: {d['relevant']} | LINK: {d['link']}" for d in audit_entries])
            
            with st.spinner("Generating Delta Report & Q1 Rewrite..."):
                try:
                    prompt = f"""
                    SYSTEM: You are a Q1 Academic Forensic Editor. 
                    CONTEXT: {report_context}
                    
                    TASK:
                    1. Display a 'DELTA REPORT' Markdown table. 
                       - Column 1: Hallucination/Outdated (The old citation).
                       - Column 2: 2026 Fact (Update based on the NEW_SOURCE topic).
                       - Column 3: Source Link.
                       - If RELEVANT is False, flag it as 'MISMATCHED TOPIC' and explain why.
                    2. Provide the 'Q1 REWRITE'. Use only the RELEVANT new sources. If a source is irrelevant, rewrite the claim as a general consensus without a citation.
                    """
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1500,
                        temperature=0.1
                    )
                    st.markdown("### 📊 Delta & Hallucination Report")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Synthesis failed: {e}")
