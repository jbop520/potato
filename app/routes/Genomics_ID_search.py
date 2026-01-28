from flask import Blueprint, render_template, request, current_app
from ..db import query_one_table, query_db

# 创建蓝图
genomics_id_search_bp = Blueprint("genomics_id_search_bp", __name__)

# ================= 同源基因函数（不变） =================
def find_homologous_genes(query_value, cfg):
    query_value = query_value.strip()
    homologous_genes = []

    rows_by_transcript = query_one_table(
        cfg["COLD_LINKS"], "参考基因ID", query_value
    )
    if rows_by_transcript:
        homologous_genes.extend(
            [row.get("对比基因ID") for row in rows_by_transcript if row.get("对比基因ID")]
        )

    return list(dict.fromkeys(homologous_genes))


# ================= 核心：支持 FASTA 前缀模糊查询 =================
def get_sequence_data(query_value, cfg):
    """
    FASTA 表：seq_id 前缀模糊匹配（LIKE xxx%）
    其他表：不受影响
    """
    query_value = query_value.strip()
    sequence_data = {}

    sequence_tables = {
        "DM8": {
            "cds": "dm8_cds_fasta",
            "protein": "dm8_protein_fasta",
        },
        "C454Hap1": {
            "cds": "c454hap1_cds_fasta",
            "protein": "c454hap1_protein_fasta",
        },
        "C454Hap2": {
            "cds": "c454hap2_cds_fasta",
            "protein": "c454hap2_protein_fasta",
        },
        "C804Hap1": {
            "cds": "c804hap1_cds_fasta",
            "protein": "c804hap1_protein_fasta",
        },
        "C804Hap2": {
            "cds": "c804hap2_cds_fasta",
            "protein": "c804hap2_protein_fasta",
        },
        "C882": {
            "cds": "c882_cds_fasta",
            "protein": "c882_protein_fasta",
        },
        "T206Hap1": {
            "cds": "t206hap1_cds_fasta",
            "protein": "t206hap1_protein_fasta",
        },
        "T206Hap2": {
            "cds": "t206hap2_cds_fasta",
            "protein": "t206hap2_protein_fasta",
        },
    }

    for species, tables in sequence_tables.items():
        species_data = {}

        # -------- CDS FASTA（前缀模糊查询） --------
        cds_table = tables["cds"]
        cds_sql = f"""
            SELECT * FROM `{cds_table}`
            WHERE `seq_id` LIKE %s
            ORDER BY `seq_id`
        """
        cds_rows = query_db(cds_sql, (query_value + "%",))

        if cds_rows:
            species_data["cds"] = []
            for row in cds_rows:
                seq = row.get("sequence", "")
                species_data["cds"].append({
                    "seq_id": row.get("seq_id"),
                    "header": row.get("header", row.get("seq_id")),
                    "sequence": seq,
                    "length": row.get("length", len(seq)),
                    "table_name": cds_table,
                })

        # -------- Protein FASTA（前缀模糊查询） --------
        protein_table = tables["protein"]
        protein_sql = f"""
            SELECT * FROM `{protein_table}`
            WHERE `seq_id` LIKE %s
            ORDER BY `seq_id`
        """
        protein_rows = query_db(protein_sql, (query_value + "%",))

        if protein_rows:
            species_data["protein"] = []
            for row in protein_rows:
                seq = row.get("sequence", "")
                species_data["protein"].append({
                    "seq_id": row.get("seq_id"),
                    "header": row.get("header", row.get("seq_id")),
                    "sequence": seq,
                    "length": row.get("length", len(seq)),
                    "table_name": protein_table,
                })

        if species_data:
            sequence_data[species] = species_data

    print(f"[DEBUG] FASTA 命中物种数: {len(sequence_data)}")
    return sequence_data


# ================= 路由（不变） =================
@genomics_id_search_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    results = []
    homologous_genes = []
    sequence_data = {}
    cfg = current_app.config

    if q:
        annotation_tables = {
            "T206_gene_annotation": cfg.get("T206_GENE_ANNOTATION", "t206_gene_annotation"),
            "C454_gene_annotation": cfg.get("C454_GENE_ANNOTATION", "c454_gene_annotation"),
            "C882_gene_annotation": cfg.get("C882_GENE_ANNOTATION", "c882_gene_annotation"),
            "C804_gene_annotation": cfg.get("C804_GENE_ANNOTATION", "c804_gene_annotation"),
            "DM8_gene_annotation": cfg.get("DM8_GENE_ANNOTATION", "dm8_gene_annotation"),
        }

        for alias, table in annotation_tables.items():
            rows = query_one_table(table, "Gene_ID", q)
            if rows:
                results.append((alias, rows))

        homologous_genes = find_homologous_genes(q, cfg)
        sequence_data = get_sequence_data(q, cfg)

        print("=== sequence_data ===")
        print(sequence_data)
        print("=== keys ===", sequence_data.keys())
        print("=== value type ===", type(next(iter(sequence_data.values()))))

    return render_template(
        "Genomics_ID_search.html",
        q=q,
        results=results,
        homologous_genes=homologous_genes,
        sequence_data=sequence_data,
    )
