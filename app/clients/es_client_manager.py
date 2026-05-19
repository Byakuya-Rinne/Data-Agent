import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config


class ESClientManager:
    def __init__(self, es_config: ESConfig):
        self.es_config = es_config
        self.client: Optional[AsyncElasticsearch] = None
    # Optional 是 Python 类型提示中的一个工具，表示 “这个变量可以是指定类型的值，也可以是 None”

    def _get_url(self):
        return f"http://{self.es_config.host}:{self.es_config.port}"

    def init(self):
        self.client = AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        await self.client.close()

es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':

    async def test():
        es_client_manager.init()
        client = es_client_manager.client

        if await client.indices.exists(index="test_index"):
            await client.indices.delete(index="test_index")

        #  创建索引
        await client.indices.create(
            index="test_index",
            mappings={
                "dynamic": False,
                "properties":{
                    "test1":{
                        "type":"text",
                        "analyzer":"ik_max_word"
                    },
                    "test2":{
                        "type":"keyword"
                    }
                }
            }
        )

        #  插入文档
        await client.bulk(
            operations=[
                {
                    "index":{
                        "_index":"test_index",
                    }
                },
                {
                    "test1":"IPhone 114514 Pro Max",
                    "test2":"1919810"
                }
            ]
        )
        await client.indices.refresh(index="test_index")
        # match 查询
        result = await es_client_manager.client.search(
            index="test_index",
            query={
                "match": {
                    "test1": "114514"
                }
            }
        )
        print(result)
        # {
        #   "took": 1,
        #   "timed_out": false,
        #   "_shards": {
        #     "total": 1,
        #     "successful": 1,
        #     "skipped": 0,
        #     "failed": 0
        #   },
        #   "hits": {
        #     "total": {
        #       "value": 1,
        #       "relation": "eq"
        #     },
        #     "max_score": 0.2876821,
        #     "hits": [
        #       {
        #         "_index": "test_index",
        #         "_id": "fLz6Op4B9tSYNmHILZ8w",
        #         "_score": 0.2876821,
        #         "_source": {
        #           "test1": "IPhone 114514 Pro Max",
        #           "test2": "1919810"
        #         }
        #       }
        #     ]
        #   }
        # }
        for hit in result["hits"]["hits"]:
            print(f"  得分: {hit['_score']}, 数据: {hit['_source']}")


        await es_client_manager.client.close()



    asyncio.run(test())







