from flask import Flask
from .config import Config
from .routes.index import index_bp
from .routes.search import search_bp
from .routes.search1 import search2_bp

from .routes.files import files_bp
from .routes.search_Bacterial_wilt import search_Bacterial_wilt_bp
from .routes.search_cold import search_cold_bp
from .routes.search_cold_ac_candol_m4_2h import search_cold_ac_candol_m4_2h_bp
from .routes.search_cold_ac_m3 import search_cold_ac_m3_bp
from .routes.search_cold_ac_m4_2h import search_cold_ac_m4_2h_bp
from .routes.search_cold_nac_m4_3h import search_cold_nac_m4_3h_bp
from .routes.search_hot import search_hot_bp
from .routes.search_multiple_treatments import search_multiple_treatments_bp
from .routes.search_transcriptomics import search_transcriptomics_bp
from .routes.search_tuber_development import search_tuber_development_bp
from .routes.transcriptomics_cold_tool import transcriptomics_cold_tool_bp
from .routes.transcriptomics_tool import transcriptomics_tool_bp


def create_app():
    app = Flask(__name__)
    # app = Flask(__name__, template_folder="app/templates")
    app.config.from_object(Config)
    app.register_blueprint(index_bp)# 首页
    app.register_blueprint(search_bp,url_prefix='/search')# 查询

    app.register_blueprint(search_cold_bp, url_prefix='/search_cold_bp')
    app.register_blueprint(search_hot_bp, url_prefix='/search_hot_bp')
    app.register_blueprint(search_transcriptomics_bp, url_prefix='/search_transcriptomics_bp')
    app.register_blueprint(search2_bp,url_prefix='/search2')#连接查询
    app.register_blueprint(files_bp, url_prefix="/files")  # 文件浏览/下载
    app.register_blueprint(transcriptomics_tool_bp, url_prefix='/transcriptomics_tool_bp')
    app.register_blueprint(search_tuber_development_bp, url_prefix='/search_tuber_development_bp')
    app.register_blueprint(search_Bacterial_wilt_bp, url_prefix='/search_Bacterial_wilt_bp')
    app.register_blueprint(search_multiple_treatments_bp, url_prefix='/search_multiple_treatments_bp')
    app.register_blueprint(search_cold_ac_m4_2h_bp, url_prefix='/search_cold_ac_m4_2h_bp')
    app.register_blueprint(search_cold_ac_m3_bp, url_prefix='/search_cold_ac_m3_bp')
    app.register_blueprint(search_cold_ac_candol_m4_2h_bp, url_prefix='/search_cold_ac_candol_m4_2h_bp')
    app.register_blueprint(transcriptomics_cold_tool_bp, url_prefix='/transcriptomics_cold_tool_bp')
    app.register_blueprint(search_cold_nac_m4_3h_bp, url_prefix='/search_cold_nac_m4_3h_bp')
    return app
