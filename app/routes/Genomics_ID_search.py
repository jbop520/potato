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


# ================= 从基因组序列中截取 up_2kb 和 down_1kb =================
# ================= 从基因组序列中截取 up_2kb 和 down_1kb =================
def extract_up_down_sequences(query_value, gene_info, cfg):
    """
    根据基因的染色体位置信息，从基因组FASTA表中截取 up_2kb 和 down_1kb 序列
    正链：up_2kb = start往前推2000bp，down_1kb = end往后推1000bp
    负链：up_2kb = end往后推2000bp，down_1kb = start往前推1000bp
    """
    up_down_data = {}

    try:
        # 获取基因的位置和链信息
        chromosome = gene_info.get('Chromosome', '').strip()
        gene_start = int(gene_info.get('Start', 0))
        gene_end = int(gene_info.get('End', 0))
        gene_strand = gene_info.get('Positive /Negative  strand', '+').strip()

        # 验证必要信息是否存在
        if not chromosome:
            current_app.logger.error(f"基因 {query_value} 缺少染色体信息")
            print(f"Error: 基因 {query_value} 缺少染色体信息")
            return up_down_data

        if gene_start <= 0 or gene_end <= 0 or gene_end < gene_start:
            current_app.logger.error(f"基因 {query_value} 位置信息无效: start={gene_start}, end={gene_end}")
            print(f"Error: 基因 {query_value} 位置信息无效")
            return up_down_data

        print(f"基因信息: Chromosome={chromosome}, Start={gene_start}, End={gene_end}, Strand={gene_strand}")

        # 根据链信息确定截取位置
        if gene_strand == '+':
            # 正链: up_2kb = start往前推2000bp, down_1kb = end往后推1000bp
            up_start = max(1, gene_start - 2000)
            up_end = gene_start - 1
            down_start = gene_end + 1
            down_end = gene_end + 1000
            print(f"正链截取: up_2kb [{up_start}-{up_end}], down_1kb [{down_start}-{down_end}]")
        else:
            # 负链: up_2kb = end往后推2000bp, down_1kb = start往前推1000bp
            up_start = gene_end + 1
            up_end = gene_end + 2000
            down_start = max(1, gene_start - 1000)
            down_end = gene_start - 1
            print(f"负链截取: up_2kb [{up_start}-{up_end}], down_1kb [{down_start}-{down_end}]")

        # 定义物种与基因组FASTA表的映射
        genome_tables = {
            "C454Hap1": "c454hap1_genome_fasta",
            "C454Hap2": "c454hap2_genome_fasta",
            "C804Hap1": "c804hap1_genome_fasta",
            "C804Hap2": "c804hap2_genome_fasta",
            "C882": "c882_genome_fasta",
            "DM8": "dm8_genome_fasta",
            "T206Hap1": "t206hap1_genome_fasta",
            "T206Hap2": "t206hap2_genome_fasta",
        }

        # 遍历所有物种的基因组FASTA表
        for species, table_name in genome_tables.items():
            species_updown = []

            # 构建查询SQL
            query_sql = f"""
                SELECT `Chromosome`, `Gene Sequences`
                FROM `{table_name}`
                WHERE `Chromosome` = %s
            """

            # 查询up_2kb区域（如果有效）
            if up_start <= up_end and up_start > 0:
                rows = query_db(query_sql, (chromosome,))

                if rows:
                    for row in rows:
                        full_sequence = row.get('Gene Sequences', '')
                        seq_length = len(full_sequence)
                        seq_id = row.get('Chromosome', '')

                        # 确保截取位置不超出序列长度
                        start_pos = up_start
                        end_pos = min(up_end, seq_length)

                        if start_pos <= end_pos and start_pos <= seq_length:
                            # 转换为0-based索引
                            up_sequence = full_sequence[start_pos - 1:end_pos]

                            if up_sequence:
                                species_updown.append({
                                    "gene_id": query_value,
                                    "seq_id": seq_id,
                                    "type": "up_2kb",
                                    "source": "genome",
                                    "species": species,
                                    "chromosome": chromosome,
                                    "region": f"{start_pos}-{end_pos}",
                                    "sequence": up_sequence,
                                    "length": len(up_sequence),
                                    "strand": gene_strand,
                                    "original_seq_id": seq_id,
                                    "display_name": f"up_2kb (Genome {chromosome})",
                                    "table_name": table_name
                                })
                                print(f"从{species}的{chromosome}截取up_2kb成功: {start_pos}-{end_pos}, 长度: {len(up_sequence)}")

            # 查询down_1kb区域（如果有效）
            if down_start <= down_end and down_start > 0:
                rows = query_db(query_sql, (chromosome,))

                if rows:
                    for row in rows:
                        full_sequence = row.get('Gene Sequences', '')
                        seq_length = len(full_sequence)
                        seq_id = row.get('Chromosome', '')

                        # 确保截取位置不超出序列长度
                        start_pos = down_start
                        end_pos = min(down_end, seq_length)

                        if start_pos <= end_pos and start_pos <= seq_length:
                            # 转换为0-based索引
                            down_sequence = full_sequence[start_pos - 1:end_pos]

                            if down_sequence:
                                species_updown.append({
                                    "gene_id": query_value,
                                    "seq_id": seq_id,
                                    "type": "down_1kb",
                                    "source": "genome",
                                    "species": species,
                                    "chromosome": chromosome,
                                    "region": f"{start_pos}-{end_pos}",
                                    "sequence": down_sequence,
                                    "length": len(down_sequence),
                                    "strand": gene_strand,
                                    "original_seq_id": seq_id,
                                    "display_name": f"down_1kb (Genome {chromosome})",
                                    "table_name": table_name
                                })
                                print(f"从{species}的{chromosome}截取down_1kb成功: {start_pos}-{end_pos}, 长度: {len(down_sequence)}")

            # 如果当前物种有数据，添加到结果中
            if species_updown:
                if species not in up_down_data:
                    up_down_data[species] = {}
                up_down_data[species]["genome_updown"] = species_updown

    except Exception as e:
        current_app.logger.error(f"截取 up/down 序列失败: {str(e)}")
        print(f"Error in extract_up_down_sequences: {str(e)}")
        import traceback
        traceback.print_exc()

    print(f"最终 up_down_data: {up_down_data}")
    return up_down_data
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


# ================= 路由 =================
@genomics_id_search_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()
    results = []
    homologous_genes = []
    sequence_data = {}
    up_down_data = {}  # 存储从基因组截取的 up_2kb 和 down_1kb
    gene_info = None  # 存储当前查询基因的注释信息
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
                # 保存第一个找到的基因注释信息
                if not gene_info and rows:
                    gene_info = rows[0]

        homologous_genes = find_homologous_genes(q, cfg)
        sequence_data = get_sequence_data(q, cfg)

        # 如果找到了基因注释信息，则截取 up/down 序列（从基因组）
        if gene_info:
            up_down_data = extract_up_down_sequences(q, gene_info, cfg)

    return render_template(
        "Genomics_ID_search.html",
        q=q,
        results=results,
        homologous_genes=homologous_genes,
        sequence_data=sequence_data,
        up_down_data=up_down_data,
    )