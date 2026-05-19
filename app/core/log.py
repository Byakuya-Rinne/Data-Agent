import asyncio
import sys
from pathlib import Path
from loguru import logger
from app.conf.app_config import app_config
from app.core.context import request_id_ctx_var

log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>request_id - {extra[request_id]}</magenta> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# record 是 loguru 内部自动创建并传入的
def inject_request_id(record):
    request_id = request_id_ctx_var.get()
    record["extra"]["request_id"] = request_id

# 移除 loguru 默认的控制台日志处理器
logger.remove()

# 注册一个钩子：每条日志发出前，都会自动调用你传入的这个函数
logger = logger.patch(inject_request_id)

# 控制台日志（保持原有逻辑）
if app_config.logging.console.enable:
    logger.add(sink=sys.stdout,
               level=app_config.logging.console.level,
               format=log_format)

# 文件日志：修改为项目根目录下的 logs 文件夹
if app_config.logging.file.enable:
# 1. 获取项目根目录（当前文件所在目录的上层/上层，根据实际结构调整）
    PROJECT_ROOT = Path(__file__).parents[2]
    # 2. 拼接日志路径：项目根目录 / logs / app.log
    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_FILE = LOG_DIR / "app.log"
    # 3. 创建日志目录（确保存在）
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # 4. 添加文件日志处理器
    logger.add(
        sink = LOG_FILE,
        level=app_config.logging.file.level,
        format=log_format,
        rotation=app_config.logging.file.rotation,
        retention=app_config.logging.file.retention,
        encoding="utf-8"
    )

if __name__ == '__main__':
    async def print_log(request: str):
        # 打印日志
        logger.info(request)


    async def test1():
        # 接收到请求
        request_id_ctx_var.set("request-1")
        # 模拟处理
        await asyncio.sleep(1)
        await print_log("request-1")


    async def test2():
        # 接收到请求
        request_id_ctx_var.set("request-2")

        # 模拟处理
        await asyncio.sleep(1)
        await print_log("request-2")


    async def main():
        await asyncio.gather(test1(), test2())


    asyncio.run(main())






