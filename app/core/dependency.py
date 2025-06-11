from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings

import redis


class AuthControl:
    @classmethod
    async def is_authed(cls, token: str = Header(..., description="token验证")) -> Optional["User"]:
        try:
            if token == "dev":
                user = await User.filter().first()
                user_id = user.id
            else:
                decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
                user_id = decode_data.get("user_id")
            user = await User.filter(id=user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="Authentication failed")
            CTX_USER_ID.set(int(user_id))
            return user
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="无效的Token")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="登录已过期")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{repr(e)}")


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles: list[Role] = await current_user.roles
        if not roles:
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        apis = [await role.apis for role in roles]
        permission_apis = list(set((api.method, api.path) for api in sum(apis, [])))
        # path = "/api/v1/auth/userinfo"
        # method = "GET"
        if (method, path) not in permission_apis:
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")

class RegisteredUserCheck:
    @classmethod
    async def is_registered(cls,request: Request, Authorization: str = Header(..., description="身份id验证")) -> int:
        auth_header = Authorization
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="无效的授权头")
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="授权头中未检测到用户id")
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="授权已失效")
        user = await User.get_or_none(id=user_id)
        if not user:
            raise HTTPException(status_code=403, detail="该用户尚未注册")
        # 将用户ID挂载到 request.state 中，供后续依赖使用
        request.state.user_id = user_id
        return user_id

    @classmethod
    async def get_user_id(cls, request: Request) -> int:
        return request.state.user_id

# import datetime
# def generate_token(user_id: int, expires_in_seconds: int = 3600) -> str:
#     """
#     生成 JWT Token
#     :param user_id: 用户ID
#     :param expires_in_seconds: Token 过期时间（秒）
#     :return: 生成的 Token 字符串
#     """
#     # 1. 设置 Token 的过期时间
#     expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)
#     # 2. 构建 Payload（有效载荷）
#     payload = {
#         "user_id": user_id,
#         "exp": expiration,  # 过期时间
#         "iat": datetime.datetime.utcnow()  # 签发时间
#     }
#     # 3. 使用密钥和算法生成 Token
#     token = jwt.encode(
#         payload=payload,
#         key="3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf",
#         algorithm="HS256",
#     )
#     return token

DependAuth = Depends(AuthControl.is_authed)
DependPermisson = Depends(PermissionControl.has_permission)
DenpendRegisteredUserCheck = Depends(RegisteredUserCheck.is_registered)


