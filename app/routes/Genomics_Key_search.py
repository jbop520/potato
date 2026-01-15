from flask import Blueprint, render_template, request, current_app
from ..db import query_one_table, query_db

# 创建蓝图
genomics_key_search_bp = Blueprint("genomics_key_search_bp", __name__)


def query_annotation_data(chromosome, start, end):
    """
    根据染色体、起始和终止位置查询注释数据
    :param chromosome: 染色体编号
    :param start: 起始位置（数值型）
    :param end: 终止位置（数值型）
    :return: 各表查询结果列表，格式[(表名, 数据行列表), ...]
    """
    results = []
    cfg = current_app.config
    # 定义需要查询的注释表（从配置读取，兜底固定值）
    annotation_tables = {
        "T206_gene_annotation": cfg.get("T206_GENE_ANNOTATION", "t206_gene_annotation"),
        "C454_gene_annotation": cfg.get("C454_GENE_ANNOTATION", "c454_gene_annotation"),
        "C882_gene_annotation": cfg.get("C882_GENE_ANNOTATION", "c882_gene_annotation"),
        "C804_gene_annotation": cfg.get("C804_GENE_ANNOTATION", "c804_gene_annotation"),
        "DM8_gene_annotation": cfg.get("DM8_GENE_ANNOTATION", "dm8_gene_annotation")   # 补充原需求笔误的C804重复问题，替换为C830
    }

    try:
        # 遍历每个注释表执行查询
        for table_alias, table_name in annotation_tables.items():
            # 构造SQL：匹配Chromosome，且start<=输入end，end>=输入start（区间重叠）
            sql = f"""
                SELECT * FROM {table_name} 
                WHERE Chromosome = %s 
                AND start <= %s 
                AND end >= %s
            """
            # 执行查询
            rows = query_db(sql, (chromosome, end, start))
            if rows:
                results.append((table_alias, rows))
    except Exception as e:
        current_app.logger.error(f"查询基因注释数据失败: {str(e)}")
        results = []
    return results


@genomics_key_search_bp.route("/genomics_key_search", methods=["GET"])
def index():
    # 获取前端输入参数
    chromosome = request.args.get("chromosome", "").strip()
    start_str = request.args.get("start", "").strip()
    end_str = request.args.get("end", "").strip()

    results = []
    error_msg = ""
    start = None
    end = None

    # 参数校验
    if chromosome and start_str and end_str:
        # 转换数值类型
        try:
            start = float(start_str)
            end = float(end_str)
            if start > end:
                error_msg = "起始位置不能大于终止位置！"
            else:
                # 执行数据查询
                results = query_annotation_data(chromosome, start, end)
        except ValueError:
            error_msg = "起始/终止位置必须为数字！"
    elif chromosome or start_str or end_str:
        error_msg = "请完整输入染色体、起始位置、终止位置！"

    return render_template(
        "Genomics_Key_search.html",
        chromosome=chromosome,
        start=start_str,
        end=end_str,
        results=results,
        error_msg=error_msg
    )