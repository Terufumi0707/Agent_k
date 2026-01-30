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


def gemini_work_parse_prompt(message: str) -> str:
    return (
        "次の文から工事依頼の内容を抽出し、指定のJSONだけを返してください。"
        "operationは change/add/delete/confirm のいずれか、"
        "work_typesは正規化された工事種別名とconfidence(high/medium/low)の配列、"
        "dateはYYYY-MM-DD、date_inferredは年や月を推定した場合trueです。"
        "工事種別の正規名一覧: "
        "現地調査,付帯工事,アクセス工事,導通工事,事前配線,宅内工事,端末工事,"
        "切替工事,端末撤去,コム撤去,地域撤去,ケーブル撤去,PD撤去,DF現調,開通日。"
        "表記揺れや俗称は正規名に正規化してください。"
        "例: 現調→現地調査, 宅内→宅内工事, 端末→端末工事, 切り替え→切替工事。"
        "撤去だけの場合は撤去系候補を列挙しconfidenceを下げてください。"
        "年がない日付は直近の未来を推定してください。"
        "推定した場合はnotesに理由を簡潔に記載してください。\n\n"
        f"入力文: {message}\n"
        "出力例:\n"
        '{'
        '"operation":"change",'
        '"work_types":[{"name":"現地調査","confidence":"high"}],'
        '"date":"2026-02-05",'
        '"date_inferred":true,'
        '"notes":"年が明示されていないため直近の年を推定"'
        "}"
    )
