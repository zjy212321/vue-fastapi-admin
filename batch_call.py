import datetime
import jwt
import time

def generate_token(user_id: int, expires_in_seconds: int = 3600) -> str:
    """
    生成 JWT Token
    :param user_id: 用户ID
    :param expires_in_seconds: Token 过期时间（秒）
    :return: 生成的 Token 字符串
    """
    # 1. 设置 Token 的过期时间
    expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)
    # 2. 构建 Payload（有效载荷）
    payload = {
        "user_id": user_id,
        "exp": expiration,  # 过期时间
        "iat": datetime.datetime.utcnow()  # 签发时间
    }
    # 3. 使用密钥和算法生成 Token
    token = jwt.encode(
        payload=payload,
        key="3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf",
        algorithm="HS256",
    )
    return token


import requests
import json

# 接口基础 URL（需要替换为实际部署的地址，如 http://localhost:8000）
BASE_URL = "http://127.0.0.1:9999/api/v1/case_ex/caseAnalysis"
BASE_URL_TEMP = "http://127.0.0.1:9999/api/v1/case_ex_temp/caseAnalysis"

# 替换为实际有效的认证令牌（如 JWT，从登录接口获取）
AUTH_TOKEN = "your-valid-auth-token"

def call_case_analysis_api(case_number: str, url: str):
    """
    调用按案件编号查询笔录的接口
    
    :param case_number: 案件编号（根据 CaseQueryRequest 模型实际字段调整）
    """
    # 构造请求头（包含认证信息和 JSON 格式声明）
    AUTH_TOKEN = generate_token(2)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"  # 假设使用 Bearer Token 认证
    }

    # 构造请求数据（需与 CaseQueryRequest 模型字段匹配）
    request_data = {
        "ajbh": case_number  # 示例字段，实际可能包含更多参数
    }

    try:
        # 发起 POST 请求
        response = requests.post(
            url=url,
            headers=headers,
            data=json.dumps(request_data)
        )

        # 处理响应
        if response.status_code == 200:
            print("请求成功！")
            print("响应数据:", response.json())
            return response.json()
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print("错误信息:", response.text)
            return None

    except requests.exceptions.RequestException as e:
        print(f"网络请求异常: {str(e)}")
        return None

# 示例调用（替换为实际案件编号）
if __name__ == "__main__":
    # for i in range(3):
    #     result = call_case_analysis_api(case_number="AJ20250524001")
    start_time = time.time()
    result = call_case_analysis_api(case_number="AJ20231010", url= BASE_URL_TEMP)
    print(time.time() - start_time)



# AJ20231010   单个案件的测试

    
