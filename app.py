"""
Streamlit chat app: agent fetches data from URL (e.g. Google Sheet), builds
DataMaLight Compare conf + dataset via LLM, and displays the Compare view in an iframe.
"""

from dotenv import load_dotenv

load_dotenv()
import streamlit as st
import streamlit.components.v1 as components

from agent import run as run_agent
from light_runner.iframe_html import build_embed_html

st.set_page_config(page_title="DataMaLight Chat", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("DataMaLight Compare – Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("payload") and msg["role"] == "assistant":
            dataset = msg["payload"].get("dataset", [])
            conf = msg["payload"].get("conf", {})
            if dataset and conf:
                html = build_embed_html(dataset, conf)
                components.html(html, height=550, scrolling=False)

if prompt := st.chat_input("Paste a Google Sheet URL (or message)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Fetching data and building Compare..."):
        result = run_agent(prompt, st.session_state.messages[:-1])
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["message"],
            "payload": result.get("payload"),
        }
    )
    st.rerun()
