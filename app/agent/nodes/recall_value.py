from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    logger.info(f"开始召回指标任务, 输入参数为{state}")
    writer = runtime.stream_writer

    try:
        query = state["query"]
        keywords = state["keywords"]
        value_es_repository = runtime.context["value_es_repository"]

        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_value_recall"),
            input_variables=["query"]
        )
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"query": query})
        logger.info(f"llm 扩展后的结果：{result}")
        keywords = list(set(keywords + result))
        # 定义一个map
        retrieved_values_map: dict[str, ValueInfo] = {}
        # 4. 循环遍历： ['地区', '销售额', '统计日期']
        for keyword in keywords:
            # 查询es索引库.
            value_infos: list[ValueInfo] = await value_es_repository.search(keyword)
            for value_info in value_infos:
                if value_info.id not in retrieved_values_map:
                    retrieved_values_map[value_info.id] = value_info
        retrieved_values = list(retrieved_values_map.values())
        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info(f"召回字段取值key信息：{retrieved_values_map.keys()}")
        # 返回字典信息
        return {"retrieved_values": retrieved_values}



    except Exception as e:
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        logger.info(f"召回字段取值失败，错误信息为{e}")
        raise















