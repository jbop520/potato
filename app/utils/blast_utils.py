import os
import subprocess
import tempfile
import re
import logging
from pathlib import Path
from flask import current_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BLAST_OUTFMT6_FIELDS = [
    'query_id', 'subject_id', 'identity', 'alignment_length',
    'mismatches', 'gap_openings', 'query_start', 'query_end',
    'subject_start', 'subject_end', 'evalue', 'bit_score'
]


class BlastRunner:
    def __init__(self, app=None):
        self.databases = {}
        self.default_params = {
            'evalue': '1e-5',
            'max_target_seqs': '50',
            'num_threads': '4',
            'outfmt': '6',
            'max_hsps': '1'
        }
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.db_path = Path(app.config.get('BLAST_DB_PATH', Path.cwd() / 'blast_databases'))
        self.upload_folder = Path(app.config.get('UPLOAD_FOLDER', Path.cwd() / 'uploads'))
        self.results_folder = Path(app.config.get('BLAST_RESULTS_FOLDER', Path.cwd() / 'blast_results'))
        self.fasta_files = app.config.get('BLAST_FASTA_FILES', {})
        self.default_params.update(app.config.get('BLAST_DEFAULT_PARAMS', {}))

        self.databases = {}
        for db_name, db_config in self.fasta_files.items():
            self.databases[db_name] = {
                'type': db_config.get('db_type', 'nucl'),
                'description': db_config.get('description', ''),
                'fasta_path': db_config.get('fasta_path', ''),
                'version': db_config.get('version', '1.0'),
                'build_time': None
            }

        for dir_path in [self.db_path, self.upload_folder, self.results_folder]:
            dir_path.mkdir(parents=True, exist_ok=True, mode=0o755)

    def build_database(self, db_name):
        try:
            if db_name not in self.fasta_files:
                return {'success': False, 'error': f'Database {db_name} not configured'}

            config = self.fasta_files[db_name]
            fasta_path = Path(config['fasta_path']).resolve()

            if not fasta_path.exists():
                return {'success': False, 'error': f'FASTA not found: {fasta_path}'}

            db_type = config.get('db_type', 'nucl')
            db_output = self.db_path / db_name

            cmd = [
                'makeblastdb',
                '-in', str(fasta_path),
                '-dbtype', db_type,
                '-out', str(db_output),
                '-parse_seqids',
                '-title', db_name
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                return {'success': False, 'error': result.stderr.strip()}

            return {
                'success': True,
                'message': f'Database {db_name} built successfully',
                'db_path': str(db_output)
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Build timeout (5min)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_database_exists(self, db_name):
        if db_name not in self.databases:
            return False
        db_type = self.databases[db_name]['type']
        db_path = self.db_path / db_name
        suffixes = ['.nhr', '.nin', '.nsq'] if db_type == 'nucl' else ['.phr', '.pin', '.psq']
        return all(db_path.with_suffix(s).exists() for s in suffixes)

    def get_database_status(self):
        status = {}
        for db_name in self.fasta_files:
            built = self.check_database_exists(db_name)
            status[db_name] = {'built': built, 'type': self.databases[db_name]['type']}
        return status

    def validate_fasta_content(self, content, seq_type='nucl'):
        allowed = {
            'nucl': re.compile(r'^[ATCGN]+$', re.I),
            'prot': re.compile(r'^[ACDEFGHIKLMNPQRSTVWY*]+$', re.I)
        }
        lines = content.strip().splitlines()
        if not lines or not lines[0].startswith('>'):
            return False, 'Invalid FASTA'

        seq = ''.join([l.strip() for l in lines if not l.startswith('>')])
        if not seq:
            return False, 'No sequence found'
        if not allowed[seq_type].match(seq):
            return False, 'Invalid characters'
        return True, f'Valid {seq_type} sequence'

    def get_blast_program(self, db_name=None, query_type='nucl', db_type=None, program='auto'):
        """获取BLAST程序名，支持多种调用方式"""
        if program and program != 'auto':
            return program
        if db_type is None:
            if db_name and db_name in self.databases:
                db_type = self.databases[db_name]['type']
            else:
                db_type = 'nucl'
        if db_type == 'nucl' and query_type == 'nucl':
            return 'blastn'
        elif db_type == 'nucl' and query_type == 'prot':
            return 'tblastn'
        elif db_type == 'prot' and query_type == 'nucl':
            return 'blastx'
        elif db_type == 'prot' and query_type == 'prot':
            return 'blastp'
        return 'blastn'

    def run_blast(self, query_file, db_name, params=None, query_type='nucl'):
        try:
            if not self.check_database_exists(db_name):
                return {'success': False, 'error': 'Database not built', 'need_build': True}

            query_path = Path(query_file)
            if not query_path.exists():
                return {'success': False, 'error': 'Query file missing'}

            blast_params = self.default_params.copy()
            if params:
                blast_params.update(params)

            program = self.get_blast_program(db_name, query_type)
            db_path = self.db_path / db_name

            with tempfile.NamedTemporaryFile(dir=self.results_folder, suffix='.out', delete=False) as tmp:
                out_path = Path(tmp.name)

            cmd = [
                program,
                '-query', str(query_path),
                '-db', str(db_path),
                '-out', str(out_path),
                '-evalue', blast_params['evalue'],
                '-max_target_seqs', blast_params['max_target_seqs'],
                '-num_threads', blast_params['num_threads'],
                '-outfmt', '6'
            ]

            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode != 0:
                return {'success': False, 'error': res.stderr.strip()}

            hits = self._parse_blast_output(out_path)
            out_path.unlink(missing_ok=True)

            return {
                'success': True,
                'hits': hits,
                'total': len(hits),
                'program': program
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'BLAST timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_blast_output(self, path):
        hits = []
        if not path.exists():
            return hits
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) != len(BLAST_OUTFMT6_FIELDS):
                    continue
                hit = dict(zip(BLAST_OUTFMT6_FIELDS, parts))
                for k in ['identity', 'evalue', 'bit_score']:
                    try:
                        hit[k] = float(hit[k])
                    except:
                        pass
                hits.append(hit)
        return hits

    def run_pairwise_blast(self, q_seq, s_seq, q_id='query', s_id='subject', seq_type='nucl'):
        try:
            def write_tmp(seq, name):
                tf = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta')
                tf.write(f'>{name}\n{seq}\n')
                tf.close()
                return tf.name

            q_file = write_tmp(q_seq, q_id)
            s_file = write_tmp(s_seq, s_id)
            out_file = tempfile.NamedTemporaryFile(delete=False, suffix='.out').name

            cmd = [
                'blastn' if seq_type == 'nucl' else 'blastp',
                '-query', q_file,
                '-subject', s_file,
                '-out', out_file,
                '-outfmt', '0'
            ]

            subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            with open(out_file, 'r') as f:
                output = f.read()

            for p in [q_file, s_file, out_file]:
                Path(p).unlink(missing_ok=True)
            return {'success': True, 'output': output}
        except Exception as e:
            return {'success': False, 'error': str(e)}


    def guess_seq_type(self, seq_text):
        """猜测序列类型：核酸(nucl)或蛋白质(prot)"""
        seq = seq_text.strip()
        lines = seq.splitlines()
        seq_only = ''.join([l.strip() for l in lines if not l.startswith('>') and l.strip()])
        if not seq_only:
            return 'nucl'
        nucl_chars = sum(1 for c in seq_only.upper() if c in 'ATCGN')
        prot_chars = sum(1 for c in seq_only.upper() if c in 'ACDEFGHIKLMNPQRSTVWY')
        total = len(seq_only)
        if total == 0:
            return 'nucl'
        if nucl_chars / total > 0.8:
            return 'nucl'
        return 'prot'

    def run_blast_flexible(self, query_path, db_path, db_type='nucl', program='blastn', params=None, db_name=None):
        """灵活的BLAST运行方法，支持直接传入数据库路径

        如果提供了 db_name 且数据库已构建，使用构建后的数据库；
        否则直接用 fasta 文件作为 subject 运行 BLAST。
        """
        try:
            query_path_obj = Path(query_path)
            if not query_path_obj.exists():
                return {'success': False, 'error': 'Query file missing'}

            blast_params = self.default_params.copy()
            if params:
                blast_params.update(params)

            db_path_str = str(db_path)
            if db_name and db_name in self.databases:
                built_db_path = self.db_path / db_name
                if self.check_database_exists(db_name):
                    db_path_str = str(built_db_path)
                    use_subject = False
                else:
                    logger.info(f"Database {db_name} not built, building now...")
                    build_result = self.build_database(db_name)
                    if build_result.get('success'):
                        db_path_str = str(built_db_path)
                        use_subject = False
                    else:
                        use_subject = True
            else:
                db_path_obj = Path(str(db_path))
                built_check = db_path_obj.with_suffix('.nsq')
                if built_check.exists() or db_path_obj.with_suffix('.psq').exists():
                    use_subject = False
                else:
                    use_subject = True

            with tempfile.NamedTemporaryFile(dir=self.results_folder, suffix='.out', delete=False) as tmp:
                out_path = Path(tmp.name)

            if use_subject:
                cmd = [
                    program,
                    '-query', str(query_path_obj),
                    '-subject', db_path_str,
                    '-out', str(out_path),
                    '-evalue', blast_params.get('evalue', '1e-5'),
                    '-max_target_seqs', blast_params.get('max_target_seqs', '50'),
                    '-num_threads', blast_params.get('num_threads', '4'),
                    '-outfmt', '6'
                ]
            else:
                cmd = [
                    program,
                    '-query', str(query_path_obj),
                    '-db', db_path_str,
                    '-out', str(out_path),
                    '-evalue', blast_params.get('evalue', '1e-5'),
                    '-max_target_seqs', blast_params.get('max_target_seqs', '50'),
                    '-num_threads', blast_params.get('num_threads', '4'),
                    '-outfmt', '6'
                ]

            logger.info(f"Running BLAST: {' '.join(cmd)}")
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if res.returncode != 0:
                error_msg = res.stderr.strip()
                logger.error(f"BLAST error: {error_msg}")
                return {'success': False, 'error': error_msg}

            hits = self._parse_blast_output(out_path)
            out_path.unlink(missing_ok=True)

            return {
                'success': True,
                'hits': hits,
                'total': len(hits),
                'program': program
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'BLAST timeout (max 10min)'}
        except Exception as e:
            logger.exception("BLAST run error")
            return {'success': False, 'error': str(e)}


    def extract_sequence_by_accession(self, accession_id, fasta_path):
        """从 FASTA 文件中按 accession ID 查找并提取序列"""
        accession_id = accession_id.strip()
        if not accession_id:
            return None
        try:
            fp = Path(fasta_path)
            if not fp.exists():
                logger.warning(f"FASTA file not found: {fasta_path}")
                return None
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            found = False
            header = ''
            seq_parts = []
            for line in lines:
                if line.startswith('>'):
                    if found:
                        break
                    if accession_id in line:
                        found = True
                        header = line.strip()
                    continue
                if found:
                    line = line.strip()
                    if line:
                        seq_parts.append(line)
            if found and seq_parts:
                seq = ''.join(seq_parts)
                logger.info(f"Found sequence for accession '{accession_id}': {len(seq)} bp")
                return f'{header}\n{seq}'
            else:
                logger.warning(f"Accession '{accession_id}' not found in {fasta_path}")
                return None
        except Exception as e:
            logger.error(f"Error extracting accession {accession_id}: {e}")
            return None

    def find_accession_in_all_databases(self, accession_id):
        """在所有预设数据库的 FASTA 文件中搜索 accession ID"""
        for db_name, config in self.fasta_files.items():
            fasta_path = config.get('fasta_path', '')
            if not fasta_path:
                continue
            result = self.extract_sequence_by_accession(accession_id, fasta_path)
            if result:
                return result, db_name
        return None, None


blast_runner = BlastRunner()