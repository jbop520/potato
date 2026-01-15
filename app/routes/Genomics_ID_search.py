from flask import Blueprint, render_template, request, current_app, url_for
from ..db import query_one_table  # 复用原有数据库查询方法

# 创建蓝图
genomics_id_search_bp = Blueprint("genomics_id_search_bp", __name__)


def find_homologous_genes(query_value, cfg):
    """
    查找同源基因（类似find_associated_gene功能）
    从同源基因关联表中查询与当前Gene ID关联的同源基因
    """
    query_value = query_value.strip()
    homologous_genes = []

    rows_by_transcript = query_one_table(cfg["COLD_LINKS"], "参考基因ID", query_value)
    if rows_by_transcript:
        homologous_genes.extend([row.get("对比基因ID") for row in rows_by_transcript if row.get("对比基因ID")])
    # 去重并保留顺序
    return list(dict.fromkeys(homologous_genes))


@genomics_id_search_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    results = []
    homologous_genes = []
    cfg = current_app.config

    # 1. 查询注释表数据
    if q:
        # 定义需要查询的注释表（配置从config读取，兜底固定值）
        annotation_tables = {
            "T206_gene_annotation": cfg.get("T206_GENE_ANNOTATION", "t206_gene_annotation"),
            "C454_gene_annotation": cfg.get("C454_GENE_ANNOTATION", "c454_gene_annotation"),
            "C882_gene_annotation": cfg.get("C882_GENE_ANNOTATION", "c882_gene_annotation"),
            "C804_gene_annotation": cfg.get("C804_GENE_ANNOTATION", "c804_gene_annotation"),
            "DM8_gene_annotation": cfg.get("DM8_GENE_ANNOTATION", "dm8_gene_annotation")  # 补充常见注释表
        }

        # 遍历表名查询数据
        for table_alias, table_name in annotation_tables.items():
            rows = query_one_table(table_name, "Gene_ID", q)
            if rows:
                results.append((table_alias, rows))

        # 2. 获取同源基因
        homologous_genes = find_homologous_genes(q, cfg)

    # 渲染模板
    return render_template(
        "Genomics_ID_search.html",
        q=q,
        results=results,
        homologous_genes=homologous_genes
    )