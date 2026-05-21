from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段", "status": "running"})

    query = state["query"]
    keywords = state["keywords"]

    embedding_client = runtime.context["embedding_client"]
    column_qdrant_repository = runtime.context["column_qdrant_repository"]

    try:
        # 使用LLM扩展关键词
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_column_recall"),
            input_variables=["query"],
        )
        output_parser = JsonOutputParser()
        chain = prompt | llm | output_parser

        result = await chain.ainvoke({"query": query})

        # 使用扩展后的关键词召回字段信息
        retrieved_columns_map: dict[str, ColumnInfo] = {}

        keywords = list(set(keywords + result)) # set只用来去重
        logger.info(f"召回字段信息扩展关键词：{keywords}")

        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            payloads: list[ColumnInfo] = await column_qdrant_repository.search(
                embedding
            )
            # 将当前关键词的向量在 Qdrant 的字段信息集合中做语义检索，
            # 返回与该向量最相似的若干个 ColumnInfo 对象（即包含字段名、描述、别名等元数据的实体）。
            for payload in payloads:
                column_id = payload.id
                if column_id not in retrieved_columns_map:
                    retrieved_columns_map[column_id] = payload
        retrieved_columns = list(retrieved_columns_map.values())
        logger.info(f"召回的字段信息为{list(retrieved_columns_map.keys())}")
        writer({"type": "progress", "step": "召回字段", "status": "success"})
        return {"retrieved_columns": retrieved_columns}

    except Exception as e:
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        logger.error(f"召回字段失败，错误信息为{e}")
        raise























