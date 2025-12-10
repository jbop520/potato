from flask import Blueprint, render_template, request, current_app
from ..db import query_one_table
from pyecharts.charts import Line, HeatMap
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode


search_Bacterial_wilt_bp = Blueprint("search_Bacterial_wilt_bp", __name__)


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
                Line(init_opts=opts.InitOpts(width="7000px", height="400px"))
                .add_xaxis(numeric_keys)
                .add_yaxis("", numeric_values)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="Line Graph"),
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

                heatmap = (
                    HeatMap(init_opts=opts.InitOpts(width="7000px", height="400px"))
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


@search_Bacterial_wilt_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()

    results = []
    chart_code = None
    heatmap_code = None
    transcriptomics_results = []  # 存储transcriptomics_tool表的查询结果
    cfg = current_app.config

    # 无论是否有搜索词，都查询transcriptomics_tool表中与bacterial_wilt相关的数据
    # 首次进入页面时自动加载，有搜索词时同时显示
    transcript_rows = query_one_table(
        cfg["TRANSCRIPTOMICS_TOOL"],  # 需在config.py中配置表名
        "处理",  # 实际存储胁迫类型的字段名（根据表结构调整）
        "Bacterial_wilt"  # 固定搜索关键词
    )
    if transcript_rows:
        transcriptomics_results.append(("Transcriptomics Tool Data", transcript_rows))

    if q:
        # 原有细菌枯萎相关数据表查询逻辑
        rows_c804 = query_one_table(cfg["BACTERIAL_WILT_REF_C804"], "Transcript_ID", q)
        if rows_c804:
            results.append((cfg["BACTERIAL_WILT_REF_C804"], rows_c804))

        rows_c882 = query_one_table(cfg["BACTERIAL_WILT_REF_C882"], "Transcript_ID", q)
        if rows_c882:
            results.append((cfg["BACTERIAL_WILT_REF_C882"], rows_c882))

        rows_c830 = query_one_table(cfg["BACTERIAL_WILT_REF_C830"], "Transcript_ID", q)
        if rows_c830:
            results.append((cfg["BACTERIAL_WILT_REF_C830"], rows_c830))

        rows_c454 = query_one_table(cfg["BACTERIAL_WILT_REF_C454"], "Transcript_ID", q)
        if rows_c454:
            results.append((cfg["BACTERIAL_WILT_REF_C454"], rows_c454))

        rows_dm = query_one_table(cfg["BACTERIAL_WILT_REF_DM"], "Transcript_ID", q)
        if rows_dm:
            results.append((cfg["BACTERIAL_WILT_REF_DM"], rows_dm))

        rows_t206 = query_one_table(cfg["BACTERIAL_WILT_REF_T206"], "Transcript_ID", q)
        if rows_t206:
            results.append((cfg["BACTERIAL_WILT_REF_T206"], rows_t206))

        # 生成图表
        if results:
            chart_code = create_line_chart(results)
            heatmap_code = create_heatmap(results)

    # 获取关联基因
    associated_genes = find_associated_gene(q, cfg) if q else []

    return render_template(
        "search_Bacterial_wilt.html",
        q=q,
        results=results,
        chart_code=chart_code,
        heatmap_code=heatmap_code,
        associated_genes=associated_genes,
        tbl804=cfg["BACTERIAL_WILT_REF_C804"],
        tbl882=cfg["BACTERIAL_WILT_REF_C882"],
        tbl830=cfg["BACTERIAL_WILT_REF_C830"],
        tbldm=cfg["BACTERIAL_WILT_REF_DM"],
        tbl206=cfg["BACTERIAL_WILT_REF_T206"],
        tbl454=cfg["BACTERIAL_WILT_REF_C454"],
        transcriptomics_results=transcriptomics_results  # 传递transcriptomics数据到模板
    )