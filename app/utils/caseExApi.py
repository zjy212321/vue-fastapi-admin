# 外部接口的对应header, body的制作过程
import secrets
import string
import time
import hashlib
from app.settings.config import settings
from collections import Counter
import json




def generate_nonce(length: int = 6) -> str:
    """
    生成一个指定长度的随机字符串，仅包含大小写字母和数字。
    :param length: 字符串长度，默认为 6
    :return: 生成的随机字符串
    """
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(secrets.choice(characters) for _ in range(length))

def yunshen_request_signparam_generate(case_number : str):
    # 1. 生成签名参数
    timestamp = int(time.time() * 1000)  # 毫秒时间戳
    nonce = generate_nonce()  # 随机字符串
    sign_str = f"{timestamp}{settings.YUNSHEN_APP_ID}{case_number}{nonce}{settings.YUNSHEN_SECRET}"
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

    # 2. 构建 signParam 字典
    sign_param = {
        'appId': settings.YUNSHEN_APP_ID,
        'ts': timestamp,
        'nonce': nonce,
        'sign': sign
    }
    return sign_param

def merge_analysis_results(analysis_results):
    merged_result = {}
    # 遍历所有分析结果
    type_dict = {}
    for item in analysis_results:
        # 校验数据结构
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            # 初始化 merged_result 中的键（如果不存在）
            if key not in merged_result:
                merged_result[key] = []
            if key != "ajfl": # 案件类型
                if isinstance(value, list):
                    merged_result[key].extend(value)
                else:
                    merged_result[key].append(value)
            else:
                try:
                    for personinfo in item['victimPersonInfo']:
                        name = personinfo.get("name", None)
                        if name and name.strip() !=  "无":
                            if name not in type_dict:
                                type_dict[name] = []
                            type_dict[name].append(value)
                        else:
                            continue
                except:
                    continue

    # 提取每个名字下,类型最多的
    most_common_types = []
    for name,values in type_dict.items():
        counter = Counter()
        for d in values:
            try:
                key_str = json.dumps(d, sort_keys=True)
                counter[key_str] += 1
            except:
                continue
        if counter:
            most_common_key_str, _ = counter.most_common(1)[0]
            most_common_dict = json.loads(most_common_key_str)
            most_common_types.append({"name":name, "type" : most_common_dict})
    merged_result["ajfl"] = most_common_types

    # 将笔录原文消除,不返回
    merged_result.pop("content",None)
    
    return merged_result

def yunshen_request_body_generate(case_number : str, analysis_result : list):
    sign_param = yunshen_request_signparam_generate(case_number)
    merged_result = merge_analysis_results(analysis_result)
    # 1. 构建请求体
    request_body = {
        'signParam': sign_param,
        'caseNumber': case_number,
        'originalTextArr': [],
        'result': merged_result
    }
    return request_body
