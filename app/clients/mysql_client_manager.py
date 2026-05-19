from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.conf.app_config import app_config, DBConfig


# 并发时会有多个请求查询数据库，同步会阻塞整个线程，性能差，需要原生异步的数据库连接
class MySQLClientManager:
    def __init__(self, db_config: DBConfig):
        self.db_config = db_config
        self.engine = None
        self.session_factory = None

    def _get_url(self):
        return (f"mysql+asyncmy://{self.db_config.user}:"
                f"{self.db_config.password}"
                f"@{self.db_config.host}:{self.db_config.port}"
                f"/{self.db_config.database}?charset=utf8mb4")

    def init(self):
        self.engine = create_async_engine(self._get_url())
        self.session_factory = async_sessionmaker(self.engine)

    async def close(self):
        if self.engine:
            await self.engine.dispose()


dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)
meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)













