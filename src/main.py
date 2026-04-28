import sys
import time
import argparse
import threading
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).parent))

from config import load_config, get_mysql_databases, get_postgresql_databases, get_output_path
from utils.logger import setup_logger
from utils.db_connector import DatabaseConnector
from scanners.structure_scanner import StructureScanner
from scanners.form_router import FormRouter
from detectors.structured import StructuredDetector
from detectors.semi_structured import SemiStructuredDetector
from detectors.encoded import EncodedDetector
from detectors.unstructured import UnstructuredDetector
from detectors.binary_blob import BinaryBlobDetector
from detectors.db_object import DbObjectDetector
from exporters.pipeline import ExportPipeline
from models.candidate import Candidate
from utils.memory_guard import set_memory_limit, check_and_gc, get_status


class NDSV5Pipeline:
    def __init__(self):
        self.logger = setup_logger()
        self.config = load_config()
        self.candidates = []
        self.stats = {
            'mysql': {'databases': 0, 'tables': 0, 'fields': 0, 'candidates': 0},
            'postgresql': {'databases': 0, 'tables': 0, 'fields': 0, 'candidates': 0},
            'forms': {'structured': 0, 'semi_structured': 0, 'encoded': 0, 
                     'unstructured': 0, 'binary_blob': 0, 'db_object': 0},
            'timing': {'start': 0, 'scanning': 0, 'detection': 0, 'export': 0, 'total': 0},
            'errors': {'connection': 0, 'scanning': 0, 'detection': 0, 'export': 0}
        }
        
        self.structured_detector = StructuredDetector()
        self.semi_structured_detector = SemiStructuredDetector()
        self.encoded_detector = EncodedDetector()
        self.unstructured_detector = UnstructuredDetector()
        self.binary_blob_detector = BinaryBlobDetector()
        self.db_object_detector = DbObjectDetector()
        self.export_pipeline = ExportPipeline()

    def run(self):
        self.stats['timing']['start'] = time.time()
        
        self._print_banner()
        
        if not self._validate_environment():
            return False
        
        mysql_dbs = get_mysql_databases()
        pg_dbs = get_postgresql_databases()
        
        self._print_database_summary(mysql_dbs, pg_dbs)
        
        scan_start = time.time()
        
        for db_name in mysql_dbs:
            self._scan_database('mysql', db_name)
        
        for db_name in pg_dbs:
            self._scan_database('postgresql', db_name)
        
        self.stats['timing']['scanning'] = time.time() - scan_start
        
        self._print_scan_summary()
        
        detection_start = time.time()
        self.logger.info("开始导出精修...")
        
        output_path = get_output_path()
        results = self.export_pipeline.export(self.candidates, str(output_path))
        
        self.stats['timing']['export'] = time.time() - detection_start
        self.stats['timing']['total'] = time.time() - self.stats['timing']['start']
        
        self._print_final_report(results, output_path)
        
        return True

    def _print_banner(self):
        self.logger.info("=" * 100)
        self.logger.info("███╗   ██╗██████╗ ███████╗    ██╗   ██╗███████╗")
        self.logger.info("████╗  ██║██╔══██╗██╔════╝    ██║   ██║██╔════╝")
        self.logger.info("██╔██╗ ██║██║  ██║███████╗    ██║   ██║███████╗")
        self.logger.info("██║╚██╗██║██║  ██║╚════██║    ╚██╗ ██╔╝╚════██║")
        self.logger.info("██║ ╚████║██████╔╝███████║     ╚████╔╝ ███████║")
        self.logger.info("╚═╝  ╚═══╝╚═════╝ ╚══════╝      ╚═══╝  ╚══════╝")
        self.logger.info("=" * 100)
        self.logger.info("NDS V5 - 敏感信息识别系统")
        self.logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 100)

    def _validate_environment(self) -> bool:
        try:
            self.logger.info("验证环境配置...")
            
            mysql_config = self.config['databases']['mysql']
            pg_config = self.config['databases']['postgresql']
            
            self.logger.info(f"MySQL 连接: {mysql_config['host']}:{mysql_config['port']}")
            self.logger.info(f"PostgreSQL 连接: {pg_config['host']}:{pg_config['port']}")
            
            output_path = get_output_path()
            output_dir = output_path.parent
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"创建输出目录: {output_dir}")
            
            self.logger.info("环境验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"环境验证失败: {e}")
            return False

    def _print_database_summary(self, mysql_dbs: List[str], pg_dbs: List[str]):
        self.logger.info("-" * 100)
        self.logger.info("数据库摘要:")
        self.logger.info(f"  MySQL ({len(mysql_dbs)}): {', '.join(mysql_dbs)}")
        self.logger.info(f"  PostgreSQL ({len(pg_dbs)}): {', '.join(pg_dbs)}")
        self.logger.info(f"  总计: {len(mysql_dbs) + len(pg_dbs)} 个数据库")
        self.logger.info("-" * 100)

    def _scan_database(self, db_type: str, db_name: str):
        self.logger.info(f"{'='*60}")
        self.logger.info(f"扫描 {db_type.upper()} 数据库: {db_name}")
        self.logger.info(f"{'='*60}")
        
        try:
            with DatabaseConnector(db_type, db_name) as connector:
                scanner = StructureScanner(connector)
                router = FormRouter(scanner)
                
                form_groups = router.route_all()
                
                total_fields = sum(len(fields) for fields in form_groups.values())
                self.logger.info(f"发现 {total_fields} 个字段:")
                self.logger.info(f"  结构化: {len(form_groups['structured'])} 个")
                self.logger.info(f"  半结构化: {len(form_groups['semi_structured'])} 个")
                self.logger.info(f"  编码: {len(form_groups['encoded'])} 个")
                self.logger.info(f"  非结构化: {len(form_groups['unstructured'])} 个")
                self.logger.info(f"  二进制: {len(form_groups['binary_blob'])} 个")
                
                self.stats[db_type]['databases'] += 1
                self.stats[db_type]['fields'] += total_fields
                
                candidates_before = len(self.candidates)
                
                if form_groups['structured']:
                    results = self.structured_detector.detect(connector, db_name, db_type, form_groups['structured'])
                    self.candidates.extend(results)
                    self.stats['forms']['structured'] += len(results)
                    self.logger.info(f"  结构化检测: +{len(results)} 条")
                    check_and_gc()
                
                if form_groups['semi_structured']:
                    results = self.semi_structured_detector.detect(connector, db_name, db_type, form_groups['semi_structured'])
                    self.candidates.extend(results)
                    self.stats['forms']['semi_structured'] += len(results)
                    self.logger.info(f"  半结构化检测: +{len(results)} 条")
                    check_and_gc()
                
                if form_groups['encoded']:
                    results = self.encoded_detector.detect(connector, db_name, db_type, form_groups['encoded'])
                    self.candidates.extend(results)
                    self.stats['forms']['encoded'] += len(results)
                    self.logger.info(f"  编码检测: +{len(results)} 条")
                    check_and_gc()
                
                if form_groups['unstructured']:
                    results = self.unstructured_detector.detect(connector, db_name, db_type, form_groups['unstructured'])
                    self.candidates.extend(results)
                    self.stats['forms']['unstructured'] += len(results)
                    self.logger.info(f"  非结构化检测: +{len(results)} 条")
                    check_and_gc()
                
                if form_groups['binary_blob']:
                    results = self.binary_blob_detector.detect(connector, db_name, db_type, form_groups['binary_blob'])
                    self.candidates.extend(results)
                    self.stats['forms']['binary_blob'] += len(results)
                    self.logger.info(f"  二进制检测: +{len(results)} 条")
                    check_and_gc()
                
                results = self.db_object_detector.detect(connector, db_name, db_type)
                self.candidates.extend(results)
                self.stats['forms']['db_object'] += len(results)
                self.logger.info(f"  数据库对象检测: +{len(results)} 条")
                check_and_gc()
                
                db_candidates = len(self.candidates) - candidates_before
                self.stats[db_type]['candidates'] += db_candidates
                self.logger.info(f"  数据库 {db_name} 总计: {db_candidates} 条")
                
        except Exception as e:
            self.logger.error(f"扫描数据库 {db_name} 失败: {e}")
            self.stats['errors']['scanning'] += 1

    def _print_scan_summary(self):
        self.logger.info("-" * 100)
        self.logger.info("扫描阶段完成:")
        self.logger.info(f"  扫描耗时: {self.stats['timing']['scanning']:.2f} 秒")
        self.logger.info(f"  发现候选: {len(self.candidates)} 条")
        self.logger.info(f"  错误数量: {self.stats['errors']['scanning']}")
        mem = get_status()
        self.logger.info(f"  内存使用: {mem['current_mb']:.1f} MB ({mem['usage_percent']:.1f}% of {mem['limit_gb']:.1f} GB)")
        self.logger.info("-" * 100)

    def _print_final_report(self, results: List[Candidate], output_path: Path):
        self.logger.info("=" * 100)
        self.logger.info("NDS V5 运行报告")
        self.logger.info("=" * 100)
        
        self.logger.info("性能统计:")
        self.logger.info(f"  总耗时: {self.stats['timing']['total']:.2f} 秒")
        self.logger.info(f"    扫描阶段: {self.stats['timing']['scanning']:.2f} 秒")
        self.logger.info(f"    导出阶段: {self.stats['timing']['export']:.2f} 秒")
        mem = get_status()
        self.logger.info(f"  内存峰值: {mem['current_mb']:.1f} MB ({mem['usage_percent']:.1f}% of {mem['limit_gb']:.1f} GB)")
        
        self.logger.info("数据库统计:")
        self.logger.info(f"  MySQL: {self.stats['mysql']['databases']} 个数据库, {self.stats['mysql']['fields']} 个字段, {self.stats['mysql']['candidates']} 条候选")
        self.logger.info(f"  PostgreSQL: {self.stats['postgresql']['databases']} 个数据库, {self.stats['postgresql']['fields']} 个字段, {self.stats['postgresql']['candidates']} 条候选")
        
        self.logger.info("数据形态统计 (原始候选):")
        for form, count in self.stats['forms'].items():
            self.logger.info(f"  {form}: {count} 条")
        
        self.logger.info("最终结果:")
        self.logger.info(f"  原始候选: {len(self.candidates)} 条")
        self.logger.info(f"  导出结果: {len(results)} 条")
        if len(self.candidates) > 0:
            self.logger.info(f"  过滤率: {(1 - len(results)/len(self.candidates))*100:.1f}%")
        
        self.logger.info("按敏感类型分布:")
        type_counts = {}
        for r in results:
            type_counts[r.sensitive_type] = type_counts.get(r.sensitive_type, 0) + 1
        for stype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            self.logger.info(f"  {stype}: {count} 条")
        
        self.logger.info("按敏感级别分布:")
        level_counts = {}
        for r in results:
            level_counts[r.sensitive_level] = level_counts.get(r.sensitive_level, 0) + 1
        for level, count in sorted(level_counts.items()):
            self.logger.info(f"  {level}: {count} 条")
        
        self.logger.info("按数据形态分布 (最终):")
        form_counts = {}
        for r in results:
            form_counts[r.data_form] = form_counts.get(r.data_form, 0) + 1
        for form, count in sorted(form_counts.items()):
            self.logger.info(f"  {form}: {count} 条")
        
        self.logger.info("错误统计:")
        for error_type, count in self.stats['errors'].items():
            if count > 0:
                self.logger.info(f"  {error_type}: {count}")
        
        self.logger.info(f"输出文件: {output_path}")
        self.logger.info("=" * 100)
        self.logger.info("NDS V5 运行结束")
        self.logger.info("=" * 100)


class DebugPipeline:
    def __init__(self, target_dbs=None, target_table=None, fast_mode=False, max_workers=4):
        self.logger = setup_logger()
        self.config = load_config()
        self.target_dbs = target_dbs
        self.target_table = target_table
        self.fast_mode = fast_mode
        self.max_workers = max_workers

        self.structured_detector = StructuredDetector()
        self.semi_structured_detector = SemiStructuredDetector()
        self.encoded_detector = EncodedDetector()
        self.unstructured_detector = UnstructuredDetector()
        self.binary_blob_detector = BinaryBlobDetector()
        self.db_object_detector = DbObjectDetector()
        self.export_pipeline = ExportPipeline()

        self.all_candidates = []
        self.db_reports = {}
        self._thread_local = threading.local()
        self._lock = threading.Lock()

    def run(self):
        self.logger.info("=" * 80)
        self.logger.info("[DEBUG MODE] NDS V5 敏感信息诊断扫描")
        self.logger.info(f"目标数据库: {', '.join(self.target_dbs) if self.target_dbs else '全部'}")
        self.logger.info(f"目标数据表: {self.target_table or '全部'}")
        self.logger.info("=" * 80)

        all_dbs = self._get_target_dbs()

        if not all_dbs:
            self.logger.error(f"未找到目标数据库: {self.target_dbs}")
            return False

        for db_type, db_name in all_dbs:
            self._debug_scan_database(db_type, db_name)

        self._print_global_report()

        if self.all_candidates:
            output_path = get_output_path()
            results = self.export_pipeline.export(self.all_candidates, str(output_path))
            self.logger.info(f"\n[DEBUG] 导出结果: {len(results)} 条 → {output_path}")

        return True

    def _get_thread_connector(self, db_type: str, db_name: str) -> DatabaseConnector:
        """获取线程本地的数据库连接器"""
        if not hasattr(self._thread_local, 'connectors'):
            self._thread_local.connectors = {}

        key = f"{db_type}:{db_name}"
        if key not in self._thread_local.connectors:
            connector = DatabaseConnector(db_type, db_name)
            connector.connect()
            self._thread_local.connectors[key] = connector

        return self._thread_local.connectors[key]

    def _close_thread_connectors(self):
        """关闭当前线程的所有连接器"""
        if hasattr(self._thread_local, 'connectors'):
            for connector in self._thread_local.connectors.values():
                try:
                    connector.disconnect()
                except:
                    pass
            self._thread_local.connectors.clear()

    def _get_target_dbs(self) -> List[tuple]:
        mysql_dbs = get_mysql_databases()
        pg_dbs = get_postgresql_databases()

        all_dbs = [('mysql', db) for db in mysql_dbs] + [('postgresql', db) for db in pg_dbs]

        if self.target_dbs:
            all_dbs = [(t, d) for t, d in all_dbs if d in self.target_dbs]

        return all_dbs

    def _debug_scan_database(self, db_type: str, db_name: str):
        self.logger.info(f"\n{'#'*80}")
        self.logger.info(f"# DATABASE: {db_name} ({db_type})")
        self.logger.info(f"{'#'*80}")

        db_report = {
            'db_type': db_type,
            'db_name': db_name,
            'tables': {},
            'db_objects': {'candidates': [], 'type_dist': {}},
            'total_candidates': 0,
        }

        try:
            with DatabaseConnector(db_type, db_name) as connector:
                scanner = StructureScanner(connector)
                router = FormRouter(scanner)
                form_groups = router.route_all()

                all_fields = []
                for form_type, fields in form_groups.items():
                    for f in fields:
                        f['data_form'] = form_type
                    all_fields.extend(fields)

                tables = {}
                for f in all_fields:
                    tbl = f['table_name']
                    if tbl not in tables:
                        tables[tbl] = []
                    tables[tbl].append(f)

                if self.target_table:
                    tables = {k: v for k, v in tables.items() if k == self.target_table}
                    if not tables:
                        self.logger.warning(f"  未找到目标数据表: {self.target_table}")
                        return

                # 快速扫描模式：多线程并行处理表
                if self.fast_mode and len(tables) > 1:
                    self.logger.info(f"  [FAST MODE] 使用 {self.max_workers} 个线程并行处理 {len(tables)} 个表")
                    self._parallel_scan_tables(db_type, db_name, tables, db_report)
                else:
                    # 常规模式：串行处理
                    for table_name, fields in sorted(tables.items()):
                        self._debug_scan_table(connector, db_type, db_name, table_name, fields, db_report)

                # 数据库对象检测（串行执行，避免连接冲突）
                obj_candidates = self.db_object_detector.detect(connector, db_name, db_type)
                self._analyze_candidates(obj_candidates, db_report['db_objects'], 'db_object')
                db_report['total_candidates'] += len(obj_candidates)

                self._print_db_summary(db_report)
                self.db_reports[f"{db_type}:{db_name}"] = db_report

        except Exception as e:
            import traceback
            self.logger.error(f"  数据库扫描失败 [{db_name}]: {e}")
            self.logger.debug(traceback.format_exc())

    def _parallel_scan_tables(self, db_type: str, db_name: str, tables: Dict[str, list], db_report: dict):
        """并行扫描多个表"""
        table_names = list(tables.keys())

        def scan_single_table(table_name):
            """单个表的扫描任务"""
            try:
                # 为每个线程创建独立的连接器
                connector = self._get_thread_connector(db_type, db_name)
                table_report = {
                    'columns': {},
                    'total_candidates': 0,
                    'type_dist': {},
                    'form_dist': {},
                }

                # 扫描字段（跳过 COUNT 查询以提升性能）
                fields = tables[table_name]
                for field_info in fields:
                    self._debug_scan_field(connector, db_type, db_name, table_name, field_info, table_report)

                # 线程安全地更新报告
                with self._lock:
                    db_report['tables'][table_name] = table_report
                    db_report['total_candidates'] += table_report['total_candidates']

                    # 合并类型分布
                    for stype, count in table_report.get('type_dist', {}).items():
                        db_report['db_objects']['type_dist'][stype] = \
                            db_report['db_objects']['type_dist'].get(stype, 0) + count

                return table_name, table_report, None

            except Exception as e:
                return table_name, None, str(e)

        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(scan_single_table, name): name for name in table_names}

            for future in as_completed(futures):
                table_name, table_report, error = future.result()
                if error:
                    self.logger.warning(f"  表 {table_name} 扫描失败: {error}")
                else:
                    # 打印表摘要
                    self._print_table_summary(table_name, table_report)

        # 关闭线程本地连接器
        self._close_thread_connectors()

    def _debug_scan_table(self, connector, db_type, db_name, table_name, fields, db_report):
        self.logger.info(f"\n  {'─'*70}")
        self.logger.info(f"  TABLE: {table_name}")

        table_report = {
            'columns': {},
            'total_candidates': 0,
            'type_dist': {},
            'form_dist': {},
        }

        row_count = 0
        try:
            q = '"' if db_type == 'postgresql' else '`'
            count_sql = f"SELECT COUNT(*) AS cnt FROM {q}{table_name}{q}"
            row = connector.execute_one(count_sql)
            row_count = row['cnt'] if row else 0
        except Exception:
            pass

        self.logger.info(f"  Rows: {row_count} | Columns: {len(fields)}")

        form_summary = {}
        for f in fields:
            form = f['data_form']
            form_summary[form] = form_summary.get(form, 0) + 1
        form_str = ', '.join(f"{k}:{v}" for k, v in sorted(form_summary.items()))
        self.logger.info(f"  Forms: {form_str}")

        for field_info in fields:
            self._debug_scan_field(connector, db_type, db_name, table_name, field_info, table_report)
            check_and_gc()

        self._print_table_summary(table_name, table_report)
        db_report['tables'][table_name] = table_report
        db_report['total_candidates'] += table_report['total_candidates']

        for stype, count in table_report['type_dist'].items():
            db_report['db_objects']['type_dist'][stype] = db_report['db_objects']['type_dist'].get(stype, 0) + count

    def _debug_scan_field(self, connector, db_type, db_name, table_name, field_info, table_report):
        column_name = field_info['column_name']
        data_form = field_info['data_form']

        samples = self._get_samples(connector, db_type, table_name, column_name, limit=3)
        sample_str = ' | '.join(repr(s)[:40] for s in samples) if samples else '(empty)'

        candidates = []
        try:
            if data_form == 'structured':
                candidates = self.structured_detector.detect(connector, db_name, db_type, [field_info])
            elif data_form == 'semi_structured':
                candidates = self.semi_structured_detector.detect(connector, db_name, db_type, [field_info])
            elif data_form == 'encoded':
                candidates = self.encoded_detector.detect(connector, db_name, db_type, [field_info])
            elif data_form == 'unstructured':
                candidates = self.unstructured_detector.detect(connector, db_name, db_type, [field_info])
            elif data_form == 'binary_blob':
                candidates = self.binary_blob_detector.detect(connector, db_name, db_type, [field_info])
        except Exception as e:
            self.logger.warning(f"    [{column_name}] ({data_form}) 检测异常: {e}")

        if candidates:
            type_dist = {}
            value_samples = {}
            for c in candidates:
                t = c.sensitive_type
                type_dist[t] = type_dist.get(t, 0) + 1
                if t not in value_samples:
                    value_samples[t] = []
                if len(value_samples[t]) < 2:
                    value_samples[t].append(c.extracted_value[:30])

            type_str = ', '.join(f"{k}:{v}" for k, v in sorted(type_dist.items(), key=lambda x: -x[1]))
            # 减少日志输出，只在有匹配时输出
            if len(candidates) > 0:
                self.logger.info(f"    [{column_name}] ({data_form}) → {len(candidates)} matches: {type_str}")

            self._analyze_candidates(candidates, table_report, data_form)

    def _get_samples(self, connector, db_type, table_name, column_name, limit=3):
        try:
            from utils.db_connector import fix_mojibake
            q = '"' if db_type == 'postgresql' else '`'
            sql = f"SELECT {q}{column_name}{q} FROM {q}{table_name}{q} WHERE {q}{column_name}{q} IS NOT NULL LIMIT {limit}"
            rows = connector.execute(sql)
            samples = []
            for row in rows:
                val = row.get(column_name, row.get(column_name.lower(), ''))
                if val is not None:
                    s = str(val)
                    if db_type == 'mysql':
                        s = fix_mojibake(s)
                    samples.append(s[:80])
            return samples
        except Exception:
            return []

    def _analyze_candidates(self, candidates, report, data_form):
        report['candidates'] = report.get('candidates', []) + candidates
        report['total_candidates'] = report.get('total_candidates', 0) + len(candidates)
        self.all_candidates.extend(candidates)

        for c in candidates:
            t = c.sensitive_type
            report['type_dist'] = report.get('type_dist', {})
            report['type_dist'][t] = report['type_dist'].get(t, 0) + 1

        report['form_dist'] = report.get('form_dist', {})
        report['form_dist'][data_form] = report['form_dist'].get(data_form, 0) + len(candidates)

    def _print_table_summary(self, table_name, report):
        if report['total_candidates'] == 0:
            return
        self.logger.info(f"  ── {table_name} 汇总: {report['total_candidates']} 条")
        for stype, count in sorted(report['type_dist'].items(), key=lambda x: -x[1]):
            self.logger.info(f"     {stype}: {count}")

    def _print_db_summary(self, db_report):
        db_name = db_report['db_name']
        db_type = db_report['db_type']
        total = db_report['total_candidates']

        self.logger.info(f"\n  {'='*70}")
        self.logger.info(f"  DATABASE SUMMARY: {db_name} ({db_type}) → {total} candidates")

        if total == 0:
            return

        self.logger.info(f"  Per-table breakdown:")
        for tbl, rpt in sorted(db_report['tables'].items(), key=lambda x: -x[1]['total_candidates']):
            if rpt['total_candidates'] > 0:
                self.logger.info(f"    {tbl}: {rpt['total_candidates']}")

        obj_total = db_report['db_objects'].get('total_candidates', 0)
        if obj_total > 0:
            self.logger.info(f"    [DB Objects]: {obj_total}")

        self.logger.info(f"  Per-type breakdown:")
        all_types = {}
        for tbl, rpt in db_report['tables'].items():
            for stype, count in rpt['type_dist'].items():
                all_types[stype] = all_types.get(stype, 0) + count
        for stype, count in db_report['db_objects'].get('type_dist', {}).items():
            all_types[stype] = all_types.get(stype, 0) + count

        for stype, count in sorted(all_types.items(), key=lambda x: -x[1]):
            self.logger.info(f"    {stype}: {count}")

    def _print_global_report(self):
        self.logger.info(f"\n{'#'*80}")
        self.logger.info(f"# GLOBAL DEBUG REPORT")
        self.logger.info(f"{'#'*80}")

        grand_total = sum(r['total_candidates'] for r in self.db_reports.values())
        self.logger.info(f"Grand total candidates: {grand_total}")

        self.logger.info(f"\nPer-database:")
        for key, rpt in sorted(self.db_reports.items(), key=lambda x: -x[1]['total_candidates']):
            self.logger.info(f"  {key}: {rpt['total_candidates']}")

        all_types = {}
        for rpt in self.db_reports.values():
            for tbl, tbl_rpt in rpt['tables'].items():
                for stype, count in tbl_rpt['type_dist'].items():
                    all_types[stype] = all_types.get(stype, 0) + count
            for stype, count in rpt['db_objects'].get('type_dist', {}).items():
                all_types[stype] = all_types.get(stype, 0) + count

        self.logger.info(f"\nGlobal type distribution:")
        for stype, count in sorted(all_types.items(), key=lambda x: -x[1]):
            self.logger.info(f"  {stype}: {count}")

        self.logger.info(f"\nTop 10 tables by candidate count:")
        all_tables = []
        for key, rpt in self.db_reports.items():
            for tbl, tbl_rpt in rpt['tables'].items():
                all_tables.append((f"{key}.{tbl}", tbl_rpt['total_candidates'], tbl_rpt['type_dist']))
        all_tables.sort(key=lambda x: -x[1])
        for tbl_key, count, types in all_tables[:10]:
            type_str = ', '.join(f"{k}:{v}" for k, v in sorted(types.items(), key=lambda x: -x[1])[:5])
            self.logger.info(f"  {tbl_key}: {count} ({type_str})")

        self.logger.info(f"\n{'#'*80}")
        self.logger.info(f"# DEBUG SCAN COMPLETE")
        self.logger.info(f"{'#'*80}")


def main():
    parser = argparse.ArgumentParser(description='NDS V5 敏感信息识别系统')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--db', type=str, nargs='+', default=None, help='指定目标数据库名称 (可指定多个，空格分隔)')
    parser.add_argument('--table', type=str, default=None, help='指定目标数据表名称 (需要配合 --db)')
    parser.add_argument('--memory-limit', type=float, default=14.0, help='内存上限 GB (默认 14.0)')
    parser.add_argument('--fast', action='store_true', help='启用快速扫描模式 (仅调试模式有效，多线程并行处理表)')
    parser.add_argument('--workers', type=int, default=12, help='快速扫描模式的线程数 (默认 12，建议不超过 CPU 核心数)')
    args = parser.parse_args()

    set_memory_limit(args.memory_limit)

    if args.debug:
        if args.table and not args.db:
            print("错误: 使用 --table 必须同时指定 --db")
            sys.exit(1)

        # 快速扫描模式参数验证
        if args.fast and args.workers < 1:
            print("错误: --workers 必须大于 0")
            sys.exit(1)

        # 限制线程数不超过 CPU 核心数
        import psutil
        max_cores = psutil.cpu_count(logical=True)
        if args.workers > max_cores:
            print(f"警告: --workers ({args.workers}) 超过 CPU 核心数 ({max_cores})，已自动调整为 {max_cores}")
            args.workers = max_cores

        pipeline = DebugPipeline(
            target_dbs=args.db,
            target_table=args.table,
            fast_mode=args.fast,
            max_workers=args.workers
        )
        success = pipeline.run()
    else:
        # 生产模式忽略快速扫描参数
        if args.fast or args.workers != 4:
            print("警告: --fast 和 --workers 参数仅在调试模式下有效，生产模式已忽略")
        pipeline = NDSV5Pipeline()
        success = pipeline.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
