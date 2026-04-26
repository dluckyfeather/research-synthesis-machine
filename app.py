import streamlit as st

st.set_page_config(page_title="CitaGuard Q1", layout="wide")
st.title("🛡️ CitaGuard: Q1 Research Synthesizer")

# Inputs
obj = st.sidebar.text_input("Research Objective", placeholder="e.g., Impact of AI on L2 Listening")
text_area = st.text_area("Paste Literature Review Segment", height=300)

if st.button("Run Audit"):
    st.write(f"### Target Objective: {obj}")
    st.info("Machine is warming up... (API connections pending)")
    # This is where we will insert the 'Window Box' logic next
