
import streamlit as st

# Configure the application
st.set_page_config(
    page_title="Gene–Disease Research Assistant",
    page_icon="🧬",
    layout="wide",
)

# Application title
st.title("🧬 Gene–Disease Research Assistant")

st.write(
    "Explore relationships between genes, genetic variants, "
    "and diseases using evidence from NCBI Gene and PubMed."
)

# Safety disclaimer
st.info(
    "For biomedical research and educational purposes only. "
    "Not intended for medical diagnosis or treatment."
)

# Chat input
question = st.chat_input(
    "Ask a gene–disease research question..."
)

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        st.write(
            "Your chat interface is working! "
            "We'll connect the research agents next."
        )
