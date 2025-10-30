import streamlit as st
from components.sidebar import render_workspace_sidebar
from components.chat_area import render_center_chat
from components.right_pane import render_right_pane

st.set_page_config(page_title="BayCurrent風エージェントUI", layout="wide")

# CSS読み込み
with open("src/assets/styles.css","r",encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown("## BayCurrent風 AIエージェント")

cols = st.columns([0.22, 0.53, 0.25])

with cols[0]:
    render_workspace_sidebar()
with cols[1]:
    render_center_chat()
with cols[2]:
    render_right_pane()
