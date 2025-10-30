import streamlit as st

from backend import run_schedule_change_workflow


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "こんにちは。ベイカレント風エージェントです。どの案件から進めますか？"},
        ]
    if "last_output" not in st.session_state:
        st.session_state.last_output = ""


def render_center_chat():
    init_state()
    st.markdown("#### チャットエリア")

    for msg in st.session_state.messages:
        role_class = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(msg["role"]):
            st.markdown(
                f"<div class='chat-message {role_class}'>{msg['content']}</div>",
                unsafe_allow_html=True,
            )

    user_input = st.chat_input("メッセージを入力してください…")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(
                f"<div class='chat-message user'>{user_input}</div>",
                unsafe_allow_html=True,
            )

        reply = run_schedule_change_workflow(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.last_output = reply

        with st.chat_message("assistant"):
            st.markdown(
                f"<div class='chat-message assistant'>{reply}</div>",
                unsafe_allow_html=True,
            )
