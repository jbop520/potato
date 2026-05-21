import os
import pandas as pd
from flask import render_template, request, send_file, Blueprint, current_app, g
import sqlite3
from ..db import query_db  # 导入数据库查询函数

# 创建蓝图
file_view_bp = Blueprint(
    'file_view',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/file_view'
)

# ========== 核心配置 ==========
ALLOWED_EXTENSIONS = {
    'txt': 'text',
    'csv': 'table',
    'tsv': 'table',
    'log': 'text',
    'md': 'text',
    'json': 'text',
    'xlsx': 'table',
    'fa': 'text',
    'fasta': 'text',
    'gff3': 'text'
}
PAGE_SIZE = 500  # 仅读取前500行
MAX_READ_BYTES = 1 * 1024 * 1024  # 最大读取1MB
ROOT_WHITELIST = [
    "/Users/chenyongtao/Code/potato"  # 替换为你的根目录
]
DEFAULT_ROOT = "/Users/chenyongtao/Code/potato/Genomics/C454"  # 替换为文件目录
BASE_GENOME_PATH = "/Users/chenyongtao/Code/potato/Genomics"  # 基因组文件的基础路径
GENOMICS_EXCEL_PATH = "/Users/chenyongtao/Code/potato/Genomics/genomics_show.xlsx"  # Excel文件路径


# ========== 安全校验 ==========
def allowed_path(path):
    try:
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(root) for root in ROOT_WHITELIST) and os.path.exists(abs_path)
    except:
        return False


def allowed_file(filename):
    try:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in ALLOWED_EXTENSIONS
    except:
        return False


# ========== 目录/文件列表 ==========
def get_file_list(current_dir):
    """获取当前目录下的子目录和文件列表"""
    dirs = []
    files = []
    if not allowed_path(current_dir):
        return dirs, files

    try:
        for name in os.listdir(current_dir):
            full_path = os.path.join(current_dir, name)
            if name.startswith('.'):
                continue

            if os.path.isdir(full_path) and allowed_path(full_path):
                dirs.append(name)
            elif os.path.isfile(full_path) and allowed_file(name):
                files.append(name)
    except Exception as e:
        current_app.logger.error(f"读取目录失败: {current_dir}, 错误: {str(e)}")

    return sorted(dirs), sorted(files)


# ========== 从Excel文件获取基因组信息 ==========
def get_genome_info_from_excel():
    """从Excel文件获取所有基因组信息"""
    try:
        # 检查Excel文件是否存在
        if not os.path.exists(GENOMICS_EXCEL_PATH):
            return [], [], f"Excel文件不存在: {GENOMICS_EXCEL_PATH}"

        # 读取Excel文件，header=1表示第二行为列名（跳过第一行的"T2T genome assembly"）
        df = pd.read_excel(GENOMICS_EXCEL_PATH, sheet_name=0, header=1)

        # 清理数据：删除全为空的行
        df = df.dropna(how='all')

        # 重命名列，使其更友好（去掉空格和特殊字符）
        df.columns = [col.strip().replace(' ', '_').replace('/', '_') for col in df.columns]

        # 转换为字典列表
        records = df.to_dict('records')

        # 获取列名
        columns = list(df.columns)

        # 检查是否有数据
        if not records:
            return columns, [], f"Excel文件中没有数据"

        # 添加一些处理信息
        info = f"成功从Excel读取 {len(records)} 条记录"
        current_app.logger.info(info)

        return columns, records, info

    except Exception as e:
        current_app.logger.error(f"Excel文件读取错误: {str(e)}")
        return [], [], f"Excel文件读取错误: {str(e)}"


# ========== 生成带链接的HTML表格（可滚动） ==========
# ========== 生成带链接的HTML表格（可滚动） ==========
def generate_html_table_from_excel(columns, rows, current_dir):
    """从Excel数据生成带链接的HTML表格，支持横向和纵向滚动"""
    try:
        if not rows:
            return '<div class="tip">📭 Excel文件中没有数据</div>'

        # 包装一个滚动容器
        html = '<div class="table-scroll-wrapper" style="overflow-x:auto; overflow-y:auto; max-height:500px; border:1px solid #dee2e6; border-radius:6px; padding:10px;">'

        # 创建HTML表格
        html += '<table class="data-table" style="border-collapse: collapse; width: max-content; min-width: 100%;">'
        html += '<thead><tr>'

        # 添加表头
        for col in columns:
            display_col = col.replace('_', ' ')
            html += f'<th style="border: 1px solid #dee2e6; padding: 8px; background-color: #f8f9fa; white-space: nowrap;">{display_col}</th>'
        html += '</tr></thead><tbody>'

        # 查找Accession列的索引
        accession_col = None
        for col in columns:
            if 'accession' in col.lower():
                accession_col = col
                break

        # 添加数据行
        for row in rows:
            html += '<tr>'
            for col in columns:
                # 获取单元格值，如果是NaN或None则显示为空字符串
                cell_value = row.get(col, '')

                # 处理NaN值（pandas的NaN）
                if pd.isna(cell_value):
                    cell_value = ''
                else:
                    cell_value = str(cell_value)

                # 处理'nan'字符串
                if cell_value.lower() == 'nan':
                    cell_value = ''

                # Accession列特殊处理
                if col == accession_col and cell_value.strip():
                    folder_path = os.path.join(BASE_GENOME_PATH, cell_value.strip())
                    path_exists = os.path.exists(folder_path) and allowed_path(folder_path)

                    if path_exists:
                        cell_display = f'''
                        <form method="POST" class="accession-form" style="display: inline;">
                            <input type="hidden" name="current_dir" value="{folder_path}">
                            <input type="hidden" name="action" value="goto_folder">
                            <input type="hidden" name="from_excel" value="true">
                            <button type="submit" class="accession-link" 
                                    title="点击跳转到 {cell_value.strip()} 文件夹"
                                    style="background: none; border: none; color: #0d6efd; 
                                           text-decoration: underline; cursor: pointer; padding: 0;
                                           font-weight: bold;">
                                {cell_value.strip()}
                            </button>
                        </form>
                        '''
                    else:
                        cell_display = f'<span title="文件夹 {cell_value.strip()} 不存在或无权访问" style="color: #6c757d;">{cell_value.strip()}</span>'
                else:
                    # 普通单元格，如果是空值则显示为空，否则显示原内容
                    if cell_value == '':
                        cell_display = ''  # 完全空白的单元格
                    else:
                        cell_display = cell_value

                # 添加单元格，空单元格会显示为空白
                html += f'<td style="border: 1px solid #dee2e6; padding: 8px; white-space: nowrap;">{cell_display}</td>'

            html += '</tr>'

        html += '</tbody></table>'
        html += '</div>'  # 滚动容器结束

        # 添加提示信息
        total_rows = len(rows)
        excel_file_name = os.path.basename(GENOMICS_EXCEL_PATH)
        html += f'''
        <div class="tip" style="margin-top: 10px; font-size: 13px;">
            📊 共 {total_rows} 条基因组记录 | 
            📁 <strong>点击Accession字段</strong>可跳转到对应文件夹 |
            💾 数据来源：Excel文件 "{excel_file_name}"
        </div>
        '''

        return html

    except Exception as e:
        current_app.logger.error(f"表格生成失败: {str(e)}")
        return f'<div class="error-tip">⚠ 表格生成失败：{str(e)}</div>'

# ========== 文件内容解析 ==========
def parse_file_content(file_path, current_dir):
    """解析文件内容，统一为表格显示"""
    try:
        ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''

        # Excel 文件提示
        if ext == 'xlsx':
            return '''
            <div class="tip">
                📊 这是一个Excel文件 (.xlsx)<br>
                💡 <strong>请点击左侧"数据库"按钮查看基因组信息</strong>
            </div>
            '''

        file_type = ALLOWED_EXTENSIONS.get(ext, 'text')

        # 表格类文件 CSV/TSV
        if file_type == 'table':
            sep = '\t' if ext == 'tsv' else ','
            try:
                df = pd.read_csv(
                    file_path,
                    sep=sep,
                    nrows=PAGE_SIZE,
                    dtype=str,
                    na_filter=False,
                    on_bad_lines='skip',
                    encoding = 'gbk'
                )
                if df.empty:
                    return '<div class="tip">📝 文件前500行无数据</div>'

                # 转换为可滚动表格
                html_table = df_to_scrollable_html(df)
                return html_table
            except Exception as e:
                current_app.logger.error(f"CSV/TSV解析失败: {str(e)}")
                return f'<div class="error-tip">⚠ CSV/TSV解析失败：{str(e)}</div>'

        # 文本文件
        else:
            return text_file_to_scrollable_table(file_path)

    except Exception as e:
        current_app.logger.error(f"文件读取失败: {str(e)}")
        return f'<div class="error-tip">⚠ 文件读取失败：{str(e)}</div>'


def df_to_scrollable_html(df):
    """将 Pandas DataFrame 转为可滚动表格 HTML"""
    html = '<div class="table-scroll-wrapper" style="overflow-x:auto; overflow-y:auto; max-height:500px; border:1px solid #dee2e6; border-radius:6px; padding:10px;">'
    html += '<table class="data-table" style="border-collapse: collapse; width: max-content; min-width: 100%;">'

    # 表头
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th style="border:1px solid #dee2e6; padding:8px; background-color:#f8f9fa; white-space: nowrap;text-align: left;">{col}</th>'
    html += '</tr></thead><tbody>'

    # 数据行
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            cell_value = str(row[col])
            html += f'<td style="border:1px solid #dee2e6; padding:8px; white-space: nowrap;">{cell_value}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'

    html += f'<div class="tip" style="margin-top:10px; font-size:13px;">📊 仅显示前{PAGE_SIZE}行</div>'
    return html


def text_file_to_scrollable_table(file_path):
    """将普通文本文件每行作为一行表格显示"""
    try:
        encodings = ['utf-8', 'gbk', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'rb') as f:
                    raw_data = f.read(MAX_READ_BYTES)
                text_data = raw_data.decode(encoding, errors='replace')
                lines = text_data.splitlines()[:PAGE_SIZE]

                html = '<div class="table-scroll-wrapper" style="overflow-x:auto; overflow-y:auto; max-height:500px; border:1px solid #dee2e6; border-radius:6px; padding:10px;">'
                html += '<table class="data-table" style="border-collapse: collapse; width: max-content; min-width: 100%;">'
                html += '<thead><tr><th style="border:1px solid #dee2e6; padding:8px; background-color:#f8f9fa;">内容</th></tr></thead><tbody>'
                for line in lines:
                    html += f'<tr><td style="border:1px solid #dee2e6; padding:8px; white-space: nowrap;">{line}</td></tr>'
                html += '</tbody></table></div>'

                if len(lines) >= PAGE_SIZE:
                    html += f'<div class="tip">📄 文件过大，仅显示前{PAGE_SIZE}行</div>'
                return html
            except UnicodeDecodeError:
                continue
        return f'<div class="error-tip">⚠ 文件编码解析失败（尝试：{", ".join(encodings)}）</div>'
    except Exception as e:
        current_app.logger.error(f"文本文件读取失败: {str(e)}")
        return f'<div class="error-tip">⚠ 文件读取失败：{str(e)}</div>'


# ========== 核心路由 ==========
@file_view_bp.route('/file-explorer', methods=['GET', 'POST'])
def index():
    """文件浏览器主页面"""
    current_dir = request.form.get('current_dir', DEFAULT_ROOT)
    selected_file = request.form.get('selected_file', '')
    show_excel = request.form.get('show_excel', 'true') == 'true'  # 默认显示Excel数据
    file_content = ""

    # 从Excel获取数据（默认显示）
    excel_columns = []
    excel_rows = []
    excel_message = ""
    excel_html = ""

    if show_excel:
        excel_columns, excel_rows, excel_message = get_genome_info_from_excel()
        if excel_columns and excel_rows:
            excel_html = generate_html_table_from_excel(excel_columns, excel_rows, current_dir)
        else:
            excel_html = f'<div class="error-tip">⚠ {excel_message}</div>'

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'enter_dir':
            dir_name = request.form.get('dir_name', '')
            current_dir = os.path.join(current_dir, dir_name)
            show_excel = False  # 进入目录后显示文件

        elif action == 'go_up':
            parent_dir = os.path.dirname(current_dir)
            if allowed_path(parent_dir):
                current_dir = parent_dir

        elif action == 'goto_folder':
            # 处理从Accession链接跳转
            folder_path = request.form.get('current_dir', '')
            if allowed_path(folder_path):
                current_dir = folder_path
                # 跳转到文件夹后显示文件列表
                show_excel = False

    # 解析选中的文件内容（只有在不显示Excel数据时才显示文件内容）
    if selected_file and allowed_path(current_dir) and not show_excel:
        file_path = os.path.join(current_dir, selected_file)
        if allowed_file(selected_file) and os.path.exists(file_path):
            file_content = parse_file_content(file_path, current_dir)
        else:
            file_content = '<div class="error-tip">❌ 文件类型不支持或路径错误</div>'

    # 获取当前目录的文件列表（当不显示Excel数据时）
    dirs, files = get_file_list(current_dir) if not show_excel else ([], [])

    return render_template(
        'file_explorer.html',
        current_dir=current_dir,
        dirs=dirs,
        files=files,
        selected_file=selected_file,
        file_content=file_content,
        show_excel=show_excel,
        excel_html=excel_html,
        page_size=PAGE_SIZE
    )


# ========== 文件下载 ==========
@file_view_bp.route('/file-download', methods=['POST'])
def file_download():
    """文件下载功能"""
    current_dir = request.form.get('current_dir', '')
    filename = request.form.get('filename', '')

    if not allowed_path(current_dir) or not allowed_file(filename):
        current_app.logger.warning(f"禁止下载请求: {current_dir}/{filename}")
        return "❌ 禁止下载", 403

    file_path = os.path.join(current_dir, filename)
    if os.path.exists(file_path):
        current_app.logger.info(f"下载文件: {file_path}")
        return send_file(file_path, as_attachment=True)
    else:
        current_app.logger.warning(f"文件不存在: {file_path}")
        return "❌ 文件不存在", 404