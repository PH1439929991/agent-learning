"""Pydantic 工具参数校验练习。

学习目标：
1. 使用 BaseModel 定义工具参数模型。
2. 使用 Field 添加字段约束和默认值。
3. 使用 ConfigDict 禁止未声明的额外参数。
4. 使用 model_validate() 校验字典。
5. 使用 model_dump() 取得校验后的参数字典。
6. 捕获并阅读 ValidationError。

运行方式：
    PYTHONPATH=src .venv/bin/python -m agent_learning.module_04_tool_schema.argument_models

说明：
    先完成 TODO 1，再运行测试；然后完成 TODO 2，再次运行测试。
    当前文件只练习参数校验，不修改原来的 Function Calling 执行器。
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class GetChampionInfoArguments(BaseModel):
    """get_champion_info 工具的参数模型。"""

    # 禁止传入模型中没有声明的额外字段。
    model_config = ConfigDict(extra="forbid")

    # 没有默认值，所以 champion_name 是必填参数。
    # str 约束参数类型，Field(min_length=1) 拒绝空字符串。
    champion_name: str = Field(
        min_length=1,
        description="英雄中文名、英文名或称号",
    )


class ListChampionsArguments(BaseModel):
    """list_champions 工具的参数模型。"""

    # TODO 2：完成列出英雄的参数模型。
    #
    # 要求：
    # 1. 禁止传入未声明的额外字段；
    # 2. 声明 region 字符串字段；
    # 3. region 是可选参数，不传时默认使用空字符串。
    model_config = ConfigDict(extra="forbid")
    region:str = Field(
        default="",
        description="地区列表，每个地区对应一个英雄列表",
    )
    pass


GET_CHAMPION_TEST_CASES = [
    {
        "name": "正确的英雄名",
        "arguments": {"champion_name": "亚索"},
        "should_pass": True,
    },
    {
        "name": "空英雄名",
        "arguments": {"champion_name": ""},
        "should_pass": False,
    },
    {
        "name": "缺少英雄名",
        "arguments": {},
        "should_pass": False,
    },
    {
        "name": "英雄名类型错误",
        "arguments": {"champion_name": 123},
        "should_pass": False,
    },
    {
        "name": "包含额外参数",
        "arguments": {
            "champion_name": "亚索",
            "unknown": "不应该出现的字段",
        },
        "should_pass": False,
    },
]


LIST_CHAMPIONS_TEST_CASES = [
    {
        "name": "指定地区",
        "arguments": {"region": "艾欧尼亚"},
        "should_pass": True,
    },
    {
        "name": "省略可选地区",
        "arguments": {},
        "should_pass": True,
    },
    {
        "name": "地区类型错误",
        "arguments": {"region": 123},
        "should_pass": False,
    },
    {
        "name": "包含额外参数",
        "arguments": {"region": "艾欧尼亚", "unknown": True},
        "should_pass": False,
    },
]


def format_validation_error(error: ValidationError) -> str:
    """把 Pydantic 错误简化成适合练习阅读的文本。"""
    messages = []

    for detail in error.errors():
        field = ".".join(str(item) for item in detail["loc"])
        messages.append(f"{field or '参数对象'}: {detail['msg']}")

    return "; ".join(messages)


def run_test_cases(
    title: str,
    arguments_model: type[BaseModel],
    test_cases: list[dict[str, Any]],
) -> tuple[int, int]:
    """运行一组参数模型测试，并返回符合预期数和总数。"""
    print(f"\n=== {title} ===")
    expected_count = 0

    for test_case in test_cases:
        name = test_case["name"]
        arguments = test_case["arguments"]
        should_pass = test_case["should_pass"]

        try:
            validated = arguments_model.model_validate(arguments)
            actual_pass = True
            result = f"校验成功：{validated.model_dump()}"
        except ValidationError as error:
            actual_pass = False
            result = f"校验失败：{format_validation_error(error)}"

        matches_expected = actual_pass == should_pass
        if matches_expected:
            expected_count += 1

        status = "符合预期" if matches_expected else "不符合预期"
        expectation = "应成功" if should_pass else "应失败"

        print(f"[{status}] {name}（{expectation}）")
        print(f"  输入：{arguments}")
        print(f"  结果：{result}")

    return expected_count, len(test_cases)


def main() -> None:
    get_passed, get_total = run_test_cases(
        "GetChampionInfoArguments",
        GetChampionInfoArguments,
        GET_CHAMPION_TEST_CASES,
    )
    list_passed, list_total = run_test_cases(
        "ListChampionsArguments",
        ListChampionsArguments,
        LIST_CHAMPIONS_TEST_CASES,
    )

    passed = get_passed + list_passed
    total = get_total + list_total

    print(f"\n总结果：{passed}/{total} 个用例符合预期")

    if passed == total:
        print("参数模型练习已完成，可以进入工具注册表改造。")
    else:
        print("请根据 TODO 和失败用例继续完善参数模型。")


if __name__ == "__main__":
    main()
