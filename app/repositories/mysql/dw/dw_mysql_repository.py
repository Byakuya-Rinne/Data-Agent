from typing import Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DWMySQLRepository:

    # 拿到session
    def __init__(self, session: AsyncSession):
        self.session = session

    # 返回每行中每列的类型
    # show columns from dim_customer

    # Field         Type
    # customer_id	varchar(20)
    # customer_name	varchar(50)
    # gender	varchar(10)
    # member_level	varchar(20)

    async def get_column_types(self, table_name: str) -> Dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        # print(result)
        return {row.Field: row.Type for row in result}



    async def get_column_values(self, table_name: str, column_name: str, limit: int = 10) -> list[str]:
        # 定义sql
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        # 执行sql
        result = await self.session.execute(text(sql))
        # 返回结果
        return result.scalars().fetchall()

