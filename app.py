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
        
        # --- PHASE 1: SEMANTIC SCHOLAR DISCOVERY ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_data = [] 

        st.subheader(f"📑 Grounded Evidence Cards ({current_year})")

        for sent in sentences:
            cit_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sent)
            if cit_match:
                auth, year = cit_match.groups()
                
                # Semantic Scholar API URL (No key needed for low volume)
                # We request 'tldr' and 'abstract' for maximum grounding
                s2_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={sent[:60]}&limit=1&fields=title,authors,year,url,abstract,tldr,venue"
                
                try:
                    res = requests.get(s2_url).json()
                    if res.get('data'):
                        paper = res['data'][0]
                        new_auth = paper['authors'][0]['name'] if paper['authors'] else "Scholar"
                        new_year = paper['year']
                        new_title = paper['title']
                        new_url = paper['url']
                        
                        # NotebookLM Mechanism: Prefer TLDR, fallback to Abstract
                        evidence_quote = paper.get('tldr', {}).get('text') if paper.get('tldr') else paper.get('abstract')
                        if not evidence_quote: evidence_quote = "No snippet available—please verify via URL."
                        
                        # Filtering for Recency
                        if new_year and new_year >= cutoff_year:
                            audit_data.append({
                                "original_sent": sent,
                                "new_cite": f"{new_auth} ({new_year})",
                                "evidence": evidence_quote,
                                "title": new_title,
                                "link": new_url
                            })
                            
                            # UI Evidence Card
                            with st.container():
                                st.markdown(f"**Evidence for Claim:** *\"{sent[:50]}...\"*")
                                st.caption(f"📖 **{new_title}** ({new_year}) — {paper.get('venue', 'Academic Journal')}")
                                st.info(f"“{evidence_quote[:400]}...”")
                                st.markdown(f"[Source Link]({new_url})")
                                st.divider()
                except Exception as e:
                    st.error(f"S2 API Error: {e}")

        # --- PHASE 2: THE NOTEBOOK-STYLE SYNTHESIS ---
        if audit_data:
            st.subheader("🧠 Grounded Q1 Rewrite")
            
            # Combine all evidence into one block for the LLM
            evidence_context = "\n".join([
                f"CLAIM: {d['original_sent']}\nEVIDENCE: {d['evidence']}\nNEW_SOURCE: {d['new_cite']}" 
                for d in audit_data
            ])

            with st.spinner("Synthesizing based on retrieved evidence..."):
                try:
                    prompt = f"""
                    SYSTEM: You are a Research Integrity AI. You use 'Grounded Theory' to rewrite text.
                    EVIDENCE DATA:
                    {evidence_context}
                    
                    TASK:
                    1. Create a Table: [Original Hallucination] | [Direct Evidence Quote] | [Correction].
                    2. Rewrite the text into a Q1 Literature Review.
                    3. RULES: 
                       - If the EVIDENCE contradicts the CLAIM, change the claim to match the evidence.
                       - Use only the NEW_SOURCE names provided.
                       - If no evidence is relevant, state 'Insufficient Evidence' and remove the claim.
                    """
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1500,
                        temperature=0.1
                    )
                    st.markdown(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Synthesis Error: {e}")
