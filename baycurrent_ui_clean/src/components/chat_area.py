import html

import streamlit as st

from backend import WorkflowResult, run_schedule_change_workflow


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "こんにちは。BayCurrentエージェントです。どの案件から進めますか？",
            },
        ]
    if "last_output" not in st.session_state:
        st.session_state.last_output = ""
    if "workflow_path" not in st.session_state:
        st.session_state.workflow_path = []
    if "workflow_classification" not in st.session_state:
        st.session_state.workflow_classification = "other"


def render_center_chat():
    init_state()
    st.markdown("#### BayCurrentエージェントとのチャット")
    st.caption("最新の会話が下部に表示されます")

    chat_placeholder = st.container()
    st.markdown("---")
    st.caption("Enter キーで送信 / Shift + Enter で改行できます")
    user_input = st.chat_input("こちらにメッセージを入力してください", key="main_chat_input")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        result: WorkflowResult = run_schedule_change_workflow(user_input)
        st.session_state.messages.append({"role": "assistant", "content": result.message})
        st.session_state.last_output = result.message
        st.session_state.workflow_path = result.path
        st.session_state.workflow_classification = result.classification

    with chat_placeholder:
        chat_html_parts: list[str] = []
        for msg in st.session_state.messages:
            role_class = "assistant" if msg["role"] == "assistant" else "user"
            content = html.escape(msg["content"]).replace("\n", "<br>")
            chat_html_parts.append(
                f"<div class='chat-bubble {role_class}'>{content}</div>"
            )

        chat_html = "".join(chat_html_parts)
        st.markdown(
            f"<div class='chat-log'>{chat_html}</div>",
            unsafe_allow_html=True,
        )
