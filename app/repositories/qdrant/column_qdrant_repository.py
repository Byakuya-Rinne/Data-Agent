from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:
    # 定义集合名称
    collection_name = "data-agent-column"
    """
    向量数据库
    """

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        # 如果没有这个集合则创建，有则什么都丕做！
        if not await self.client.collection_exists(collection_name=self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=app_config.qdrant.embedding_size, distance=Distance.COSINE)
            )

    async def upsert(self, ids: list[str], embeddings: list[list[float]], payloads: list[ColumnInfo],
                     batch_size: int = 10):
        # 设zip函数对数据进行转换;ids=[1,2,3] embeddings=[张三,李四，王五] payloads=[18,20,23]
        # 1,张三，18 2，李四，20 3，王五，23
        zipped = list(zip(ids, embeddings, payloads))
        for i in range(0, len(zipped), batch_size):
            # 获取截取数据;
            batch = zipped[i:i + batch_size]
            # PointStruct(id vector payload)
            points = [PointStruct(id=id, vector=embedding, payload=asdict(payload)) for id, embedding, payload in batch]
            # 调用客户端向，向量数据库中添加数据.
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )




