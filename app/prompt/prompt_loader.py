# 加载提示词模版函数;
from pathlib import Path

def load_prompt(file_name: str):
    path = Path(__file__).parents[2]/ "prompts" / f"{file_name}.prompt"
    # 读取文件中的内容
    return path.read_text(encoding="utf-8")
