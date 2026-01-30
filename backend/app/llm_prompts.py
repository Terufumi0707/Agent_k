def gemini_extract_prompt(message: str) -> str:
    return (
        "次の文から情報を抽出してください。"
        "a_numberはA-12345形式、entry_idはENT-XXXX形式、"
        "work_changesは工事種別と変更希望日(YYYY-MM-DD)の配列です。"
        "存在しない項目はnullまたは空配列で返してください。\n\n"
        f"入力文: {message}\n"
        "出力例:\n"
        '{"a_number":"A-12345","entry_id":null,'
        '"work_changes":[{"work_type":"メイン回線_開通","desired_date":"2026-02-10"}]}'
    )
