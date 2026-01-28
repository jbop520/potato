from flask import Blueprint, render_template, request, jsonify
from ..db import query_db

genomics_key_search_bp = Blueprint(
    "genomics_key_search_bp",
    __name__
)

# 基因组 → 表名映射
GENOME_TABLE_MAP = {
    "dm8": "dm8_gene_annotation",
    "c454": "c454_gene_annotation",
    "c804": "c804_gene_annotation",
    "c882": "c882_gene_annotation",
    "t206": "t206_gene_annotation",
}

# ================== 染色体接口 ==================
@genomics_key_search_bp.route(
    "/genomics_key_search/chromosomes",
    methods=["GET"]
)
def get_chromosomes_by_genome():
    genome = request.args.get("genome", "").lower()
    table_name = GENOME_TABLE_MAP.get(genome)

    if not table_name:
        return jsonify({"chromosomes": []})

    sql = f"""
        SELECT DISTINCT Chromosome
        FROM {table_name}
        ORDER BY Chromosome
    """
    rows = query_db(sql)

    return jsonify({
        "chromosomes": [r["Chromosome"] for r in rows]
    })


def query_annotation_data(genome, chromosome, start, end):
    table_name = GENOME_TABLE_MAP.get(genome)
    if not table_name:
        return []

    sql = f"""
        SELECT *
        FROM {table_name}
        WHERE Chromosome = %s
          AND start <= %s
          AND end >= %s
    """
    rows = query_db(sql, (chromosome, end, start))
    if rows:
        return [(table_name, rows)]
    return []


# ================== 主页面 ==================
@genomics_key_search_bp.route(
    "/genomics_key_search",
    methods=["GET"]
)
def index():
    genome = request.args.get("genome", "").strip().lower()
    chromosome = request.args.get("chromosome", "").strip()
    start_str = request.args.get("start", "").strip()
    end_str = request.args.get("end", "").strip()

    results = []
    error_msg = ""

    if genome and chromosome and start_str and end_str:
        try:
            start = float(start_str)
            end = float(end_str)
            if start > end:
                error_msg = "起始位置不能大于终止位置！"
            else:
                results = query_annotation_data(
                    genome, chromosome, start, end
                )
        except ValueError:
            error_msg = "起始/终止位置必须为数字！"
    elif any([genome, chromosome, start_str, end_str]):
        error_msg = "请完整选择基因组、染色体并输入位置区间！"

    return render_template(
        "Genomics_Key_search.html",
        genomes=GENOME_TABLE_MAP.keys(),
        genome=genome,
        chromosome=chromosome,
        start=start_str,
        end=end_str,
        results=results,
        error_msg=error_msg
    )
