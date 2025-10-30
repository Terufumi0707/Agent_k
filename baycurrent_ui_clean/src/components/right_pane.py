import streamlit as st

def render_right_pane():
    st.markdown("### アウトプット")
    st.caption("最新の生成結果")

    with st.container(border=True):
        output = st.session_state.get("last_output","")
        if output:
            st.markdown(output)
        else:
            st.markdown("（ここに最新の応答や生成結果が表示されます）")

    st.markdown("---")
    st.markdown("### エージェントログ（直近）")
    st.caption("直近 3 件の会話を確認できます")

    history = st.session_state.get("messages", [])[-3:]
    with st.container(border=True):
        for msg in history:
            st.markdown(msg["content"])
