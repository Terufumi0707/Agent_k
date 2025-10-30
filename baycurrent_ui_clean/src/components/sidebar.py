import matplotlib.pyplot as plt
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
    st.caption("LangGraph のワークフロー進行状況")

    workflow_path: list[str] = st.session_state.get("workflow_path", [])
    classification: str = st.session_state.get("workflow_classification", "other")

    nodes = ["START", "classify_intent", "call_schedule_api", "END"]
    node_labels = {
        "START": "Start",
        "classify_intent": "意図判定",
        "call_schedule_api": "API 呼び出し",
        "END": "End",
    }
    positions = {
        "START": (0.5, 0.92),
        "classify_intent": (0.5, 0.68),
        "call_schedule_api": (0.5, 0.44),
        "END": (0.5, 0.2),
    }
    edges = [
        ("START", "classify_intent"),
        ("classify_intent", "call_schedule_api"),
        ("call_schedule_api", "END"),
        ("classify_intent", "END"),
    ]

    full_path = ["START", *workflow_path]
    if classification == "schedule_change":
        full_path.append("END")
    elif workflow_path:
        full_path.append("END")

    visited_edges = {edge for edge in zip(full_path[:-1], full_path[1:])}
    active_node = workflow_path[-1] if workflow_path else "START"

    fig, ax = plt.subplots(figsize=(3.4, 4.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    for edge in edges:
        start, end = edge
        start_pos = positions[start]
        end_pos = positions[end]
        color = "#2A6CC6" if edge in visited_edges else "#C6D2EB"
        ax.annotate(
            "",
            xy=end_pos,
            xytext=start_pos,
            arrowprops=dict(arrowstyle="->", color=color, linewidth=2),
        )

    for node in nodes:
        x, y = positions[node]
        is_active = node == active_node
        is_visited = node in full_path
        facecolor = "#142C54" if is_active else "#2A6CC6" if is_visited else "#E0E7F5"
        text_color = "#FFFFFF" if is_active or is_visited else "#142C54"
        circle = plt.Circle((x, y), 0.07, facecolor=facecolor, edgecolor="#0B1E3F", linewidth=1.2)
        ax.add_patch(circle)
        ax.text(x, y, node_labels[node], ha="center", va="center", fontsize=9, color=text_color)

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    if workflow_path:
        st.markdown(f"**現在のステップ:** {node_labels.get(active_node, active_node)}")
    else:
        st.markdown("**現在のステップ:** Start")
