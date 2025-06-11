
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter,Depends,Query
from fastapi.responses import JSONResponse
import os
from typing import List
from datetime import datetime
from fastapi_limiter.depends import RateLimiter
from app.core.dependency import  AuthControl
from app.core.ctx import CTX_USER_ID
from app.settings import settings


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


# 配置项
UPLOAD_DIR = "uploads"  # 文件保存目录
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.doc'}  # 允许的文件扩展名
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB 文件大小限制

# 初始化上传目录
os.makedirs(UPLOAD_DIR, exist_ok=True)
router = APIRouter()


def is_allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in ALLOWED_EXTENSIONS]

@router.post("/upload", summary="上传笔录文件")
async def upload_files(files: List[UploadFile] = File(...)):
    """文件上传接口，支持同时上传多个文件"""
    saved_files = []
    
    for file in files:
        # 校验文件类型
        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.filename}。仅支持 {ALLOWED_EXTENSIONS} 类型"
            )
        
        # 校验文件大小（通过读取内容判断，适用于小文件）
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件 {file.filename} 超过大小限制（最大10MB）"
            )
        
        # 保存文件
        save_path = os.path.join(UPLOAD_DIR, file.filename)
        try:
            with open(save_path, "wb") as buffer:
                buffer.write(content)
            saved_files.append(content.decode('utf-8'))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"保存文件 {file.filename} 失败: {str(e)}"
            )
    
    return {
        "code": 200,
        "message": f"成功上传 {len(saved_files)} 个文件",
        "data": saved_files
    }

@router.get("/get-by-key", summary="通过案件编号查询笔录",
    dependencies=[
        Depends(AuthControl.is_authed),
        Depends(RateLimiter(identifier=CTX_USER_ID.get(), times=10, seconds=60))
    ]
)
async def get_case_by_key(
    caseNumber: str = Query(..., description="案件编号")
):
    user_id = CTX_USER_ID.get()
    try:
        async with get_db_connection() as conn:
            results = await conn.fetch(settings.QUERY_GET_BY_CASE_NUMBER, caseNumber)
            transcripts = [dict(row) for row in results]
        data = []
        for transcript in transcripts:
            data.append(transcript.get('xwnr'))
        res = {
            "code": 200,
            "message": "案件查询成功",
            "data": data
        }
        return res

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")


