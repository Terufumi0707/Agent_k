def mock_reply(user_text: str) -> str:
    text = user_text.lower().strip()
    if "提案" in text or "準備" in text:
        return (
            "承知しました。A社向けの提案準備を開始します。\n"
            "- タスク：シナリオ構築\n"
            "- 状況：進行中\n\n"
            "次にどのタスクを実行しますか？"
        )
    if "日程" in text or "候補" in text:
        return (
            "現在の空き日程：\n"
            "- 11/12 (水)\n- 11/14 (金)\n- 11/18 (火)\n\n"
            "※ 連日実行は禁止されています。"
        )
    if "ok" in text or "はい" in text or "進め" in text:
        return "了解しました。進捗をタスクボードに反映します。"
    return f"「{user_text}」ですね。関連タスクを検索中です…"
