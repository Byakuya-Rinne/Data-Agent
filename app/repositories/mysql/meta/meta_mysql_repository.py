from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.column_info import ColumnInfo
from app.entities.column_metric import ColumnMetric
from app.entities.metric_info import MetricInfo
from app.entities.table_info import TableInfo
from app.models.table_info_mysql import TableInfoMySQL
from app.repositories.mysql.meta.mappers.column_info_mapper import ColumnInfoMapper
from app.repositories.mysql.meta.mappers.column_metric_mapper import ColumnMetricMapper
from app.repositories.mysql.meta.mappers.metric_info_mapper import MetricInfoMapper
from app.repositories.mysql.meta.mappers.table_info_mapper import TableInfoMapper


class MetaMySQLRepository:
    # 与MySQL交互，返回SQLAlchemy的model

    # 拿到session
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_table_infos(self, table_infos: List[TableInfo]):
        table_info_models: List[TableInfoMySQL] = []
        for table_info in table_infos:
            model = TableInfoMapper.to_model(table_info)
            table_info_models.append(model)
        self.session.add_all(table_info_models)


    async def save_column_infos(self, column_infos: list[ColumnInfo]):
        models = [ColumnInfoMapper.to_model(column_info) for column_info in column_infos]
        self.session.add_all(models)

    async def save_column_metrics(self, column_metric_infos: list[ColumnMetric]):
        models = [ColumnMetricMapper.to_model(column_metric_info) for column_metric_info in column_metric_infos]
        self.session.add_all(models)

    async def save_metric_infos(self, metric_infos: list[MetricInfo]):
        #MetricInfo->MetricInfoMySQL
        models = [MetricInfoMapper.to_model(metric_info) for metric_info in metric_infos]
        self.session.add_all(models)





