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


from flask import Blueprint, render_template, request, current_app
from ..db import query_one_table
from pyecharts.charts import Line, HeatMap
from pyecharts import options as opts

# 调整JsCode的导入路径，兼容旧版本pyecharts
try:
    from pyecharts import JsCode  # 适用于较新版本
except ImportError:
    from pyecharts.commons.utils import JsCode  # 适用于旧版本
from pyecharts.options import AxisTickOpts
from pyecharts import options as opts
search_multiple_treatments_bp = Blueprint("search_multiple_treatments_bp", __name__)


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
                    Line(init_opts=opts.InitOpts(width="1000px", height="400px"))
                    .add_xaxis(numeric_keys)
                    .add_yaxis("数据值", numeric_values)
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title="数据折线图"),
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
                            name="属性",
                            name_location="middle",
                            name_gap=30
                        ),
                        yaxis_opts=opts.AxisOpts(name="数值"),
                    )
                )
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
                    HeatMap(init_opts=opts.InitOpts(width="1000px", height="400px"))
                    .add_xaxis(numeric_keys)
                    .add_yaxis(
                        "数据行",
                        [f"记录 {i + 1}" for i in range(len(data_rows))],
                        heatmap_data,
                        label_opts=opts.LabelOpts(
                            is_show=True,
                            formatter=JsCode("function(params){return params.data[2].toFixed(2);}")
                        ),
                    )
                    .set_global_opts(
                        title_opts=opts.TitleOpts(title="数据热力图"),
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
                            name="属性"
                        ),
                        yaxis_opts=opts.AxisOpts(
                            type_="category",
                            name="数据记录"
                        ),
                    )
                )
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




# 搜索
@search_multiple_treatments_bp.route("/", methods=["GET"])
def index():
    q = (request.args.get("q") or "").strip()

    results = []
    chart_code = None
    heatmap_code = None
    cfg = current_app.config

    if q:
        rows_c804 = query_one_table(cfg["MULTIPLE_TREATMENTS_REF_C804"], "Transcript_ID", q)
        if rows_c804:
            results.append((cfg["MULTIPLE_TREATMENTS_REF_C804"], rows_c804))

        rows_c882 = query_one_table(cfg["MULTIPLE_TREATMENTS_REF_C882"], "Transcript_ID", q)
        if rows_c882:
            results.append((cfg["MULTIPLE_TREATMENTS_REF_C882"], rows_c882))

        rows_c830 = query_one_table(cfg["MULTIPLE_TREATMENTS_REF_C830"], "Transcript_ID", q)
        if rows_c830:
            results.append((cfg["MULTIPLE_TREATMENTS_REF_C830"], rows_c830))

        rows_c454 = query_one_table(cfg["MULTIPLE_TREATMENTS_REF_C454"], "Transcript_ID", q)
        if rows_c454:
            results.append((cfg["MULTIPLE_TREATMENTS_REF_C454"], rows_c454))

        rows_dm = query_one_table(cfg["MULTIPLE_TREATMENTS_REF_DM"], "Transcript_ID", q)
        if rows_dm:
            results.append((cfg["MULTIPLE_TREATMENTS_REF_DM"], rows_dm))

        rows_t206 = query_one_table(cfg["MULTIPLE_TREATMENTS_REF_T206"], "Transcript_ID", q)
        if rows_t206:
            results.append((cfg["MULTIPLE_TREATMENTS_REF_T206"], rows_t206))

        if results:
            chart_code = create_line_chart(results)
            heatmap_code = create_heatmap(results)
    associated_genes = find_associated_gene(q, cfg) if q else []

    return render_template(
        "search_multiple_treatments.html",
        q=q,
        results=results,
        chart_code=chart_code,
        heatmap_code=heatmap_code,
        associated_genes=associated_genes,
        tbl804=cfg["MULTIPLE_TREATMENTS_REF_C804"],
        tbl882=cfg["MULTIPLE_TREATMENTS_REF_C882"],
        tbl830=cfg["MULTIPLE_TREATMENTS_REF_C830"],
        tbldm=cfg["MULTIPLE_TREATMENTS_REF_DM"],
        tbl206=cfg["MULTIPLE_TREATMENTS_REF_T206"],
        tbl454=cfg["MULTIPLE_TREATMENTS_REF_C454"],


    )