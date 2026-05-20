from elasticsearch import AsyncElasticsearch


class ValueESRepository:
    """
    es索引库
    """
    index_name = "data-agent-value"
    index_mappings = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value":
                {
                    "type": "text",
                 "analyzer": "ik_max_word",
                 "search_analyzer": "ik_max_word"
                 },
            "column_id": {"type": "keyword"}
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def ensure_index(self):
        if not await self.client.indices.exists(index=self.index_name):
            # 如果不存在，则创建一个索引库;
            await self.client.indices.create(
                index=self.index_name,
                mappings=self.index_mappings
            )



