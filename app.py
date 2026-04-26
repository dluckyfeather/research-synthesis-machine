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
        
        # --- PHASE 1: FORENSIC CLAIM VERIFICATION ---
        import datetime
        current_year = datetime.datetime.now().year
        cutoff_year = current_year - 4
        
        # Regex to find the sentence containing the citation
        sentences = re.split(r'(?<=[.!?]) +', text_input)
        audit_report = ""
        
        st.subheader(f"🔍 Forensic Integrity Audit ({current_year})")

        for sentence in sentences:
            citation_match = re.search(r'\(([^)]+),?\s(\d{4})\)', sentence)
            if citation_match:
                author, year = citation_match.groups()
                year_int = int(year)
                
                # 1. Fetch metadata + Abstract from Crossref
                query = f"{author} {year} {sentence[:50]}"
                res = requests.get(f"https://api.crossref.org/works?query.bibliographic={query}&rows=1").json()
                items = res.get('message', {}).get('items', [])
                
                if items:
                    item = items[0]
                    title = item.get('title', ['Unknown'])[0]
                    abstract = item.get('abstract', "No abstract available for automated matching.")
                    actual_year = item.get('created', {}).get('date-parts', [[0]])[0][0]
                    
                    # 2. THE NEURAL VERDICT (Comparing Claim vs. Abstract)
                    with st.spinner(f"Verifying claim for {author}..."):
                        verdict_prompt = f"""
                        COMPARE CLAIM VS DATA:
                        Claim in Text: "{sentence}"
                        Article Title: "{title}"
                        Article Abstract: "{abstract}"
                        
                        Does the claim in the text accurately reflect the data/topic of the article?
                        Respond with: [MATCH], [MISINTERPRETATION], or [UNVERIFIABLE].
                        Briefly explain why.
                        """
                        verdict_res = client.chat.completions.create(
                            model=model_id,
                            messages=[{"role": "user", "content": verdict_prompt}],
                            max_tokens=150
                        )
                        verdict = verdict_res.choices[0].message.content

                    # 3. THE WINDOW BOX UI
                    color = "green" if "MATCH" in verdict and year_int >= cutoff_year else "red"
                    border = "5px solid #2ecc71" if color == "green" else "5px solid #e74c3c"
                    
                    st.markdown(f"""
                    <div style="background-color: #f9f9f9; border-left: {border}; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
                        <strong>📍 Claim Location:</strong> "{sentence}"<br>
                        <strong>📄 Cited Article:</strong> {title} ({actual_year})<br>
                        <strong>⚖️ Forensic Verdict:</strong> {verdict}<br>
                        <strong>📅 Recency:</strong> {"✅ Pass" if year_int >= cutoff_year else "❌ Fail (Pre-"+str(cutoff_year)+")"}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    audit_report += f"Sentence: {sentence} | Verdict: {verdict}\n"
                else:
                    st.error(f"🚨 HALLUCINATION: {author} ({year}) not found in database.")

        # --- PHASE 2: NEURAL SYNTHESIS (Updated for Conversational Task) ---
        st.divider()
        st.subheader("🧠 Q1 Neural Rewrite")
        
        with st.spinner("Synthesizing through Hugging Face Chat Layers..."):
            try:
                # Switching to the Chat Completion method to satisfy the provider
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": f"You are a Q1 Academic Editor. Objective: {obj}. Audit Report: {audit_report}"},
                        {"role": "user", "content": f"Rewrite this text for high-impact flow and interconnectedness. Fix citations: {text_input}"}
                    ],
                    max_tokens=1000,
                    temperature=0.2
                )
                
                # Extract the message content correctly
                q1_output = response.choices[0].message.content
                
                st.success("Synthesis Complete")
                st.write(q1_output)
                st.download_button("Download Q1 Manuscript", q1_output, "Q1_Revised.txt")
            except Exception as e:
                st.error(f"Neural Engine Error: {e}. Try changing the Model ID in the sidebar to 'meta-llama/Llama-3.2-3B-Instruct' if this persists.")
