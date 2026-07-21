from urllib.parse import quote

from flask import Blueprint, request, render_template, current_app, url_for
from ..db import query_db

# 创建蓝图
search_id_transcriptomics_bp = Blueprint("search_id_transcriptomics_bp", __name__)


def get_gene_related_treatments(gene_id):
    """
    从数据库中：
    1. 根据基因ID前缀匹配对应的材料名
    2. 根据材料名查询该材料参与的所有处理（排除cold_ac_candol_m4_2h相关链接）
    返回格式：[{
        "name": "前端直接显示的处理名",
        "route": "目标处理页面的路由代码",
        "url": "目标处理页面的URL"
    }, ...]
    """
    # 1. 配置项（表名、字段映射）
    GENE_TREATMENT_TABLE = current_app.config.get(
        "MERGED_GENE_TREATMENT_RESULT", "merged_gene_treatment_result"
    )
    MATERIAL_TABLE = "transcriptomics_tool"  # 材料-处理关联表（对应截图中的表）

    TREATMENT_FIELD_MAP = {
        "bacterial_wilt": {"display_name": "Bacterial wilt", "route_code": "search_Bacterial_wilt_bp.index"},
        "cold_nac_m4_3h": {"display_name": "Cold (NAC_M4_3h)", "route_code": "search_cold_nac_m4_3h_bp.index"},
        "salt_48h": {"display_name": "Salt (48h)", "route_code": "search_salt_48h_bp.index"},
        "tuber_development": {"display_name": "Tuber Development", "route_code": "search_tuber_development_bp.index"},
        "cold_ac_m4_2h": {"display_name": "Cold (AC_M4_2h)", "route_code": "search_cold_ac_m4_2h_bp.index"},
        "cold_ac_candol_m4_2h": {"display_name": "Cold (AC_candol_M4_2h)",
                                 "route_code": "search_cold_ac_candol_m4_2h_bp.index"},
        "cold_ac_m3": {"display_name": "Cold (AC_M3)", "route_code": "search_cold_ac_m3_bp.index"},
        "multiple_treatments": {"display_name": "multiple_treatments",
                                "route_code": "search_multiple_treatments_bp.index"}
    }

    # 需排除的路由代码（核心配置）
    # EXCLUDE_ROUTE = "search_Bacterial_wilt_bp.index"

    related_treatments = []
    try:
        # ---------- 步骤1：解析基因ID的前缀，匹配对应的材料名 ----------
        gene_prefix = None
        target_material = None  # 补充定义，避免未定义报错
        prefix_patterns = [
            ("ScanH1c", "c454"),
            ("ScomH1c", "c804"),
            ("Smochap1C", "c830"),
            ("SverC", "c882"),
            ("DM8", "dm"),
            ("SchoHap1C", "t206")
        ]
        for prefix, material in prefix_patterns:
            if gene_id.startswith(prefix):
                gene_prefix = prefix
                target_material = material
                break
        if not gene_prefix:
            return related_treatments  # 无匹配前缀，返回空

        # ---------- 步骤2：根据材料名，查询该材料参与的所有处理 ----------
        query_material_sql = f"""
            SELECT 处理 FROM {MATERIAL_TABLE} 
            WHERE 材料 LIKE %s
        """
        material_treatments = query_db(query_material_sql, (f"%{target_material}%",))
        if not material_treatments:
            return related_treatments

        # 提取处理名列表（去重）
        treatment_names = list({t["处理"] for t in material_treatments})

        # ---------- 步骤3：映射处理名到路由、URL（排除指定路由） ----------
        for treatment in treatment_names:
            # 匹配TREATMENT_FIELD_MAP中的处理（需统一处理名字段格式）
            db_field = treatment.lower().replace(" ", "_").replace("(", "").replace(")", "")
            config = TREATMENT_FIELD_MAP.get(db_field)
            if not config:
                continue  # 无配置的处理，跳过

            # 过滤需排除的路由（核心逻辑）


            # 生成URL
            try:
                route_url = url_for(config["route_code"], q=gene_id)
            except:
                route_url = url_for(config["route_code"])

            related_treatments.append({
                "name": config["display_name"],
                "route": config["route_code"],
                "url": route_url
            })

        return related_treatments

    except Exception as e:
        current_app.logger.error(f"查询基因[{gene_id}]关联处理失败：{str(e)}")
        return related_treatments


def get_gene_ncbi_link(gene_id):
    mapping_table = current_app.config.get("DM8_NCBI_MAPPING", "dm8_ncbi_mapping")
    try:
        row = query_db(
            f"""
            SELECT ncbi_id
            FROM `{mapping_table}`
            WHERE gene_id = %s
              AND ncbi_id IS NOT NULL
              AND ncbi_id <> ''
            LIMIT 1
            """,
            (gene_id,),
            one=True,
        )
        if not row:
            return None

        ncbi_id = (row.get("ncbi_id") or "").strip()
        if not ncbi_id:
            return None

        return {
            "id": ncbi_id,
            "url": f"https://www.ncbi.nlm.nih.gov/search/all/?term={quote(ncbi_id)}",
        }
    except Exception as e:
        current_app.logger.error(f"Query NCBI mapping for gene [{gene_id}] failed: {str(e)}")
        return None


@search_id_transcriptomics_bp.route("/", methods=["GET"])
def index():
    # 同时接受 q 和 ref_id 参数
    q = (request.args.get("q") or request.args.get("ref_id") or "").strip()

    cfg = current_app.config
    related_treatments = []
    ncbi_link = None

    print(f"=== search_id_transcriptomics 调试信息 ===")
    print(f"接收到的参数: {dict(request.args)}")
    print(f"最终使用的基因ID: {q}")
    print(f"请求URL: {request.url}")
    print(f"蓝图名称: {search_id_transcriptomics_bp.name}")

    if q:
        # 获取关联处理
        related_treatments = get_gene_related_treatments(q)
        ncbi_link = get_gene_ncbi_link(q)
        print(f"查询到的处理数量: {len(related_treatments)}")

    print("Related Treatments:")
    for treatment in related_treatments:
        print(f"- Name: {treatment.get('name')}, URL: {treatment.get('url')}")

    if not related_treatments:
        print("Related Treatments is empty")

    print("=== 调试结束 ===\n")

    return render_template(
        "search_id_transcriptomics.html",
        q=q,
        related_treatments=related_treatments,
        ncbi_link=ncbi_link
    )


