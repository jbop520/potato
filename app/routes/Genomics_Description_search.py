from flask import Blueprint, render_template, request, current_app
from ..db import query_db

# =========================================================
# Blueprint
# =========================================================
genomics_description_search_bp = Blueprint(
    "genomics_description_search_bp",
    __name__,
    url_prefix="/genomics_description_search"
)

# 基因组 → 表名映射（与 keyword search 保持一致）
GENOME_TABLE_MAP = {
    "dm8": "dm8_gene_annotation",
    "c454": "c454_gene_annotation",
    "c804": "c804_gene_annotation",
    "c882": "c882_gene_annotation",
    "t206": "t206_gene_annotation",
}

# =========================================================
# Description 模糊查询函数
# =========================================================
def search_description(keyword, cfg, genome=None):
    """
    在所有 *_gene_annotation 表中
    使用 Description LIKE %keyword% 进行模糊查询
    如果指定了 genome，则只查询对应的表
    """
    keyword = keyword.strip()
    results = []

    annotation_tables = {
        "T206_gene_annotation": cfg.get("T206_GENE_ANNOTATION", "t206_gene_annotation"),
        "C454_gene_annotation": cfg.get("C454_GENE_ANNOTATION", "c454_gene_annotation"),
        "C882_gene_annotation": cfg.get("C882_GENE_ANNOTATION", "c882_gene_annotation"),
        "C804_gene_annotation": cfg.get("C804_GENE_ANNOTATION", "c804_gene_annotation"),
        "DM8_gene_annotation": cfg.get("DM8_GENE_ANNOTATION", "dm8_gene_annotation"),
    }

    for alias, table in annotation_tables.items():
        # 如果指定了 genome，只查询匹配的表
        if genome:
            alias_lower = alias.lower().replace("_gene_annotation", "")
            if alias_lower != genome.lower():
                continue

        sql = f"""
            SELECT *
            FROM `{table}`
            WHERE `Description` LIKE %s
        """
        rows = query_db(sql, (f"%{keyword}%",))

        if rows:
            results.append((alias, rows))

    return results


# =========================================================
# 路由
# =========================================================
@genomics_description_search_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    genome = (request.args.get("genome") or "").strip().lower()
    results = []
    cfg = current_app.config

    if q:
        results = search_description(q, cfg, genome=genome if genome else None)
        print(f"[DEBUG] Description 命中表数: {len(results)}")

    return render_template(
        "Genomics_Description_search.html",
        q=q,
        genome=genome,
        genomes=GENOME_TABLE_MAP.keys(),
        results=results,
    )
