from flask import Blueprint, render_template, abort, send_from_directory, redirect, url_for, current_app
from pathlib import Path

files_bp = Blueprint("files_bp", __name__)

def _safe_resolve(subpath: str) -> Path:
    base: Path = current_app.config["BASE_FILES_DIR"]
    p = (base / (subpath or "")).resolve()
    if not str(p).startswith(str(base)):
        abort(403)
    return p

def _fmt_size(n: int) -> str:
    size, unit = float(n), "B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024 or unit == "PB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024

@files_bp.route("/", defaults={"subpath": ""})
@files_bp.route("/<path:subpath>")
def list_files(subpath: str):
    full = _safe_resolve(subpath)
    if not full.exists():
        abort(404)

    # 如果直接访问到具体文件，则跳转到下载
    if full.is_file():
        rel = str(full.relative_to(current_app.config["BASE_FILES_DIR"])).replace("\\", "/")
        return redirect(url_for("files_bp.download_file", subpath=rel))

    # 目录列表：先文件夹后文件
    entries = []
    for p in sorted(full.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        entries.append({
            "name": p.name,
            "is_dir": p.is_dir(),
            "size": _fmt_size(p.stat().st_size) if p.is_file() else "",
            "rel": str(p.relative_to(current_app.config["BASE_FILES_DIR"])).replace("\\", "/")
        })

    # 返回上级
    parts, acc = [], ""
    for part in Path(subpath).parts:
        acc = f"{acc}/{part}" if acc else part
        parts.append({"name": part, "rel": acc})
    parent_rel = "/".join(Path(subpath).parts[:-1]) if subpath else None

    return render_template(
        "files.html",
        base=str(current_app.config["BASE_FILES_DIR"]),
        entries=entries,
        breadcrumbs=parts,
        parent_rel=parent_rel
    )

@files_bp.route("/download/<path:subpath>")
def download_file(subpath: str):
    full = _safe_resolve(subpath)
    if not full.exists() or not full.is_file():
        abort(404)
    return send_from_directory(directory=str(full.parent), path=full.name, as_attachment=True)
