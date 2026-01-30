def gemini_extract_prompt(message: str) -> str:
    return (
        "次の文から情報を抽出してください。"
        "a_numberは英字2文字+数字10桁の形式、entry_idも英字2文字+数字10桁の形式、"
        "work_changesは工事種別と変更希望日(YYYY-MM-DD)の配列です。"
        "存在しない項目はnullまたは空配列で返してください。\n\n"
        f"入力文: {message}\n"
        "出力例:\n"
        '{"a_number":"AA1234567890","entry_id":null,'
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


def build_dialogue_prompt(state: dict) -> str:
    return (
        "あなたは社内向け業務システムの対話エージェントです。"
        "目的はA番号またはエントリ番号・工事種別・対象日付を揃えることですが、"
        "入力検証やエラー返却は禁止です。"
        "不足や曖昧さがあれば、次に聞くべき最重要事項を1つ選び、"
        "丁寧で自然な日本語の質問を返してください。"
        "すべて十分な確度で揃った場合は確認メッセージを返してください。"
        "A番号やエントリ番号の形式やルールは説明しないでください。"
        "工事種別の正規名一覧: "
        "現地調査,付帯工事,アクセス工事,導通工事,事前配線,宅内工事,端末工事,"
        "切替工事,端末撤去,コム撤去,地域撤去,ケーブル撤去,PD撤去,DF現調,開通日。"
        "日付は文脈から妥当な日を推定し、内部的にYYYY-MM-DD形式を意識してください。"
        "出力は必ずJSONのみで、次の形式を守ってください:\n"
        "{"
        '"status":"need_more_info|completed",'
        '"missing_fields":["..."],'
        '"questions":["..."],'
        '"assistant_message":"..."\n'
        "}\n\n"
        "現在の状態:\n"
        f"{state}\n"
    )


def build_autonomous_prompt(state: dict) -> str:
    return (
        "あなたは社内向け業務システムの自律型コミュニケーションエージェントです。"
        "目的はA番号・工事種別・対象日付を揃えることです。"
        "不足や曖昧さがあれば次に聞くべき質問文を1つだけ返してください。"
        "質問文は丁寧で自然な日本語で、ルールや形式は説明しないでください。"
        "ユーザーに対して『エラー』『不正』『条件違反』という言葉は使わないでください。"
        "工事種別の正規名一覧: "
        "現地調査,付帯工事,アクセス工事,導通工事,事前配線,宅内工事,端末工事,"
        "切替工事,端末撤去,コム撤去,地域撤去,ケーブル撤去,PD撤去,DF現調,開通日。"
        "日付は文脈から妥当な日を推定し、内部的にYYYY-MM-DD形式に正規化してください。"
        "出力は必ずJSONのみで、次の形式を守ってください:\n"
        "{"
        '"a_number":string|null,'
        '"work_types":[{"name":string,"confidence":"high|medium|low"}],'
        '"date":string|null,'
        '"date_inferred":boolean,'
        '"question":string"\n'
        "}\n\n"
        "現在の状態:\n"
        f"{state}\n"
    )
