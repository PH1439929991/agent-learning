"""logging 基础练习：日志对象、日志级别和统一输出格式。"""

import logging


# __name__ 是当前模块名。以后看到日志时，可以知道它来自哪个模块。
logger = logging.getLogger(__name__)


def configure_logging(level: int = logging.INFO) -> None:
    """设置整个程序的基础日志格式。通常只在程序入口调用一次。"""
    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ),
    )


def demonstrate_log_levels() -> None:
    """模拟 Agent 运行中的四类事件。"""
    # 当前配置是 INFO，因此 DEBUG 默认不会显示。
    logger.debug("准备构造模型请求参数")

    # 使用 %s 占位符，把动态数据作为后续参数传入。
    logger.info(
        "Agent 请求开始 | question=%s",
        "请介绍亚索",
    )

    # TODO 1：使用 logger.warning() 记录下面的内容：
    # 工具返回失败 | tool_name=get_champion_info
    logger.warning(
        "工具返回失败 | tool_name=%s",
        "get_champion_info",
    )

    # TODO 2：使用 logger.error() 记录下面的内容：
    # 达到最大工具轮次 | max_tool_rounds=5
    logger.error(
        "达到最大工具轮次 | max_tool_rounds=%s",
        5,
    )


def main() -> None:
    configure_logging()
    demonstrate_log_levels()


if __name__ == "__main__":
    main()
