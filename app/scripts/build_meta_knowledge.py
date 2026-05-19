from pathlib import Path

from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.es_client_manager import es_client_manager
from app.clients.mysql_client_manager import dw_mysql_client_manager, meta_mysql_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from loguru import logger

async def build(config_path: Path):
    logger.info(f"当前配置文件为：{config_path}")

    # 获取各个客户端连接
    embedding_client = embedding_client_manager.es_client()
    es_client = es_client_manager.es_client()
    dw_mysql_client = dw_mysql_client_manager.dw_mysql_client()
    meta_mysql_client = meta_mysql_client_manager.meta_mysql_client()
    qdrant_client = qdrant_client_manager.qdrant_client()







# 写入元数据库（MySQL meta 库）

# 构建向量索引和全文索引


if __name__ == '__main__':
    pass

