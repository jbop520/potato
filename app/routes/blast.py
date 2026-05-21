from flask import Blueprint, request, jsonify, current_app, render_template
from werkzeug.utils import secure_filename
from pathlib import Path
from ..utils.blast_utils import blast_runner
import time
import uuid

blast_bp = Blueprint('blast', __name__, url_prefix='/blast')

ALLOWED_EXTENSIONS = {'fasta', 'fa', 'fna', 'faa'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@blast_bp.route('/', methods=['GET'])
def index():
    databases = blast_runner.get_database_status() if hasattr(blast_runner, 'get_database_status') else {}
    default_params = blast_runner.default_params if hasattr(blast_runner, 'default_params') else {
        'evalue': '1e-5',
        'max_target_seqs': '50',
        'num_threads': '4'
    }
    return render_template('blast.html', databases=databases, default_params=default_params)

@blast_bp.route('/api/search', methods=['POST'])
def blast_api_search():
    try:
        input_mode = request.form.get('input_mode', 'pasted')
        program = request.form.get('program', 'auto')
        evalue = request.form.get('evalue', '1e-5')
        max_target_seqs = request.form.get('max_target_seqs', '50')
        num_threads = request.form.get('num_threads', '4')
        database_id_orig = request.form.get('database', '').strip()

        seq_text = None
        auto_found_db = None

        if input_mode == "pasted":
            seq_text = request.form.get('sequence_text', '').strip()
        elif input_mode == "file":
            file = request.files.get('file')
            if file: seq_text = file.read().decode('utf-8', errors='ignore').strip()
        elif input_mode == "accession":
            accession_id = request.form.get('accession_id', '').strip()
            if not accession_id:
                return jsonify({'success': False, 'error': '请输入 Accession ID'})
            # 先尝试从所选数据库的 FASTA 文件中提取序列
            if database_id_orig and database_id_orig in blast_runner.fasta_files:
                config = blast_runner.fasta_files[database_id_orig]
                fasta_path = config.get('fasta_path', '')
                if hasattr(blast_runner, 'extract_sequence_by_accession') and fasta_path:
                    seq_text = blast_runner.extract_sequence_by_accession(accession_id, fasta_path)
            # 如果没找到，在所有预设数据库中搜索
            if not seq_text and hasattr(blast_runner, 'find_accession_in_all_databases'):
                seq_text, auto_found_db = blast_runner.find_accession_in_all_databases(accession_id)
            if not seq_text:
                return jsonify({'success': False, 'error': f'未在数据库中查找到序列 "{accession_id}"，请确认 ID 是否正确，或改用粘贴序列方式'})

        if not seq_text:
            return jsonify({'success': False, 'error': '请提供查询序列'})
        if not seq_text.startswith(">"):
            seq_text = '>query\n' + seq_text

        # 确定最终使用的数据库ID
        if input_mode == "accession" and auto_found_db and (not database_id_orig or database_id_orig == "__temp__"):
            database_id = auto_found_db
        else:
            database_id = database_id_orig

        query_id = f"query_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(exist_ok=True)
        query_path = upload_dir / f'{query_id}.fasta'
        query_path.write_text(seq_text, encoding='utf-8')
        if database_id == "__temp__":
            db_file = request.files.get('db_file')
            if not db_file: return jsonify({'success': False, 'error': '请上传数据库文件'})
            db_content = db_file.read().decode('utf-8', errors='ignore').strip()
            db_filename = secure_filename(db_file.filename or 'database.fasta')
            db_temp_path = upload_dir / f'db_{query_id}_{db_filename}'
            db_temp_path.write_text(db_content, encoding='utf-8')
            db_type = blast_runner.guess_seq_type(db_content) if hasattr(blast_runner, 'guess_seq_type') else 'nucl'
            db_path = db_temp_path
        elif database_id and database_id in blast_runner.fasta_files:
            config = blast_runner.fasta_files[database_id]
            db_path = Path(config['fasta_path'])
            db_type = config.get('db_type', 'nucl')
            if not db_path.exists(): return jsonify({'success': False, 'error': '数据库文件不存在'})
        else:
            return jsonify({'success': False, 'error': '请选择或上传数据库'})
        query_type = blast_runner.guess_seq_type(seq_text) if hasattr(blast_runner, 'guess_seq_type') else 'nucl'
        blast_program = blast_runner.get_blast_program(db_type=db_type, query_type=query_type, program=program) if hasattr(blast_runner, 'get_blast_program') else 'blastn'
        if hasattr(blast_runner, "run_blast_flexible"):
            result = blast_runner.run_blast_flexible(
                query_path=str(query_path),
                db_path=str(db_path),
                db_type=db_type,
                program=blast_program,
                params={'evalue': evalue, 'max_target_seqs': max_target_seqs, 'num_threads': num_threads},
                db_name=database_id if database_id not in ("__temp__", "", None) else None
            )
        else:
            result = blast_runner.run_blast(query_file=str(query_path), db_name=database_id, query_type=query_type)
        try: query_path.unlink(missing_ok=True)
        except: pass
        if database_id == "__temp__":
            try: db_temp_path.unlink(missing_ok=True)
            except: pass
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@blast_bp.route('/api/validate', methods=['POST'])
def blast_api_validate():
    try:
        seq_text = None; input_mode = request.form.get('input_mode', 'pasted')
        if input_mode == "pasted":
            seq_text = request.form.get('sequence_text', '').strip()
        elif input_mode == "file":
            file = request.files.get('file')
            if file: seq_text = file.read().decode('utf-8', errors='ignore').strip()
        elif input_mode == "accession":
            accession_id = request.form.get('accession_id', '').strip()
            if accession_id:
                # 从所选数据库中查找序列
                database_id = request.form.get('database', '').strip()
                seq_found = None
                if database_id and database_id in blast_runner.fasta_files:
                    config = blast_runner.fasta_files[database_id]
                    if hasattr(blast_runner, 'extract_sequence_by_accession'):
                        seq_found = blast_runner.extract_sequence_by_accession(accession_id, config.get('fasta_path', ''))
                if not seq_found and hasattr(blast_runner, 'find_accession_in_all_databases'):
                    seq_found, _ = blast_runner.find_accession_in_all_databases(accession_id)
                if seq_found:
                    seq_text = seq_found
                else:
                    seq_text = f'>{accession_id}'
        if not seq_text:
            return jsonify({'success': False, 'error': '请提供序列'})
        seq_type = blast_runner.guess_seq_type(seq_text) if hasattr(blast_runner, 'guess_seq_type') else 'nucl'
        lines = seq_text.strip().split('\n')
        sequences = []; current_id = "query"; current_seq = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith(">"):
                if current_seq: sequences.append({"id": current_id, "sequence": "".join(current_seq), "length": len("".join(current_seq))})
                current_id = line[1:].split()[0] if len(line) > 1 else "query"; current_seq = []
            else: current_seq.append(line.upper())
        if current_seq: sequences.append({"id": current_id, "sequence": "".join(current_seq), "length": len("".join(current_seq))})
        return jsonify({'success': True, 'seq_type': seq_type, 'sequence_count': len(sequences), 'sequence_ids': [s['id'] for s in sequences], 'sequence_preview': [{'id': s['id'], 'length': s['length'], 'sequence': s['sequence'][:100]} for s in sequences]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@blast_bp.route('/status', methods=['GET'])
def blast_status():
    status = blast_runner.get_database_status()
    return jsonify(status)

@blast_bp.route('/build/<db_name>', methods=['POST'])
def build_db(db_name):
    res = blast_runner.build_database(db_name)
    return jsonify(res)

@blast_bp.route('/upload', methods=['POST'])
def upload_fasta():
    if 'file' not in request.files: return jsonify({'success': False, 'error': 'No file'})
    file = request.files['file']
    if file.filename == '': return jsonify({'success': False, 'error': 'Empty filename'})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(exist_ok=True)
        path = upload_dir / filename
        file.save(str(path))
        valid, msg = blast_runner.validate_fasta_content(path.read_text(), seq_type=request.form.get('seq_type', 'nucl'))
        if not valid:
            path.unlink(missing_ok=True)
            return jsonify({'success': False, 'error': msg})
        return jsonify({'success': True, 'filename': filename, 'path': str(path)})
    return jsonify({'success': False, 'error': 'Invalid file type'})

@blast_bp.route('/run', methods=['POST'])
def run_blast():
    data = request.json
    query_path = data.get('query_path')
    db_name = data.get('database')
    seq_type = data.get('seq_type', 'nucl')
    if not query_path or not db_name:
        return jsonify({'success': False, 'error': 'Missing parameters'})
    res = blast_runner.run_blast(query_path, db_name, query_type=seq_type)
    return jsonify(res)

@blast_bp.route('/pairwise', methods=['POST'])
def pairwise():
    data = request.json
    q = data.get('query_seq'); s = data.get('subject_seq'); t = data.get('seq_type', 'nucl')
    if not q or not s:
        return jsonify({'success': False, 'error': 'Empty sequence'})
    res = blast_runner.run_pairwise_blast(q, s, seq_type=t)
    return jsonify(res)
