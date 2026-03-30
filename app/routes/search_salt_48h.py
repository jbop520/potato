from flask import Blueprint, render_template, request, current_app, url_for
from ..db import query_one_table, query_db  # 确保导入query_db
from pyecharts.charts import Line, HeatMap
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

search_salt_48h_bp = Blueprint("search_salt_48h_bp", __name__)


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
                    numeric_keys.append(str(k))
                except (ValueError, TypeError):
                    continue

            if not numeric_keys:
                return None

            line = (
                Line(init_opts=opts.InitOpts(width="3000px", height="400px"))
                .add_xaxis(numeric_keys)
                .add_yaxis("", numeric_values)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=" Line Graph"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    xaxis_opts=opts.AxisOpts(
                        interval=0,
                        axislabel_opts=opts.LabelOpts(font_size=10, margin=15),
                        axistick_opts=opts.AxisTickOpts(length=8, is_align_with_label=True),
                        name="",
                        name_location="middle",
                        name_gap=30,
                        boundary_gap=False,
                    ),
                    yaxis_opts=opts.AxisOpts(name=""),
                )
            )

            try:
                line.options["grid"] = {"left": "2%", "right": "2%", "top": "12%", "bottom": "18%"}
            except Exception:
                pass

            return line.render_embed()
    except Exception as e:
        try:
            current_app.logger.error(f"生成折线图失败: {str(e)}")
        except Exception:
            pass
    return None


#def create_heatmap(results):
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

                heatmap = (
                    HeatMap(init_opts=opts.InitOpts(width="7000px", height="400px"))
                    .add_xaxis(numeric_keys)
                    .add_yaxis(
                        "",
                        [f"Sample {i + 1}" for i in range(len(data_rows))],  # 添加Y轴标签
                        heatmap_data,
                        label_opts=opts.LabelOpts(
                            is_show=True,
                            formatter=JsCode("function(params){return params.data[2].toFixed(2);}")
                        ),
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=" Heatmap"),
                        visualmap_opts=opts.VisualMapOpts(),
                        xaxis_opts=opts.AxisOpts(
                            type_="category",
                            axislabel_opts=opts.LabelOpts(
                                font_size=10,
                                interval=0,
                                margin=15
                            ),
                            axistick_opts=opts.AxisTickOpts(
                                length=8,
                                is_align_with_label=True
                            ),
                        ),
                        yaxis_opts=opts.AxisOpts(
                            type_="category",
                            name=""
                        ),
                    )
                )

                try:
                    heatmap.options["grid"] = {"left": "2%", "right": "2%", "top": "20%", "bottom": "18%"}
                except Exception:
                    pass
                return heatmap.render_embed()
    except Exception as e:
        current_app.logger.error(f"生成热力图失败: {str(e)}")
    return None

import math


def create_heatmap(results):
    """生成热力图，使用Log2转换提高区分度"""

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
                # 收集所有转换后的值以计算最小值和最大值
                transformed_values = []

                for y, row in enumerate(data_rows):
                    for x, key in enumerate(numeric_keys):
                        try:
                            original_value = float(row.get(key, 0))

                            # Log2转换处理
                            if original_value > 0:
                                transformed_value = math.log2(original_value)
                            else:
                                transformed_value = 0  # 0或负值处理为0

                            heatmap_data.append([x, y, transformed_value])
                            transformed_values.append(transformed_value)

                        except (ValueError, TypeError, OverflowError):
                            heatmap_data.append([x, y, 0])
                            transformed_values.append(0)

                # 计算最小值和最大值
                if transformed_values:
                    min_val = min(transformed_values)
                    max_val = max(transformed_values)

                    # 如果最小值和最大值相等，设置一个默认范围
                    if min_val == max_val:
                        min_val = max_val - 1 if max_val > 0 else 0
                        max_val = max_val + 1
                else:
                    min_val, max_val = 0, 10

                heatmap = (
                    HeatMap(init_opts=opts.InitOpts(width="7000px", height="400px"))
                    .add_xaxis(numeric_keys)
                    .add_yaxis(
                        "",
                        [f"Sample {i + 1}" for i in range(len(data_rows))],
                        heatmap_data,
                        label_opts=opts.LabelOpts(
                            is_show=True,
                            formatter=JsCode("function(params){return params.data[2].toFixed(2);}")
                        ),
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title=" Heatmap (Log2 transformed)"),
                        visualmap_opts=opts.VisualMapOpts(
                            min_=min_val,
                            max_=max_val,
                            range_color=["#313695", "#4575b4", "#74add1", "#abd9e9",
                                         "#e0f3f8", "#ffffbf", "#fee090", "#fdae61",
                                         "#f46d43", "#d73027", "#a50026"]
                        ),
                        xaxis_opts=opts.AxisOpts(
                            type_="category",
                            axislabel_opts=opts.LabelOpts(
                                font_size=10,
                                interval=0,
                                margin=15
                            ),
                            axistick_opts=opts.AxisTickOpts(
                                length=8,
                                is_align_with_label=True
                            ),
                        ),
                        yaxis_opts=opts.AxisOpts(
                            type_="category",
                            name=""
                        ),
                    )
                )

                try:
                    heatmap.options["grid"] = {"left": "2%", "right": "2%", "top": "20%", "bottom": "18%"}
                except Exception:
                    pass

                return heatmap.render_embed()
    except Exception as e:
        current_app.logger.error(f"生成热力图失败: {str(e)}")
    return None


def find_associated_gene(query_value, cfg):
    """获取所有关联基因的列表"""
    query_value = query_value.strip()
    associated_genes = []

    rows_by_transcript = query_one_table(cfg["COLD_LINKS"], "参考基因ID", query_value)
    if rows_by_transcript:
        associated_genes.extend([row.get("对比基因ID") for row in rows_by_transcript if row.get("对比基因ID")])

    return list(dict.fromkeys(associated_genes))  # 去重并保留顺序


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
    EXCLUDE_ROUTE = "search_salt_48h_bp.index"

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
            if config["route_code"] == EXCLUDE_ROUTE:
                continue

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


@search_salt_48h_bp.route("/", methods=["GET"])
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

    # 查询transcriptomics_tool表数据
    transcript_rows = query_one_table(
        cfg.get("TRANSCRIPTOMICS_TOOL", ""),
        "处理",
        "Salt_48h"
    )
    if transcript_rows:
        transcriptomics_results.append(("Transcriptomics Tool Data", transcript_rows))

    if q:
        # 细菌枯萎相关数据表查询
        rows_c804 = query_one_table(cfg.get("SALT_48H_REF_C804", ""), "Transcript_ID", q)
        if rows_c804:
            results.append((cfg["SALT_48H_REF_C804"], rows_c804))

        rows_c882 = query_one_table(cfg.get("SALT_48H_REF_C882", ""), "Transcript_ID", q)
        if rows_c882:
            results.append((cfg["SALT_48H_REF_C882"], rows_c882))

        rows_c830 = query_one_table(cfg.get("SALT_48H_REF_C830", ""), "Transcript_ID", q)
        if rows_c830:
            results.append((cfg["SALT_48H_REF_C830"], rows_c830))

        rows_c454 = query_one_table(cfg.get("SALT_48H_REF_C454", ""), "Transcript_ID", q)
        if rows_c454:
            results.append((cfg["SALT_48H_REF_C454"], rows_c454))

        rows_dm = query_one_table(cfg.get("SALT_48H_REF_DM", ""), "Transcript_ID", q)
        if rows_dm:
            results.append((cfg["SALT_48H_REF_DM"], rows_dm))

        rows_t206 = query_one_table(cfg.get("SALT_48H_REF_T206", ""), "Transcript_ID", q)
        if rows_t206:
            results.append((cfg["SALT_48H_REF_T206"], rows_t206))

        # 生成图表
        if results:
            chart_code = create_line_chart(results)
            heatmap_code = create_heatmap(results)

    # 获取关联基因
    associated_genes = find_associated_gene(q, cfg) if q else []

    # print("Related Treatments:")
    # for treatment in related_treatments:
    #     print(f"- Name: {treatment.get('name')}, URL: {treatment.get('url')}")
    #     # 检查 URL 是否对应 search_Bacterial_wilt_bp.index 路由
    #     if 'search_Bacterial_wilt_bp.index' in str(treatment.get('url')):
    #         print(f"  ✅ 包含目标路由: search_Bacterial_wilt_bp.index")
    #
    # # 如果 related_treatments 为空
    # if not related_treatments:
    #     print("Related Treatments is empty")


    return render_template(
        "search_salt_48h.html",
        q=q,
        results=results,
        chart_code=chart_code,
        heatmap_code=heatmap_code,
        associated_genes=associated_genes,
        tbl804=cfg.get("SALT_48H_REF_C804", ""),
        tbl882=cfg.get("SALT_48H_REF_C882", ""),
        tbl830=cfg.get("SALT_48H_REF_C830", ""),
        tbldm=cfg.get("SALT_48H_REF_DM", ""),
        tbl206=cfg.get("SALT_48H_REF_T206", ""),
        tbl454=cfg.get("SALT_48H_REF_C454", ""),
        transcriptomics_results=transcriptomics_results,
        related_treatments=related_treatments
    )