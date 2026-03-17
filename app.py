"""
Streamlit chat app: agent accepts any prompt and keeps message history. When the user
provides a data source URL (e.g. Google Sheet), the LLM uses the fetch_datas tool;
then we build DataMaLight Compare conf + dataset and display the Compare view in an iframe.
"""

from dotenv import load_dotenv

load_dotenv()
import streamlit as st
import streamlit.components.v1 as components

from agent import run as run_agent
from light_runner.iframe_html import build_embed_html
from app_header import render_app_header

st.set_page_config(page_title="Datama AI Chat", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []

render_app_header()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("payload") and msg["role"] == "assistant":
            dataset = msg["payload"].get("dataset", [])
            conf = msg["payload"].get("conf", {})
            if dataset and conf:
                html = build_embed_html(dataset, conf)
                components.html(html, height=600, scrolling=False)

if prompt := st.chat_input(
    "Prompt instruction (data should be provided through Gsheet public url)"
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        result = run_agent(prompt, st.session_state.messages[:-1])
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["message"],
            "payload": result.get("payload"),
        }
    )
    st.rerun()
