from flask import Blueprint, request, render_template, current_app
from ..db import query_one_table  # 导入数据库工具

# 创建蓝图（修复模板路径参数，与项目结构匹配）
transcriptomics_cold_tool_bp = Blueprint(
    "transcriptomics_cold_tool_bp",
    __name__,
    template_folder="../templates"  # 模板文件夹相对路径
)


# def get_transcriptomics_tools(cfg):
#     """查询全表工具数据"""
#     tool_table = cfg["TRANSCRIPTOMICS_TOOL"]  # 从配置获取表名
#     # 调用全表查询（key_col传"*"）
#     tools = query_one_table(
#         table=tool_table,
#         key_col="*",
#         key_value=None
#     )
#     return tools

def get_transcriptomics_tools(cfg):
    tool_table = cfg["TRANSCRIPTOMICS_TOOL"]
    # 新增：打印表名，确认与数据库实际表名一致
    print("当前查询的数据库表名：", tool_table)
    tools = query_one_table(table=tool_table, key_col="*", key_value=None)
    # 新增：打印查询结果数量和第一条数据（若有）
    print(f"查询到的数据条数：{len(tools)}")
    if tools:
        print("第一条数据的字段的字段：", tools[0].keys())  # 确认是否包含模板所需字段
    return tools

def get_tool_by_id(tool_id, cfg):
    """根据ID查询单个工具"""
    tool_table = cfg["TRANSCRIPTOMICS_TOOL"]
    # 调用条件查询（key_col传真实字段名"tool_id"）
    results = query_one_table(
        table=tool_table,
        key_col="tool_id",
        key_value=tool_id
    )
    return results[0] if results else None


@transcriptomics_cold_tool_bp.route("/", methods=["GET"])
def index():
    """工具主页面：展示所有工具"""
    try:
        cfg = current_app.config
        tool_data = get_transcriptomics_tools(cfg)

        # 渲染工具列表页面
        return render_template(
            "transcriptomics_cold_tool.html",
            tool_data=tool_data,  # 工具列表数据
            page_title="Transcriptomics Tools",  # 页面标题
            error_message=""  # 无错误时传空
        )
    except Exception as e:
        # 捕获异常并返回错误信息
        return render_template(
            "transcriptomics_cold_tool.html",
            tool_data=[],  # 空数据
            page_title="Transcriptomics Tools",
            error_message=f"查询失败：{str(e)}"  # 错误提示
        )


@transcriptomics_cold_tool_bp.route("/use/<int:tool_id>", methods=["GET"])
def use_tool(tool_id):
    """工具使用页面：展示单个工具详情"""
    try:
        cfg = current_app.config
        tool = get_tool_by_id(tool_id, cfg)

        # 工具不存在时返回错误页面
        if not tool:
            return render_template(
                "tool_error.html",
                message=f"工具ID {tool_id} 不存在",  # 错误信息
                back_url="/transcriptomics_cold_tool_bp/"  # 返回主页链接
            )

        # 工具存在时渲染详情页面
        return render_template(
            "use_tool.html",
            tool=tool,  # 单个工具详情
            page_title=f"Tool: {tool.get('tool_name', 'Unknown')}"  # 动态标题
        )
    except Exception as e:
        # 捕获异常并返回错误页面
        return render_template(
            "tool_error.html",
            message=f"获取工具失败：{str(e)}",
            back_url="/transcriptomics_cold_tool_bp/"
        )