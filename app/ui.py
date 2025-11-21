import streamlit as st
from agents import is_menu_query, menu_tool, run_faq, restaurant_team
import os

# ---------------- UI CONFIG ----------------
st.set_page_config(
    page_title="Xander's AI Assistant",
    page_icon="🍽️",
    layout="centered"
)

# ---------------- CUSTOM CSS TO REMOVE AVATARS COMPLETELY ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700&display=swap');

/* GLOBAL */
html, body, .stApp {
    background-color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    color: #000000 !important;
}

/* ⚡ REMOVE ALL CHAT AVATARS + THE COLUMN THEY SIT IN */
div[data-testid="stChatMessageAvatar"] {
    display: none !important;
}

/* Remove avatar column (most important fix) */
div[data-testid="stChatMessage"] {
    grid-template-columns: 1fr !important;
}

/* Removes leftover spacing where avatars were */
div[data-testid="stChatMessage"] > div:first-child {
    display: none !important;
}

/* Remove hover expand button */
[data-testid="stChatMessageExpand"] {
    display: none !important;
}

/* ---------- CHAT CONTAINER ---------- */
div[data-testid="stChatMessageContainer"] {
    display: grid !important;
    grid-template-columns: 1fr !important;
    gap: 0 !important;
}

/* ---------- USER MESSAGE ---------- */
div[data-testid="stChatMessageContent"]:not([data-testid="assistant"]) {
    background: #FFFFFF !important;
    border: 2px solid #8CC63E !important;
    border-radius: 12px !important;
    padding: 12px !important;
    font-size: 16px !important;
    color: #000000 !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05) !important;
}

/* ---------- ASSISTANT MESSAGE ---------- */
div[data-testid="assistant"] div[data-testid="stChatMessageContent"] {
    background: #EDEDED !important;
    border-radius: 12px !important;
    padding: 12px !important;
    font-size: 16px !important;
    color: #000000 !important;
    border: none !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.03) !important;
}

/* ---------- INPUT BOX ---------- */
textarea, .stTextArea>div>div>textarea {
    border: 2px solid #8CC63E !important; /* green border */
    border-radius: 12px !important;
    background-color: #8CC63E !important; /* change background to match border */
    color: #000000 !important; /* text color stays black */
    padding: 8px !important;
    font-size: 16px !important;
    outline: none !important;
    box-shadow: none !important;
}

textarea:focus, .stTextArea>div>div>textarea:focus {
    border: 2px solid #6EA52F !important; /* darker green on focus */
    background-color: #6EA52F !important; /* match focus border */
    box-shadow: none !important;
}


/* ---------- SEND BUTTON ---------- */
button, div.stButton>button {
    background-color: #8CC63E !important;
    color: white !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 6px 16px !important;
    font-size: 16px;
}

button:hover, div.stButton>button:hover {
    background-color: #6EA52F !important;
}

/* TITLE */
.main-title {
    text-align: center;
    color: #8CC63E;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 54px;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADING ----------------
st.markdown("<h1 class='main-title' style='color:#8CC63E;'>XANDER'S AI ASSISTANT</h1>", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "menu_pdf" not in st.session_state:
    st.session_state.menu_pdf = None

# ---------------- DISPLAY CHAT HISTORY ----------------
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg.get("content") == "PDF_BUTTON":
            st.info("📄 Menu PDF is ready!")
            if st.session_state.menu_pdf and os.path.exists(st.session_state.menu_pdf):
                with open(st.session_state.menu_pdf, "rb") as f:
                    st.download_button(
                        label="📥 Download Menu PDF",
                        data=f,
                        file_name="menu_card.pdf",
                        mime="application/pdf",
                        key=f"menu_pdf_{idx}"
                    )
        else:
            st.write(msg["content"])

# ---------------- USER INPUT ----------------
user_query = st.chat_input("Ask anything about menu, branches, or food...")

pdf_triggers = ["generate card", "show me menu card", "menu card", "make menu card"]

if user_query:

    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("user"):
        st.write(user_query)

    with st.spinner("Thinking..."):

        if any(t in user_query.lower() for t in pdf_triggers):

            response = menu_tool.run(user_query)

            pdf_file = "menu_card.pdf"
            if os.path.exists(pdf_file):
                st.session_state.menu_pdf = pdf_file

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "PDF_BUTTON"
                })

                with st.chat_message("assistant"):
                    st.info("📄 Menu PDF is ready!")
                    with open(st.session_state.menu_pdf, "rb") as f:
                        st.download_button(
                            label="📥 Download Menu PDF",
                            data=f,
                            file_name="menu_card.pdf",
                            mime="application/pdf",
                            key=f"menu_pdf_{len(st.session_state.messages)}"
                        )
                st.rerun()

        elif is_menu_query(user_query, menu_tool):
            response = menu_tool.run(user_query)

        elif any(word in user_query.lower() for word in [
            "branch", "location", "clifton", "tipu sultan", "bukhari",
            "contact", "timing", "hours", "number", "address",
            "policy", "allergy", "ingredient", "gluten"
        ]):
            response = run_faq(user_query)

        else:
            resp = restaurant_team.run(user_query)
            response = resp.content if hasattr(resp, "content") else resp

    if not any(t in user_query.lower() for t in pdf_triggers):
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)