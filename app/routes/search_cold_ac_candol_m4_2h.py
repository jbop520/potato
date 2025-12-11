# from flask import Blueprint, render_template, request, current_app
# from ..db import query_one_table
#
# search_bp = Blueprint("search_bp", __name__)
#
# # 新主页路由
# @search_bp.route("/", methods=["GET"])
# def index():
#     return render_template("index.html")
#
# # 原搜索功能，换到 /search
# @search_bp.route("/search", methods=["GET"])
# def search_page():
#     q = (request.args.get("q") or "").strip()
#     results = []
#     cfg = current_app.config
#
#     if q:
#         rows_c804 = query_one_table(cfg["TABLE_C804"], "names", q)
#         if rows_c804:
#             results.append((cfg["TABLE_C804"], rows_c804))
#
#         rows_c882 = query_one_table(cfg["TABLE_C882"], "Transcript_ID", q)
#         if rows_c882:
#             results.append((cfg["TABLE_C882"], rows_c882))
#
#     return render_template(
#         "search.html",
#         q=q,
#         results=results,
#         tbl804=cfg["TABLE_C804"],
#         tbl882=cfg["TABLE_C882"]
#     )


from flask import Blueprint, render_template, request, current_app, url_for
from ..db import query_one_table, query_db
from pyecharts.charts import Line, HeatMap
from pyecharts import options as opts

# 调整JsCode的导入路径，兼容旧版本pyecharts
try:
    from pyecharts import JsCode  # 适用于较新版本
except ImportError:
    from pyecharts.commons.utils import JsCode  # 适用于旧版本
from pyecharts.options import AxisTickOpts
from pyecharts import options as opts
search_cold_ac_candol_m4_2h_bp = Blueprint("search_cold_ac_candol_m4_2h_bp", __name__)


def create_line_chart(results):
    try:
        if results and len(results) > 0 and len(results[0][1]) > 0:
            data_list = results[0][1][0]
            keys = list(data_list.keys())
            values = list(data_list.values())

            numeric_keys = []
            numeric_values = []
            for k, v in zip(keys, values):
                try:
                    numeric_values.append(float(v))
                    numeric_keys.append(k)
                except (ValueError, TypeError):
                    continue

            if numeric_keys:
                # 固定宽度为2000px，确保超过容器宽度
                line = (
                    Line(init_opts=opts.InitOpts(width="4000px", height="400px"))
                    .add_xaxis(numeric_keys)
                    .add_yaxis("", numeric_values)
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title="Line Graph"),
                        tooltip_opts=opts.TooltipOpts(trigger="axis"),
                        xaxis_opts=opts.AxisOpts(
                            interval=0,

                            axislabel_opts=opts.LabelOpts(
                                font_size=10,
                                # rotate=-45,  # 标签旋转减少重叠
                                margin=15
                            ),
                            axistick_opts=opts.AxisTickOpts(
                                length=8 , # 刻度线长度，可调整为 10、12 等
                                is_align_with_label=True
                            ),
                            # boundary_gap=False,
                            name="",
                            name_location="middle",
                            name_gap=30
                        ),
                        yaxis_opts=opts.AxisOpts(name=""),
                    )
                )

                try:
                    line.options["grid"] = {"left": "2%", "right": "2%", "top": "15%", "bottom": "18%"}
                except Exception:
                    pass
                return line.render_embed()
    except Exception as e:
        current_app.logger.error(f"生成折线图失败: {str(e)}")
    return None


def create_heatmap(results):
    try:
        if results and len(results) > 0 and len(results[0][1]) > 0:
            heatmap_data = []
            data_rows = results[0][1][:5]

            numeric_keys = []
            for row in data_rows:
                for k, v in row.items():
                    try:
                        float(v)
                        if k not in numeric_keys:
                            numeric_keys.append(k)
                    except (ValueError, TypeError):
                        continue
                if len(numeric_keys) >= 10:
                    break

            if len(numeric_keys) >= 1 and len(data_rows) >= 1:
                for y, row in enumerate(data_rows):
                    for x, key in enumerate(numeric_keys):
                        try:
                            value = float(row.get(key, 0))
                            heatmap_data.append([x, y, value])
                        except (ValueError, TypeError):
                            heatmap_data.append([x, y, 0])

                # 固定宽度为2000px，确保超过容器宽度
                heatmap = (
                    HeatMap(init_opts=opts.InitOpts(width="4000px", height="400px"))
                    .add_xaxis(numeric_keys)
                    .add_yaxis(
                        "",
                        [],
                        heatmap_data,
                        label_opts=opts.LabelOpts(
                            is_show=True,
                            formatter=JsCode("function(params){return params.data[2].toFixed(2);}")
                        ),
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title="Heatmap"),
                        visualmap_opts=opts.VisualMapOpts(),

                        xaxis_opts=opts.AxisOpts(
                            type_="category",
                            axislabel_opts=opts.LabelOpts(
                                font_size=10,
                                interval=0,
                                # rotate=45,  # 标签旋转减少重叠
                                margin=15
                            ),
                            axistick_opts=opts.AxisTickOpts(
                                length=8,  # 刻度线长度，与折线图保持一致
                                is_align_with_label=True
                            ),
                            name=""
                        ),
                        yaxis_opts=opts.AxisOpts(
                            type_="category",
                            name=""
                        ),
                    )
                )

                try:
                    heatmap.options["grid"] = {"left": "2%", "right": "2%", "top": "15%", "bottom": "18%"}
                except Exception:
                    pass
                return heatmap.render_embed()
    except Exception as e:
        current_app.logger.error(f"生成热力图失败: {str(e)}")
    return None

def find_associated_gene(query_value, cfg):
    """修改为返回所有关联基因的列表"""
    query_value = query_value.strip()
    associated_genes = []

    # 1. 用names字段查询，获取所有匹配的Transcript_ID
    # rows_by_names = query_one_table(cfg["COLD_LINKS"], "对比基因ID", query_value)
    # if rows_by_names:
    #     associated_genes.extend([row.get("参考基因ID") for row in rows_by_names if row.get("参考基因ID")])

    # 2. 用Transcript_ID字段查询，获取所有匹配的names
    rows_by_transcript = query_one_table(cfg["COLD_LINKS"], "参考基因ID", query_value)
    if rows_by_transcript:
        associated_genes.extend([row.get("对比基因ID") for row in rows_by_transcript if row.get("对比基因ID")])

    # 去重并返回（保持顺序）
    return list(dict.fromkeys(associated_genes))  # 去重但保留首次出现顺序


def get_gene_related_treatments(gene_id):
    """
    从数据库基因-处理矩阵表中，筛选指定基因的有效关联处理
    返回格式：[{
        "name": "前端直接显示的处理名",
        "route": "目标处理页面的路由代码",
        "url": "目标处理页面的URL"
    }, ...]
    """
    # 1. 从config读取表名
    GENE_TREATMENT_TABLE = current_app.config.get(
        "MERGED_GENE_TREATMENT_RESULT",
        "merged_gene_treatment_result"
    )

    # 2. 处理字段映射
    TREATMENT_FIELD_MAP = {
        "bacterial_wilt": {
            "display_name": "Bacterial wilt",
            "route_code": "search_Bacterial_wilt_bp.index"
        },
        "cold_nac_m4_3h": {
            "display_name": "Cold (NAC_M4_3h)",
            "route_code": "search_cold_nac_m4_3h_bp.index"
        },
        "salt_48h": {
            "display_name": "Salt (48h)",
            "route_code": "search_salt_48h_bp.index"
        },
        "tuber_development": {
            "display_name": "Tuber Development",
            "route_code": "search_tuber_development_bp.index"
        },
        "cold_ac_m4_2h": {
            "display_name": "Cold (AC_M4_2h)",
            "route_code": "search_cold_ac_m4_2h_bp.index"
        },
        "cold_ac_candol_m4_2h": {
            "display_name": "Cold (AC_candol_M4_2h)",
            "route_code": "search_cold_ac_candol_m4_2h_bp.index"
        },
        "cold_ac_m3": {
            "display_name": "Cold (AC_M3)",
            "route_code": "search_cold_ac_m3_bp.index"
        },
        "multiple_treatments": {
            "display_name": "multiple_treatments",
            "route_code": "search_multiple_treatments_bp.index"
        }
    }

    related_treatments = []
    try:
        # 检查基因是否存在
        check_gene_sql = f"""
            SELECT 1 FROM {GENE_TREATMENT_TABLE} 
            WHERE Transcript_ID = %s LIMIT 1
        """
        gene_exists = query_db(check_gene_sql, (gene_id,), one=True)
        if not gene_exists:
            return related_treatments

        # 查询处理数据
        treatment_fields = ", ".join(TREATMENT_FIELD_MAP.keys())
        query_sql = f"""
            SELECT {treatment_fields} FROM {GENE_TREATMENT_TABLE} 
            WHERE Transcript_ID = %s
        """
        treatment_data = query_db(query_sql, (gene_id,), one=True)

        # 筛选有效处理并生成URL
        for db_field, config in TREATMENT_FIELD_MAP.items():
            field_value = treatment_data.get(db_field, None)
            if field_value is not None and str(field_value).strip() != "":
                # 生成完整URL
                try:
                    route_url = url_for(config["route_code"], q=gene_id)
                except:
                    route_url = url_for(config["route_code"])

                related_treatments.append({
                    "name": config["display_name"],
                    "route": config["route_code"],
                    "url": route_url  # 新增URL字段
                })

        # 排除当前处理
        related_treatments = [
            t for t in related_treatments
            if t["route"] != "search_cold_ac_candol_m4_2h_bp.index"
        ]
        return related_treatments

    except Exception as e:
        current_app.logger.error(f"查询基因[{gene_id}]关联处理失败：{str(e)}")
        return related_treatments

# 搜索
@search_cold_ac_candol_m4_2h_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()

    results = []
    chart_code = None
    heatmap_code = None
    transcriptomics_results = []
    related_treatments = []
    cfg = current_app.config

    if q:
        # 获取关联处理
        related_treatments = get_gene_related_treatments(q)

    transcript_rows = query_one_table(
        cfg["TRANSCRIPTOMICS_TOOL"],  # 需在config.py中配置表名
        "处理",  # 实际存储胁迫类型的字段名（根据表结构调整）
        "Cold_AC_candol_M4_2h"  # 固定搜索关键词
    )
    if transcript_rows:
        transcriptomics_results.append(("Transcriptomics Tool Data", transcript_rows))

    if q:
        rows_c804 = query_one_table(cfg["COLD_AC_CANDOL_M4_2H_REF_C804"], "Transcript_ID", q)
        if rows_c804:
            results.append((cfg["COLD_AC_CANDOL_M4_2H_REF_C804"], rows_c804))

        rows_c882 = query_one_table(cfg["COLD_AC_CANDOL_M4_2H_REF_C882"], "Transcript_ID", q)
        if rows_c882:
            results.append((cfg["COLD_AC_CANDOL_M4_2H_REF_C882"], rows_c882))

        rows_c830 = query_one_table(cfg["COLD_AC_CANDOL_M4_2H_REF_C830"], "Transcript_ID", q)
        if rows_c830:
            results.append((cfg["COLD_AC_CANDOL_M4_2H_REF_C830"], rows_c830))

        rows_c454 = query_one_table(cfg["COLD_AC_CANDOL_M4_2H_REF_C454"], "Transcript_ID", q)
        if rows_c454:
            results.append((cfg["COLD_AC_CANDOL_M4_2H_REF_C454"], rows_c454))

        rows_dm = query_one_table(cfg["COLD_AC_CANDOL_M4_2H_REF_DM"], "Transcript_ID", q)
        if rows_dm:
            results.append((cfg["COLD_AC_CANDOL_M4_2H_REF_DM"], rows_dm))

        rows_t206 = query_one_table(cfg["COLD_AC_CANDOL_M4_2H_REF_T206"], "Transcript_ID", q)
        if rows_t206:
            results.append((cfg["COLD_AC_CANDOL_M4_2H_REF_T206"], rows_t206))

        if results:
            chart_code = create_line_chart(results)
            heatmap_code = create_heatmap(results)
    associated_genes = find_associated_gene(q, cfg) if q else []

    print("Related Treatments:")
    for treatment in related_treatments:
        print(f"- Name: {treatment.get('name')}, URL: {treatment.get('url')}")
        # 检查 URL 是否对应 search_Bacterial_wilt_bp.index 路由
        if 'search_cold_ac_candol_m4_2h_bp.index' in str(treatment.get('url')):
            print(f"  ✅ 包含目标路由: ssearch_cold_ac_candol_m4_2h_bp.index")

    # 如果 related_treatments 为空
    if not related_treatments:
        print("Related Treatments is empty")

    return render_template(
        "search_cold_ac_candol_m4_2h.html",
        q=q,
        results=results,
        chart_code=chart_code,
        heatmap_code=heatmap_code,
        associated_genes=associated_genes,
        tbl804=cfg["COLD_AC_CANDOL_M4_2H_REF_C804"],
        tbl882=cfg["COLD_AC_CANDOL_M4_2H_REF_C882"],
        tbl830=cfg["COLD_AC_CANDOL_M4_2H_REF_C830"],
        tbldm=cfg["COLD_AC_CANDOL_M4_2H_REF_DM"],
        tbl206=cfg["COLD_AC_CANDOL_M4_2H_REF_T206"],
        tbl454=cfg["COLD_AC_CANDOL_M4_2H_REF_C454"],
        transcriptomics_results=transcriptomics_results,
        related_treatments=related_treatments


    )