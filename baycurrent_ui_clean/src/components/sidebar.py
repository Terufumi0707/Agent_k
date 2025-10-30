import streamlit as st

def render_workspace_sidebar():
    st.markdown("### ワークスペース")

    with st.expander("【完了】A社アポイント準備", expanded=False):
        st.markdown("- 議事体裁作成\n- ターゲット課題整理")

    with st.expander("【進行中】A社提案準備", expanded=True):
        st.markdown("- 提案シナリオ作成（進行中）\n- 課題整理（待機）")

    with st.expander("【未着手】B社見積対応", expanded=False):
        st.markdown("- 案件概要ヒアリング\n- 構成提案作成")

    st.markdown("---")
    st.markdown("### タスク状況")
    st.markdown(
        '''
        <div style="background:#142C54; padding:12px; border-radius:8px; color:#fff;">
            <div><b>業務開始</b></div>
            <div style="margin:6px 0 6px 16px;">└ ● 提案シナリオ作成 - A社向け</div>
            <div style="margin:6px 0 6px 16px;">└ ○ 課題整理</div>
            <div style="margin:6px 0 6px 16px;">└ ○ 事例検索</div>
        </div>
        ''',
        unsafe_allow_html=True
    )
