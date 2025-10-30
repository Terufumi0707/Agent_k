import streamlit as st

from backend import WorkflowResult, run_schedule_change_workflow


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "こんにちは。ベイカレント風エージェントです。どの案件から進めますか？"},
        ]
    if "last_output" not in st.session_state:
        st.session_state.last_output = ""
    if "workflow_path" not in st.session_state:
        st.session_state.workflow_path = []
    if "workflow_classification" not in st.session_state:
        st.session_state.workflow_classification = "other"


def render_center_chat():
    init_state()
    st.markdown("#### チャットエリア")
    st.caption("担当エージェントとの会話履歴")

    chat_log = st.container()

    with chat_log:
        for msg in st.session_state.messages:
            role_class = "assistant" if msg["role"] == "assistant" else "user"
            with st.chat_message(msg["role"]):
                st.markdown(
                    f"<div class='chat-message {role_class}'>{msg['content']}</div>",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("##### メッセージ入力")
    st.caption("Enter キーで送信 / Shift + Enter で改行できます")
    user_input = st.chat_input("こちらにメッセージを入力してください", key="main_chat_input")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(
                f"<div class='chat-message user'>{user_input}</div>",
                unsafe_allow_html=True,
            )

        result: WorkflowResult = run_schedule_change_workflow(user_input)
        st.session_state.messages.append({"role": "assistant", "content": result.message})
        st.session_state.last_output = result.message
        st.session_state.workflow_path = result.path
        st.session_state.workflow_classification = result.classification

        with st.chat_message("assistant"):
            st.markdown(
                f"<div class='chat-message assistant'>{result.message}</div>",
                unsafe_allow_html=True,
            )
