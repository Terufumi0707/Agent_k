import streamlit as st

def render_right_pane():
    st.markdown("### アウトプット")

    with st.container(border=True):
        output = st.session_state.get("last_output","")
        if output:
            st.markdown(output)
        else:
            st.markdown("（ここに最新の応答や生成結果が表示されます）")

    st.markdown("---")
    st.markdown("### エージェントログ（直近）")

    history = st.session_state.get("messages", [])[-3:]
    for msg in history:
        st.markdown(msg["content"])
