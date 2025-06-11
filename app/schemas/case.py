from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import HttpUrl  # 用于 URL 格式校验

class CaseQueryRequest(BaseModel):
    # case_number 改成ajbh
    ajbh: str = Field(
        ...,  # 表示必填字段（无默认值）
        min_length=1,  # 字符串长度至少为1（非空）
        description="案件编号（非空字符串）"
    )

class AnalysisResultRequest(BaseModel):
    task_id: str = Field(..., min_length=1, description="任务ID（不能为空）")    
    transcript_content_pp: str
    analysis_result: str  # JSON格式字符串
    analysis_duration: float

class PGLoopSearch(BaseModel):
    page_size : int
    offset : int