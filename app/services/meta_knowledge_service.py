import uuid
from pathlib import Path

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from loguru import logger
from omegaconf import OmegaConf

from app.conf.meta_config import MetaConfig, MetricConfig
from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.entities.value_info import ValueInfo
from app.repositories.es.value_es_repository import ValueESRepository
from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMySQLRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    def __init__(self,
                 meta_mysql_repository: MetaMySQLRepository,
                 dw_mysql_repository: DWMySQLRepository,
                 column_qdrant_repository: ColumnQdrantRepository,
                 embedding_client: HuggingFaceEndpointEmbeddings,
                 value_es_repository: ValueESRepository,
                 metric_qdrant_repository: MetricQdrantRepository):

        self.meta_mysql_repository = meta_mysql_repository
        self.dw_mysql_repository = dw_mysql_repository
        self.column_qdrant_repository = column_qdrant_repository
        self.embedding_client = embedding_client
        self.value_es_repository = value_es_repository
        self.metric_qdrant_repository = metric_qdrant_repository


    async def _save_tables_to_meta_db(self, meta_config: MetaConfig):
        # 保存五个表到table_info：
        # id(name)  name    role    description
        # column_info:
        # id(表名+列名) name    type    role    examples    description alias   table_id

        # class ColumnConfig:
        #     name: str
        #     role: str
        #     description: str
        #     alias: list[str]
        #     sync: bool

        # class TableConfig:
        #     name: str
        #     role: str
        #     description: str
        #     columns: list[ColumnConfig]

        table_infos: list[TableInfo] = []
        column_infos: list[ValueInfo] = []

        for table in MetaConfig.tables:
            table_info = TableInfo(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description
            )
            table_infos.append(table_info)
            field_types: dict[str, str] = await self.dw_mysql_repository.get_column_types(table)

            for column in table.columns:
                example_values: list[str] = self.dw_mysql_repository.get_column_values(table.name, column.name)
                column_info = ColumnInfo(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=field_types.get(column.name),
                    role=column.role,
                    examples=example_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=f"{table.name}"
                )
                column_infos.append(column_info)

        async with self.meta_mysql_repository.session.begin():
            #   把table_infos插入到table_info表
            await self.meta_mysql_repository.save_table_infos(table_infos)

            #   把value_infos插入到table_info表
            await self.meta_mysql_repository.save_table_infos(column_infos)
        return column_infos


    async def _save_column_info_to_qdrant(self, column_infos: list[ColumnInfo]):
        # 1.先判断是否有集合存在！
        await self.column_qdrant_repository.ensure_collection()
        # 2.把value_infos的每一行插入qdrant
        # 向量化column_info表的name，description，alias中的每一个值

        # 准备要向量化的数据
        points = []
        for value_info in column_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": value_info.name,
                "payload":value_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": value_info.description,
                "payload":value_info
            })
            for alia in value_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload":value_info
                })
        ids = [point["id"] for point in points]
        embedding_tests = [point["embedding_text"] for point in points]
        payloads = [point["payload"] for point in points]
        batch_size = 10

        # 把embedding_tests向量化
        embeddings = []
        for i in range(0, len(embedding_tests), batch_size):
            batch = embedding_tests[i:i + batch_size]
            embedding_text = await self.embedding_client.aembed_documents(batch)
            embeddings.extend(embedding_text)

        # 把向量化完的结果存入qdrant
        await self.column_qdrant_repository.upsert(ids, embeddings, payloads)



    async def _save_value_info_to_es(self, meta_config: MetaConfig, column_infos: list[ColumnInfo]):
        # 先判断是否有索引库！
        await self.value_es_repository.ensure_index()

        # 读取配置config，没有原始数据
        column_sync: dict[str,bool] = {}
        for table in meta_config.tables:
            for column in table.columns:
                # 拿到了"哪些字段需要存"的信息，没有原始数据
                # "dim_region.region_id": False,
                # "dim_region.province": True,
                # ......
                column_sync[f"{table.name}.{column.name}"] = column.sync

        # 查这些列的数据库内真实数据（column_infos）存入es
        value_infos: list[ValueInfo] = []
        for column_info in column_infos:
            if column_sync[f"{column_info.table_id}.{column_info.name}"]:
                table_name = column_info.table_id
                column_name = column_info.name
                # 取原dw表一列所有真实取值
                column_values: list[str] = await self.dw_mysql_repository.get_column_values(table_name, column_name, 10000)

                for column_value in column_values:
                    value_info = ValueInfo(
                        id=f"{column_info.id}.{column_value}",
                        value=column_value,
                        column_id=column_info.id
                    )
                    value_infos.append(value_info)
        await self.value_es_repository.index(value_infos)

    async def _save_metrics_to_meta_db(self, meta_config: MetaConfig):

        metric_infos: list[MetricInfo] = []
        column_metrics: list[ColumnMetric] = []
        for metrics in meta_config.metrics:
            metric_info: MetricInfo = MetricInfo(
                id=metrics.name,
                name=metrics.name,
                description=metrics.description,
                relevant_columns=metrics.relevant_columns,
                alias=metrics.alias
            )
            metric_infos.append(metric_info)

            for relevant_column in metrics.relevant_columns:
                column_metric: ColumnMetric = ColumnMetric(
                    column_id=relevant_column,
                    metric_id=metrics.name
                )
                column_metrics.append(column_metric)
        async with self.meta_mysql_repository.session.begin():
            # 操作数据库：
            await self.meta_mysql_repository.save_metric_infos(metric_infos)
            await self.meta_mysql_repository.save_column_metrics(column_metrics)

        return metric_infos



    async def _save_metric_info_to_qdrant(self, metric_infos: list[MetricInfo]):
        await self.metric_qdrant_repository.ensure_collection()
        # name description alias
        points = []
        for metric_info in metric_infos:
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.name,
                "payload":metric_info
            })
            points.append({
                "id": uuid.uuid4(),
                "embedding_text": metric_info.description,
                "payload":metric_info
            })
            for alia in metric_info.alias:
                points.append({
                    "id": uuid.uuid4(),
                    "embedding_text": alia,
                    "payload":metric_info
                })

        ids: list[str] = []
        embedding_text: list[str] = []
        payloads = []

        for point in points:
            ids.append(point["id"])
            embedding_text.append(point["embedding_text"])
            payloads.append(point["payload"])

        # 每次处理几条数据;
        batch_size = 10
        embeddings = []
        # 调用绑定模型向量化
        for i in range(0, len(embedding_text), batch_size):
            batch = embedding_text[i:i + batch_size]
            batch_embeddings = await self.embedding_client.aembed_documents(batch)
            embeddings.extend(batch_embeddings)

        await self.metric_qdrant_repository.upsert(ids, embeddings, payloads)



    async def build(self, config_path: Path):
        # 1.先读取配置文件 meta_config.yaml
        context = OmegaConf.load(config_path)
        structured = OmegaConf.structured(MetaConfig)
        merge = OmegaConf.merge(structured, context)
        meta_config: MetaConfig = OmegaConf.to_object(merge)

        if meta_config.tables:
            column_infos: list[ColumnInfo] = await self._save_tables_to_meta_db(meta_config)
            logger.info("保存数据到meta数据库中成功！")
            # # 2.1.1 将字段信息保存到向量数据库
            await self._save_column_info_to_qdrant(column_infos)
            logger.info("保存数据到qdrant向量数据库中成功！")
            # # 2.1.2 将字段值保存到es中
            # # 将字段的值保存到es中. 字段从：column_infos 值：metaConfig配置文件有关系！
            await self._save_value_info_to_es(meta_config, column_infos)
            logger.info("保存数据到es中成功！")
        if meta_config.metrics:
            # 2.2 保存指标信息:metric_info column_metric meta_config.yaml
            metric_infos: list[MetricInfo] = await self._save_metrics_to_meta_db(meta_config)
            logger.info("保存数据到meta数据库中成功！")
            # 2.2.1 保存指标信息到向量数据库
            await self._save_metric_info_to_qdrant(metric_infos)
            logger.info("保存数据到qdrant向量数据库中成功！")










