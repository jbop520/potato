from flask import Blueprint, render_template

index_bp = Blueprint(
    "index_bp",
    __name__,
    template_folder="../templates"  )
# index_bp = Blueprint("index_bp", __name__)

@index_bp.route("/")
def index():
    # print("index")
    return render_template("index.html")
    return "<h1>欢迎来到主页</h1><a href=' '>去搜索</a >"