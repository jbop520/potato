from flask import Blueprint, render_template, request, current_app, redirect, url_for
from ..db import query_one_table

search2_bp = Blueprint("search2_bp", __name__)


def find_associated_gene(query_value, cfg):
    """
    在lins表中查找关联的基因信息
    返回: 如果找到，返回对应的另一个属性值；否则返回None
    """
    query_value = query_value.strip()
    #print("query_value:", query_value)
    # 先尝试用names字段查询
    rows_by_names = query_one_table(cfg["LINKS_804_882"], "names", query_value)
    if rows_by_names:
        # 如果通过names找到，返回对应的Transcript_ID
        return rows_by_names[0].get("Transcript_ID")

    # 再尝试用Transcript_ID字段查询
    rows_by_transcript = query_one_table(cfg["LINKS_804_882"], "Transcript_ID", query_value)
    if rows_by_transcript:
        # 如果通过Transcript_ID找到，返回对应的names
        return rows_by_transcript[0].get("names")

    return None


@search2_bp.route("/", methods=["GET"])
def index():
    # 1. 获取并处理查询词q
    q = request.args.get("q", "").strip()  # 简化写法，q默认是空字符串
    cfg = current_app.config
    #print("hello")  # 用于验证函数是否进入
    #print(q)

    # 2. 路径1：q为空→重定向到search1首页
    if not q:
        print("q为空，重定向到search1首页")  # 调试日志
        return redirect(url_for("search_bp.index"))

    # 3. 路径2：q不为空→查询关联基因
    associated_value = find_associated_gene(q, cfg)
    print(f"associated_value: {associated_value}")  # 打印关联结果，方便调试

    # 3.1 路径2.1：找到关联基因→重定向到search1显示关联结果
    if associated_value:
        print(f"找到关联基因：{associated_value}，重定向到search1")
        return redirect(url_for("search_bp.index", q=associated_value))

    # 3.2 路径2.2：未找到关联基因→重定向回search1，带提示参数
    print("未找到关联基因，重定向回search1并提示")
    return redirect(url_for("search_bp.index", q=q, no_associate="true"))