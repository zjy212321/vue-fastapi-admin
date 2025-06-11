
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter,Depends, Request
from fastapi.responses import JSONResponse
import os
from typing import List
from datetime import datetime
from app.settings import settings

from app.models.admin import User
from app.models.case import CaseAnalysisRequest,CaseAnalysisRequestRecord ,CaseAnalysisResultsPushed
from app.schemas.case import CaseQueryRequest,AnalysisResultRequest
from pydantic import BaseModel
import psycopg2
import requests 
import uuid
import asyncio

from fastapi_limiter.depends import RateLimiter
from app.core.dependency import RegisteredUserCheck
from tortoise.transactions import in_transaction
from tortoise.exceptions import DoesNotExist
import httpx
import json
from redis.asyncio import Redis
from redis.exceptions import RedisError
from functools import lru_cache

from loguru import logger as loguru_logger 

# 异步日志记录
loguru_logger.add("case.log", enqueue=True)  

router_ex = APIRouter() 

import asyncpg
from contextlib import asynccontextmanager

# 全局连接池单例
@asynccontextmanager
async def get_db_connection():
    if not hasattr(get_db_connection, "POOL"):
        get_db_connection.POOL = await asyncpg.create_pool(
            **settings.PG_DB_CONFIG,
            max_size=20  # 根据实际并发调整
        )
    async with get_db_connection.POOL.acquire() as conn:
        yield conn

# 全局复用Redis连接（单例模式），避免高频调用时重复创建连接
redis = Redis.from_url(
    settings.REDIS_URL,
    # "redis://redis:6379/0",
    decode_responses=True,
    max_connections=100,  # 最大连接数，避免资源耗尽
    socket_timeout=10,    # 套接字超时（秒）
    health_check_interval=30  # 连接健康检查间隔
)

# 全局信号量（或通过依赖注入共享）
@lru_cache(maxsize=1)  # 确保只创建一次
def get_global_semaphore():
    return asyncio.Semaphore(100)

# 定义后台处理任务
async def background_case_analysis_request_post(request_id, caller_identity_id, case_number,transcripts):
    records_to_create = []
    payloads_to_send = []
    # 处理每条笔录
    idx = 1
    for transcript in transcripts:
        task_id = str(uuid.uuid4())
        id_number = transcript.get('zjhm')
        gender, birth_date, age, household_registration = get_id_info(id_number)
        try:
            # 构造 payload
            payload = {
                "task_id": task_id,
                "transcript": transcript.get('xwnr'),
                "case_number": case_number,
                "name": transcript.get('ryxm'),
            }
            payloads_to_send.append(payload)
            is_analysis_complete = 0
        except Exception as e:
            is_analysis_complete = 1  
        # 收集所有记录对象
        records_to_create.append(CaseAnalysisRequestRecord(
            task_id=task_id,
            request_id=request_id,
            case_number=case_number,
            caller_identity_id=caller_identity_id,
            transcript_number=idx,
            transcript_content=transcript.get('xwnr'),
            ask_type=transcript.get('xwlx'),
            interviewee_name=transcript.get('ryxm'),
            id_number=id_number,
            gender=gender,
            age=age,
            birth_date=birth_date,
            household_registration=household_registration,
            is_analysis_complete=is_analysis_complete,
            transcript_time=transcript.get('kssj').strftime("%Y-%m-%d %H:%M:%S"),
            register_dep=transcript.get('zbdw_mc'),
        ))
        idx += 1
    # 一次性批量写入所有记录
    await CaseAnalysisRequestRecord.bulk_create(records_to_create)
    # 并行创建所有异步任务
    if payloads_to_send:
        # 获取全局信号量
        semaphore = get_global_semaphore()
        tasks = [
            _send_with_semaphore(settings.LLM_URL, payload, semaphore)
            for payload in payloads_to_send
        ]
        await asyncio.gather(*tasks)

# 外部通过按键编号查询笔录的接口
@router_ex.post("/caseAnalysis", summary="按案件编号查询笔录", 
    dependencies=[
        Depends(RegisteredUserCheck.is_registered),
        Depends(RateLimiter(identifier=RegisteredUserCheck.get_user_id, times=5, seconds=60))
    ]
)
async def case_analysis(
    data: CaseQueryRequest,
    user_id: int = Depends(RegisteredUserCheck.get_user_id)
):
    """
    接口处理流程：
    1. 生成唯一请求ID
    2. 执行数据库查询
    3. 处理查询结果
    4. 调用大模型接口
    5. 记录完整日志
    """
    request_id = str(uuid.uuid4())
    case_number = data.ajbh
    caller_identity_id = user_id
    
    # 初始化日志字段
    query_success = 0
    transcript_count = 0
    analysis_result_count = 0
    result_pushed = 0
    push_time = None
    is_completed = 0 
    request_type = "后台调用"

    # 2. 异步数据库查询
    try:
        async with get_db_connection() as conn:
            results = await conn.fetch(settings.QUERY_GET_BY_CASE_NUMBER, case_number)
            transcripts = [dict(row) for row in results]
            transcript_count = len(transcripts)
            query_success = 1
    except Exception as e:
        # 记录日志并抛出异常
        await CaseAnalysisRequest.create(
            request_id=request_id,
            case_number=case_number,
            caller_identity_id=caller_identity_id,
            query_success=query_success,
            transcript_count=transcript_count,
            analysis_result_count=analysis_result_count,
            result_pushed=result_pushed,
            push_time=push_time,
            is_completed=is_completed,
            request_type=request_type
        )
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {e}")
    
    # 3. 处理查询结果
    if transcript_count == 0:
        # 情况2：查询成功但无结果
        # 记录日志
        await CaseAnalysisRequest.create(
            request_id=request_id,
            case_number=case_number,
            caller_identity_id=caller_identity_id,
            query_success=query_success,
            transcript_count=transcript_count,
            analysis_result_count=analysis_result_count,
            result_pushed=result_pushed,
            push_time=push_time,
            is_completed=1,
            request_type=request_type
        )
        raise HTTPException(status_code=501, detail=f"未查询到相关笔录记录,案件编号: {case_number}")
    else:
        await CaseAnalysisRequest.create(
            request_id=request_id,
            case_number=case_number,
            caller_identity_id=caller_identity_id,
            query_success=query_success,
            transcript_count=transcript_count,
            analysis_result_count=analysis_result_count,
            result_pushed=result_pushed,
            push_time=push_time,
            is_completed=0,
            request_type=request_type
        )
        # 构造返回结果
        result = {
            "code": 200,
            "msg": f"查询到 {transcript_count} 条笔录,并成功接收任务,请静等分析结果推送",
            "data": {
                "ajbh": data.ajbh, # 按照公安厅接口标准要求,改成拼音首字母: 案件编号
                "jglj": "", # 按照公安厅接口标准要求,改成拼音首字母: 结果链接
            }
        }
        # 对算法服务发起的请求,放到后台任务处理
        asyncio.create_task(background_case_analysis_request_post(request_id, caller_identity_id, case_number,transcripts))
        return result


async def background_case_analysis_result_recieve(data: AnalysisResultRequest):
    try:
        # 2. 更新记录
        record = await CaseAnalysisRequestRecord.get(task_id=data.task_id)
        record.transcript_content_pp = data.transcript_content_pp
        record.analysis_result = data.analysis_result
        record.analysis_duration = data.analysis_duration
        record.is_analysis_complete = 1
        record.return_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        user_id = record.caller_identity_id
        case_number = record.case_number
        await record.save(update_fields=[
            'transcript_content_pp', 'analysis_result', 'analysis_duration',
            'is_analysis_complete', 'return_time'
        ])
        request_id = record.request_id

        # 将同一request_id的返回结果数量存入redis, 进行数量统计
        try:
            # 原子增加 Redis 中的计数器
            current_count = await redis.incr(f"request:{request_id}:analysis_result_count")
            # 如果是首次创建该键，则设置过期时间
            if current_count == 1:
                await redis.expire(f"request:{request_id}:analysis_result_count", 86400)
                # 从 MySQL 获取transcript_count 值,并缓存到 Redis
                case_request = await CaseAnalysisRequest.get(request_id=request_id)
                transcript_count = case_request.transcript_count
                await redis.set(f"request:{request_id}:transcript_count", transcript_count)
                await redis.expire(f"request:{request_id}:transcript_count", 86400)
            else:
                transcript_count = await redis.get(f"request:{request_id}:transcript_count")
                if transcript_count is None:
                    # 如果 Redis 中不存在该键，重新从 MySQL 获取并缓存
                    case_request = await CaseAnalysisRequest.get(request_id=request_id)
                    transcript_count = case_request.transcript_count
            transcript_count = int(transcript_count)
            # 检查是否所有分析结果都已接收
            if current_count < transcript_count:
                return  # 未完成，无需继续处理
            # 删除 Redis 中的临时键
            await redis.delete(f"request:{request_id}:analysis_result_count")
            await redis.delete(f"request:{request_id}:transcript_count")
        except RedisError as e:
            loguru_logger.error(f"Redis 操作失败: {e}")
            return

        # 4. 合并分析结果
        loguru_logger.info(f"合并分析结果")
        records_list = await CaseAnalysisRequestRecord.filter(request_id=request_id).values()
        analysis_results = []
        for re in records_list:
            try:
                bilu_header = {}
                r = json.loads(re["analysis_result"]) # json字符串转成 dict
                keys = ["interviewee_name", "gender", "age", "birth_date", "id_number","household_registration"]
                for key in keys:
                    bilu_header[key] = re.get(key, "")
                r["bilu_header"] = bilu_header
                analysis_results.append(r)
            except json.JSONDecodeError:
                analysis_results.append("")

        # 5. 调用外部接口
        code = 200
        message = "全部分析结果已成功接收"
        push_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        result_pushed = 1
        is_completed = 1

        request_body = {}

        try:
            user = await User.get(id=user_id)
            dept_id = user.dept_id
            if dept_id == 1:  # 杭州刑侦 && 云深科技
                from app.utils.caseExApi import yunshen_request_body_generate
                callback_url = settings.YUNSHEN_URL
                request_body = yunshen_request_body_generate(case_number, analysis_results)
                loguru_logger.info(json.dumps(request_body, ensure_ascii=False, indent=4))
                await _async_send_request(callback_url, request_body)
            else:
                code = 403
                message = "无效的部门id"
                push_time = None
                result_pushed = 0
        except (httpx.HTTPStatusError, httpx.RequestError, DoesNotExist) as e:
            code = 400
            message = "结果发送给客户失败"
            push_time = None
            result_pushed = 0

        # 6. 更新请求状态
        await CaseAnalysisRequest.filter(request_id=request_id).update(
            push_time=push_time,
            result_pushed=result_pushed,
            is_completed=is_completed
        )

        await CaseAnalysisResultsPushed.create(
            push_id = str(uuid.uuid4()),
            request_id=request_id,
            analysis_result_pushed=json.dumps(request_body, ensure_ascii=False, indent=4),
            push_time=push_time
        )

    except Exception as e:
        # 记录后台任务中的异常
        loguru_logger.error(f"后台处理失败: {e}")


@router_ex.post("/caseAnalysisResult", summary="接收笔录分析结果")
async def receive_analysis_result(data: AnalysisResultRequest):
    try:
        asyncio.create_task(background_case_analysis_result_recieve(data))
        loguru_logger.info(f"接收到大模型分析结果, 任务id: {data.task_id}")
        return {"code": 200, "message": f"大模型分析结果已接收，正在处理, task_id: {data.task_id}"}
    except Exception as e:
        loguru_logger.error(f"服务器内部错误, 任务id: {data.task_id}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

# 身份证号码解析
from id_validator import validator
def get_id_info(id_number):
    try:
        id_number = str(id_number).strip()
        if validator.is_valid(id_number):
            info = validator.get_info(id_number)
            gender = "男" if info["sex"] == 1 else "女"
            birth_date = info["birthday_code"].strftime("%Y-%m-%d")
            age = info["age"]
            household_registration = info["address"]
            return gender, birth_date, age, household_registration
        else:
            return None, None, None, None
    except Exception as e:
        return None, None, None, None

async def _async_send_request(url, payload):
    """使用 httpx 异步发送 POST 请求"""
    task_id = payload.get("task_id", "无")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=30.0)
        loguru_logger.info(f"调用成功, 任务id: {task_id}")
    except httpx.TimeoutException as te:
        loguru_logger.error(f"调用超时, 任务id: {task_id}, 错误: {str(te)}")
    except httpx.HTTPStatusError as hse:
        loguru_logger.error(f"HTTP状态错误, 任务id: {task_id}, 状态码: {hse.response.status_code}, 错误: {str(hse)}")
    except Exception as e:
        loguru_logger.error(f"未知错误, 任务id: {task_id}, 错误: {str(e)}")

async def _send_with_semaphore(url, payload, semaphore):
    async with semaphore:
        return await _async_send_request(url, payload)