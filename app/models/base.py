from sqlalchemy.orm import DeclarativeBase


# Python 类到 MySQL 表的直接映射
# SQLAlchemy 的 ORM 模型，直接映射到 MySQL 里的 table_info、column_info 等表。
class Base(DeclarativeBase):
    pass