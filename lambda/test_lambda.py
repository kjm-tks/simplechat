import json
from index import lambda_handler

# Lambda関数のテスト用イベントを作成
test_event = {
    "body": json.dumps({
        "message": "こんにちは、テストメッセージです",
        "conversationHistory": []
    })
}

# Lambda関数の実行をシミュレート
response = lambda_handler(test_event, None)

# レスポンスを表示
print("Lambda response status code:", response["statusCode"])
print("Lambda response body:", json.loads(response["body"]))