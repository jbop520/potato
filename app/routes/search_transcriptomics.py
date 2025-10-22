from flask import Blueprint, request, render_template, current_app
from ..db import query_one_table  # 导入现有数据库查询工具

# 创建蓝图（与文件名保持一致）
search_transcriptomics_bp = Blueprint("search_transcriptomics_bp", __name__)


def query_transcriptomics_data(ref_id, cfg):
    """
    查询两个蛋白过滤表的基因数据并合并结果
    参数:
        ref_id: 参考基因ID
        cfg: 配置字典
    返回:
        合并后的结果列表（含来源表信息）
    """
    results = []
    # 要查询的表名（从配置中获取）
    tables = [
        cfg["TABLE_C804_C882_PROTEIN_FILTER"],
        cfg["TABLE_C882_C804_PROTEIN_FILTER"]
    ]

    for table in tables:
        # 调用query_one_table（按位置参数传递：表名, 字段名, 查询值）
        # 注意：字段名需与你的数据库表中实际字段一致，此处假设为"reference_genome_id"
        rows = query_one_table(
            table,  # 第一个参数：表名（位置参数）
            "Reference_genome_ID",  # 第二个参数：查询字段名
            ref_id  # 第三个参数：查询值
        )

        # 为每条记录添加来源表标识
        for row in rows:
            row["source_table"] = table  # 增加来源表信息
            results.append(row)

    return results


@search_transcriptomics_bp.route("/", methods=["GET"])
def index():
    """转录组基因查询主页面"""
    # 获取前端传入的参考基因ID
    ref_id = request.args.get("ref_id", "").strip()
    # 获取配置
    cfg = current_app.config

    # 执行查询（如果ref_id不为空）
    results = []
    if ref_id:
        results = query_transcriptomics_data(ref_id, cfg)

    # 渲染前端页面
    return render_template(
        "search_transcriptomics.html",
        ref_id=ref_id,  # 回显查询条件
        results=results,  # 查询结果
        # 传递表名用于前端显示
        table1=cfg["TABLE_C804_C882_PROTEIN_FILTER"],
        table2=cfg["TABLE_C882_C804_PROTEIN_FILTER"]
    )