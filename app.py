import streamlit as st
import requests
import re

st.set_page_config(page_title="CitaGuard Q1", layout="wide")

# Custom CSS for the 'Window Box' look
st.markdown("""
    <style>
    .proof-box {
        background-color: #f0f2f6;
        border-left: 5px solid #2ecc71;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .fail-box {
        background-color: #fdf2f2;
        border-left: 5px solid #e74c3c;
        padding: 15px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ CitaGuard: Integrity & Q1 Synthesis")

# Sidebar for Objectives
st.sidebar.header("Research Parameters")
obj = st.sidebar.text_area("Research Objective", placeholder="e.g., Analyzing the role of AI in listening assessment...")
min_year = st.sidebar.slider("Minimum Citation Year", 2010, 2026, 2022)

# Main Input
text_input = st.text_area("Paste Literature Review Segment", height=250)

if st.button("Run Integrity Audit & Q1 Rewrite"):
    if text_input:
        # 1. Regex to find citations (e.g., Smith, 2024)
        citations = re.findall(r'\(([^)]+),?\s(\d{4})\)', text_input)
        
        st.subheader("1. Integrity Audit (Window Boxes)")
        
        if not citations:
            st.warning("No citations detected in (Author, Year) format.")
        
        for author, year in citations:
            # 2. Simple API check to Crossref for factual verification
            query = f"{author} {year}"
            api_url = f"https://api.crossref.org/works?query.bibliographic={query}&rows=1"
            
            try:
                response = requests.get(api_url).json()
                items = response.get('message', {}).get('items', [])
                
                if items:
                    source = items[0]
                    title = source.get('title', ['Unknown Title'])[0]
                    journal = source.get('container-title', ['Unknown Journal'])[0]
                    pub_year = source.get('created', {}).get('date-parts', [[0]])[0][0]
                    
                    # 3. Create the Window Box UI
                    if int(pub_year) >= min_year:
                        st.markdown(f"""
                        <div class="proof-box">
                            <strong>🟢 Verified: {author} ({year})</strong><br>
                            <em>Title:</em> {title}<br>
                            <em>Journal:</em> {journal}<br>
                            <small>Factual status: Found in Crossref Index. Meets year criteria ({pub_year}).</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="fail-box">
                            <strong>⚠️ Outdated: {author} ({year})</strong><br>
                            <em>Actual Pub Year:</em> {pub_year}<br>
                            <small>Action: Machine suggests replacing with 2023-2026 data.</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"🔴 Hallucination Detected: Could not find {author} ({year}) in academic databases.")
            except:
                st.write("Connection error to database.")

        st.divider()
        st.subheader("2. Q1 Synthesis Preview")
        st.write("*(In the next step, we will activate the full LLM rewrite logic here)*")
    else:
        st.error("Please paste text first.")
