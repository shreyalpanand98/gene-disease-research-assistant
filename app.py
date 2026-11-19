
import streamlit as st

from orchestrator import process_research_question
from session_memory import ResearchMemory

st.set_page_config(
    page_title="Gene–Disease Research Assistant",
    page_icon="🧬",
    layout="wide",
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "research_memory" not in st.session_state:
    st.session_state.research_memory = ResearchMemory(max_turns=5)

# Example research questions
example_questions = [
    "What is the PKD1 gene?",
    "How do PKD1 mutations affect ADPKD progression?",
    "What is the difference between PKD1 and PKD2?",
]

# Sidebar
with st.sidebar:
    st.header("🧬 Research Dashboard")

    st.subheader("Current Session")

    question_count = sum(
        1 for message in st.session_state.messages
        if message["role"] == "user"
    )

    st.metric("Research Questions", question_count)
    st.metric("Conversation Messages", len(st.session_state.messages))

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.research_memory.clear()
        st.rerun()

    st.divider()

    st.subheader("Research Sources")
    st.write("🧬 NCBI Gene")
    st.write("📚 PubMed")

    st.caption(
        "Source retrieval will be enabled when "
        "the research backend is connected."
    )

# Main interface
st.title("🧬 Gene–Disease Research Assistant")

st.write(
    "Explore relationships between genes, genetic variants, "
    "and diseases using scientific evidence."
)

st.info(
    "For biomedical research and educational purposes only. "
    "Not intended for medical diagnosis or treatment."
)

# Suggested questions
st.subheader("Suggested Research Questions")

columns = st.columns(3)

selected_question = None

for index, example in enumerate(example_questions):
    with columns[index]:
        if st.button(
            example,
            key=f"example_{index}",
            use_container_width=True,
        ):
            selected_question = example

st.divider()

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Accept typed or suggested question
typed_question = st.chat_input(
    "Ask a gene–disease research question..."
)

question = selected_question or typed_question


if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Researching NCBI Gene and PubMed..."):
            try:
                result = process_research_question(
                    question,
                    st.session_state.research_memory,
                )

                if result["status"] == "completed":
                    response = result["answer"]

                else:
                    # Never display an answer that failed safety review
                    response = (
                        "⚠️ The research answer was withheld because "
                        "the evidence or scientific claims require "
                        "additional review."
                    )

            except Exception as e:
                import traceback

                print("\n--- STREAMLIT BACKEND ERROR ---")
                traceback.print_exc()

                response = (
                    "⚠️ The research request could not be completed. "
                    "Check the VS Code terminal for details."
                )

    st.write(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
    })

    st.rerun()
