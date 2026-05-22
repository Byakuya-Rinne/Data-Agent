from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.metric_info import MetricInfo
from app.prompt.prompt_loader import load_prompt

async def recall_metric(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    logger.info(f"开始召回指标任务, 输入参数为{state}")
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回指标", "status": "running"})

    try:
        # 拿query和keywords
        query = state["query"]

        #调用llm扩展关键词
        prompt = PromptTemplate(
            template=load_prompt("extend_keywords_for_metric_recall"),
            input_variables=["query"]
        )
        chain = prompt | llm |JsonOutputParser()
        result = await chain.ainvoke({"query": query})
        # result 是 LLM 根据用户问题生成的一组指标关键词列表，类型是 list[str]

        keywords = state["keywords"] # 第一个节点分出来的关键词
        keywords = list(set(keywords + result))

        # 逐个生成keyword的向量，逐个去向量数据库里查
        embedding_client = runtime.context["embedding_client"]
        metric_qdrant_repository = runtime.context["metric_qdrant_repository"]
        retrieved_metrics_map: dict[str, MetricInfo] = {}
        for keyword in keywords:
            embedding = await embedding_client.aembed_query(keyword)
            metric_infos: list[MetricInfo] = await metric_qdrant_repository.search(embedding)
            # 去重
            # 不能直接 set(metric_infos)，因为：
            # 默认 set 使用对象的 __hash__ 和 __eq__ 方法
            # 需求是按 “ID 字段” 去重，不是按对象整体相等
            for metric_info in metric_infos:
                if metric_info.id not in retrieved_metrics_map:
                    retrieved_metrics_map[metric_info.id] = metric_info
        retrieved_metrics = list(retrieved_metrics_map.values())
        writer({"type": "progress", "step": "召回指标", "status": "success"})
        logger.info(f"召回指标key：{retrieved_metrics_map.keys()}")
        logger.info(f"召回指标信息：{retrieved_metrics}")
        # 返回数据
        return {"retrieved_metrics": retrieved_metrics}

    except Exception as e:
        logger.error(f"召回指标失败，错误信息为{e}")
        writer({"type": "progress", "step": "召回指标", "status": "error"})
        raise












