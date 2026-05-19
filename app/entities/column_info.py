from dataclasses import dataclass
from typing import Any

# 业务实体类（dataclass）
# 代表元数据概念（表、字段、指标、取值等），不限于给 ES/Qdrant 用，是应用层统一的数据模型
@dataclass
class ColumnInfo:
    id: str
    name: str
    type: str
    role: str
    examples: list[Any]
    description: str
    alias: list[str]
    table_id: str