from fastapi import APIRouter

from .case import router
from .case_ex import router_ex
from .case_ex_temp import router_ex_temp

case_router = APIRouter()
case_router.include_router(router, tags=["笔录分析模块"])

case_router_ex = APIRouter()
case_router_ex.include_router(router_ex, tags=["笔录分析模块-外部接口"])

case_router_ex_temp = APIRouter()
case_router_ex_temp.include_router(router_ex_temp, tags=["笔录分析模块-外部接口-临时业务需求"])

 
__all__ = ["case_router","case_router_ex", "case_router_ex_temp"]
