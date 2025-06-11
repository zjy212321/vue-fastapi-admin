import os
import typing

from pydantic_settings import BaseSettings
import redis.asyncio as redis # Use async Redis client


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day
    TORTOISE_ORM: dict = {
        "connections": {
            # SQLite configuration
            # "sqlite": {
            #     "engine": "tortoise.backends.sqlite",
            #     "credentials": {"file_path": f"{BASE_DIR}/db.sqlite3"},  # Path to SQLite database file
            # },
            # MySQL/MariaDB configuration
            # Install with: tortoise-orm[asyncmy]
            "mysql": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    # "host": "192.168.1.118",  # home
                    # "host": "192.168.207.225",  # binjiang gongan
                    "host": "mysql",  # work
                    "port": 3306,  # Database port
                    "user": "root",  # Database username
                    "password": "my-secret-pw",  # Database password
                    "database": "case",  # Database name
                },
            },
            # # PostgreSQL configuration
            # # Install with: tortoise-orm[asyncpg]
            # "postgres": {
            #     "engine": "tortoise.backends.asyncpg",
            #     "credentials": {
            #         "host": "192.168.18.106",  # Database host address
            #         "port": 5432,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # }, 
            # MSSQL/Oracle configuration
            # Install with: tortoise-orm[asyncodbc]
            # "oracle": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 1433,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
            # SQLServer configuration
            # Install with: tortoise-orm[asyncodbc]
            # "sqlserver": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 1433,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
        },
        "apps": {
            "models": {
                # 特别说明: 在存在多个数据库连接时，即使设置了default_connection，仍需在事务操作中显式指定connection_name='mysql'以消除歧义。所以暂时删除其他数据库
                "models": ["app.models","app.models.case","aerich.models"],
                # "models": ["app.models.admin","app.models.base","app.models.enums", "aerich.models"],
                "default_connection": "mysql",
            },

        },
        "use_tz": False,  # Whether to use timezone-aware datetimes
        "timezone": "Asia/Shanghai",  # Timezone setting
    }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    QUERY_GET_BY_CASE_NUMBER: str = """
        SELECT 
            a.id, 
            a.xwlx, 
            a.xwnr, 
            a.xwcs, 
            b.bllx,
            b.ywbh,
            b.ywmc,
            b.ajlx,
            b.zbdw_mc,
            b.ryxm,  
            b.zjhm  
        FROM 
            gg_xxwbl a 
        JOIN 
            gg_blxx b 
            ON a.id = b.zjz 
            AND b.blbm = 'gg_xxwbl'
            AND b.ywbh = $1
    """ 
    # 临时业务需求
    QUERY_GET_BY_TEMP: str = """
        SELECT 
            a.id, 
            a.xwlx, 
            a.xwnr, 
            a.xwcs, 
            b.bllx,
            b.ywbh,
            b.ywmc,
            b.ajlx,
            b.zbdw_mc,
            b.ryxm,  
            b.zjhm,
            b.kssj
        FROM 
            gg_xxwbl a 
        JOIN 
            gg_blxx b 
            ON a.id = b.zjz 
            AND b.blbm = 'gg_xxwbl'
            and (b.ywmc like '%诈骗%' or b.ywmc like '%被骗案%')
            and b.kssj >= '2025-03-01'
            and b.kssj <= '2025-03-31'
        ORDER BY a.id
        LIMIT $1 OFFSET $2;
    """ 

    PG_DB_CONFIG:dict = {
        # "host": "192.168.1.118",  # home
        "host": "postgres",  # work
        # "host": "192.168.207.225",  # binjiang gongan
        "port": 5432,  # Database port
        "user": "postgres",  # Database username
        "password": "112233",  # Database password
        "database": "zfba_zd"  # Database name
    }

    # 核心业务需求用的算法服务接口
    LLM_URL:str = "http://192.168.1.118:8084/extract/" 
    # 临时业务需求用的算法服务接口
    LLM_URL_TEMP:str = "http://192.168.1.118:8084/extract_temp/" 

    REDIS_URL:str = "redis://redis:6379/0"
    REDIS_CONNECTION: typing.ClassVar[redis.Redis] = redis.Redis(
        host = "redis",
        port=6379,
        db=0, # Assuming you have a DB setting for Redis
        encoding="utf-8",
        decode_responses=True # Important for string keys/values
    )
    # 调用杭州刑侦 云深科技时用的
    YUNSHEN_APP_ID:str = "0553aa9c-c0d7-4533-a123-01ad1062291c"
    YUNSHEN_SECRET:str = "7e1e5997-8fce-4280-98c5-194a55fc1554"
    YUNSHEN_URL:str = "http://41.196.13.32:8701/aifz/third/addCaseBiluResultTask"

settings = Settings()
