# lambda/index.py
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import socket

# FastAPI接続用の設定
# ルートエンドポイントを試す
FASTAPI_URL = "https://502f-34-105-47-232.ngrok-free.app"
# タイムアウト設定（秒）
TIMEOUT = 60

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # FastAPIにリクエストを送信
        try:
            # まずは利用可能なエンドポイントを確認
            print("Checking available endpoints at FastAPI server...")
            
            # ルートエンドポイントにアクセスしてサーバー情報を取得
            root_req = urllib.request.Request(
                FASTAPI_URL,
                method="GET"
            )
            
            # タイムアウト設定を適用
            socket.setdefaulttimeout(TIMEOUT)
            
            try:
                with urllib.request.urlopen(root_req) as response:
                    root_response = response.read().decode('utf-8')
                    print(f"Root endpoint response: {root_response}")
                    
                    # FastAPIサーバーの情報を出力
                    try:
                        root_data = json.loads(root_response)
                        print(f"Server info: {json.dumps(root_data)}")
                    except json.JSONDecodeError:
                        print("Root response is not valid JSON")
            except Exception as e:
                print(f"Error checking root endpoint: {str(e)}")
            
            # /docsエンドポイントを確認してみる（Swagger UIが利用可能か）
            try:
                print("Checking /docs endpoint...")
                docs_req = urllib.request.Request(
                    f"{FASTAPI_URL}/docs",
                    method="GET"
                )
                with urllib.request.urlopen(docs_req) as response:
                    print(f"Docs endpoint status: {response.status}")
                    print("Swagger UI appears to be available at /docs")
            except Exception as e:
                print(f"Swagger UI not available: {str(e)}")
            
            # 実際のリクエストを送信
            # FastAPIのURLに/generateを追加してみる
            generate_url = f"{FASTAPI_URL}/generate"
            print(f"Attempting to access generate endpoint at: {generate_url}")
            
            request_data = {
                "prompt": message,
                "max_new_tokens": 512,
                "do_sample": True,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            req = urllib.request.Request(
                generate_url,
                data=json.dumps(request_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method="POST"
            )
            
            try:
                with urllib.request.urlopen(req) as response:
                    response_text = response.read().decode('utf-8')
                    print(f"Generate endpoint raw response: {response_text}")
                    
                    # JSONレスポンスを解析
                    fastapi_response = json.loads(response_text)
                    
                    # 'generated_text'フィールドからアシスタント応答を取得
                    model_response = fastapi_response.get('generated_text', '')
                    
                    # 会話履歴を更新
                    messages.append({
                        "role": "assistant",
                        "content": model_response
                    })
                    
                    # 成功レスポンスを返却
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                            "Access-Control-Allow-Methods": "OPTIONS,POST"
                        },
                        "body": json.dumps({
                            "success": True,
                            "response": model_response,
                            "conversationHistory": messages
                        })
                    }
            except urllib.error.HTTPError as e:
                print(f"Generate endpoint error: {e.code} - {e.reason}")
                
                # 別のエンドポイントを試してみる
                # 例えば、FastAPIコードではgenerateが定義されていますが、
                # 実際にはchatなどの名前になっている可能性も
                alternative_endpoints = ["/chat", "/completion", "/predict", "/inference"]
                
                for endpoint in alternative_endpoints:
                    alt_url = f"{FASTAPI_URL}{endpoint}"
                    print(f"Trying alternative endpoint: {alt_url}")
                    
                    alt_req = urllib.request.Request(
                        alt_url,
                        data=json.dumps(request_data).encode('utf-8'),
                        headers={'Content-Type': 'application/json'},
                        method="POST"
                    )
                    
                    try:
                        with urllib.request.urlopen(alt_req) as alt_response:
                            alt_response_text = alt_response.read().decode('utf-8')
                            print(f"Alternative endpoint response: {alt_response_text}")
                            
                            try:
                                alt_data = json.loads(alt_response_text)
                                print(f"Alternative endpoint data: {json.dumps(alt_data)}")
                                
                                # 有効なレスポンスが見つかった場合、それを使用
                                model_response = alt_data.get('generated_text', 
                                                             alt_data.get('response',
                                                                         alt_data.get('text', 
                                                                                      alt_response_text)))
                                
                                # 会話履歴を更新
                                messages.append({
                                    "role": "assistant",
                                    "content": model_response
                                })
                                
                                # 成功レスポンスを返却
                                return {
                                    "statusCode": 200,
                                    "headers": {
                                        "Content-Type": "application/json",
                                        "Access-Control-Allow-Origin": "*",
                                        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                                        "Access-Control-Allow-Methods": "OPTIONS,POST"
                                    },
                                    "body": json.dumps({
                                        "success": True,
                                        "response": model_response,
                                        "conversationHistory": messages
                                    })
                                }
                            except json.JSONDecodeError:
                                print(f"Alternative endpoint response is not valid JSON")
                                continue
                    except Exception as alt_e:
                        print(f"Alternative endpoint error: {str(alt_e)}")
                        continue
                
                # 全ての代替エンドポイントを試してもうまくいかない場合
                error_message = (f"推論エンドポイントが見つかりません。FastAPIサーバーの設定を確認してください。"
                                f"(HTTP Error: {e.code} - {e.reason})")
                raise Exception(error_message)
                
        except Exception as e:
            print(f"Error communicating with FastAPI: {str(e)}")
            
            # シンプルなモックレスポンスを返す（実際の環境ではコメントアウト）
            mock_response = f"FastAPIサーバーに接続できませんでした。エラー: {str(e)}"
            messages.append({
                "role": "assistant",
                "content": mock_response
            })
            
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({
                    "success": False,
                    "error": str(e),
                    "mock_response": mock_response,  # デバッグ用
                    "conversationHistory": messages  # 会話履歴を含める
                })
            }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }