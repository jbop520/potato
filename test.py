from pyecharts.charts import Line
from pyecharts import options as opts
from flask import current_app

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

            max_labels_shown = 50  # 希望在视图中最多显示多少个刻度标签
            label_interval = 0
            n = len(numeric_keys)
            if n > max_labels_shown:
                # interval 为整数：显示每隔 interval 个标签（0 表示全部显示）
                label_interval = max(1, n // max_labels_shown)

            line = (
                Line(init_opts=opts.InitOpts(width="100%", height="420px"))
                .add_xaxis(numeric_keys)
                .add_yaxis(
                    series_name="数据值",
                    y_axis=numeric_values,
                    is_smooth=False,
                    symbol="circle",
                    symbol_size=6,
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="数据折线图"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
                    xaxis_opts=opts.AxisOpts(
                        type_="category",
                        boundary_gap=False,  # 关闭左右留白
                        axislabel_opts=opts.LabelOpts(
                            font_size=10,
                            margin=12,
                            rotate=45,            # 标签旋转
                            interval=label_interval  # 只显示部分标签时可避免拥挤
                        ),
                        axistick_opts=opts.AxisTickOpts(is_align_with_label=True),
                        name="属性",
                        name_location="middle",
                        name_gap=30,
                    ),
                    yaxis_opts=opts.AxisOpts(name="数值"),
                    grid_opts=opts.GridOpts(left="5%", right="5%", top="12%", bottom="18%"),
                    datazoom_opts=[
                        # 页面上出现滑动条，并允许鼠标滚轮缩放
                        opts.DataZoomOpts(type_="slider", range_start=0, range_end=100),
                        opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
                    ],
                )
            )

            return line.render_embed()
    except Exception as e:
        try:
            current_app.logger.error(f"生成折线图失败: {str(e)}")
        except Exception:
            pass
    return None
