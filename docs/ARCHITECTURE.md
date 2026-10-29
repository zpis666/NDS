# NDS V6 架构设计文档

## 1. 系统概述

NDS V6（Network Data Scanner V6）是一套面向数据库敏感信息发现任务的本地化识别系统。系统连接 MySQL 与 PostgreSQL，按数据形态将字段分流到六类检测器，经过规则匹配、格式校验、OCR 识别与导出治理，最终生成赛事要求的九列 `upload.csv`。

设计目标：

- **可解释**：每条结果保留数据库、表、字段、记录主键、数据形态、敏感类型与敏感级别。
- **可复现**：数据库连接由外置 `config.yaml` 管理，源码与 Windows 可执行程序均可直接运行。
- **可交付**：PyInstaller 单文件打包，现场无需 Python 环境。

## 2. 总体架构

系统采用“管道—过滤器 + 策略路由”架构：

```text
config.yaml
    │
    ▼
Config Loader ──► DatabaseConnector（MySQL / PostgreSQL）
    │
    ▼
StructureScanner ──► 表、字段、类型、主键
    │
    ▼
FormRouter ──► structured / semi_structured / encoded /
               unstructured_text / binary_blob / db_object
    │
    ├──► StructuredDetector
    ├──► SemiStructuredDetector
    ├──► EncodedDetector
    ├──► UnstructuredDetector
    ├──► BinaryBlobDetector
    └──► DbObjectDetector
    │
    ▼
Candidate（统一候选项模型）
    │
    ▼
ExportPipeline
    ├── Normalizer
    ├── Deduplicator
    ├── Suppressor
    ├── SemanticCleaner
    ├── CrossTypeDedup
    ├── FinalBoost
    ├── CrossTypeDedup
    └── CsvWriter
    │
    ▼
output/upload.csv
```

## 3. 模块详解

### 3.1 入口与配置（`main.py` / `config.py` / `config.yaml`）

- `main.py` 负责解析命令行参数、初始化管道、调度扫描与检测、输出运行报告。
- `config.py` 在源码模式从 `config.py` 所在目录加载 `config.yaml`；在 PyInstaller 冻结模式下从 `sys.executable` 所在目录加载，保证 exe 可外置配置。
- 支持 `--debug`、`--db`、`--table`、`--fast`、`--workers`、`--memory-limit` 等参数。

### 3.2 数据库访问（`utils/db_connector.py`）

- 统一封装 MySQL（PyMySQL）与 PostgreSQL（psycopg2）连接。
- 提供游标上下文、批量查询、主键获取与数据库列表读取。
- `fix_mojibake()` 对 MySQL 中文乱码进行多编码组合修复（latin1/cp1252/iso-8859-1 × utf-8/gbk/gb2312/gb18030）。

### 3.3 结构扫描（`scanners/structure_scanner.py`）

- MySQL 通过 `information_schema` 读取库、表、列、类型与主键。
- PostgreSQL 通过 `pg_tables`、`information_schema.columns` 读取对应元数据。
- 产出字段清单供 `FormRouter` 路由。

### 3.4 数据形态路由（`scanners/form_router.py`）

按优先级链式判断每个字段属于哪类数据形态：

1. `binary_blob`：MySQL 的 `blob/mediumblob/longblob/binary/varbinary/tinyblob`，PostgreSQL 的 `bytea`。
2. `semi_structured`：`json` / `jsonb`。
3. `encoded`：字段名包含 `encoded/encrypt/cipher/base64/hex/hash/token/secret/credential` 等关键词。
4. `unstructured_text`：字段名包含文本关键词且不以结构化后缀结尾，或特定 `varchar/char` 描述性字段。
5. `structured`：默认兜底。

`db_object` 由 `DbObjectScanner` 单独扫描视图与存储过程定义，不经过字段路由。

### 3.5 六类检测器（`detectors/`）

| 检测器 | 职责 |
| --- | --- |
| `StructuredDetector` | 结构化字段的正则、字段语义与格式校验 |
| `SemiStructuredDetector` | 递归解析 JSON/JSONB，按键名与值联合判断 |
| `EncodedDetector` | 最多 4 层 Base64/Hex/URL 递归解码，解码后做 JSON/KV 解析与规则匹配 |
| `UnstructuredDetector` | 上下文关键词、全文正则、中文姓名专项三策略并行 |
| `BinaryBlobDetector` | 图片签名判断、本地 OCR、OCR 容错匹配、文本回退 |
| `DbObjectDetector` | 扫描视图与存储过程定义中的硬编码敏感值 |

### 3.6 匹配与校验（`matchers/`）

- `patterns.py`：20 类敏感信息的正则模式、字段关键词表、噪声词表与格式校验函数。
- `core.py`：`match_field_value()`（字段语义引导）、`match_with_hints()`（正则 + 类型提示）。
- `field_semantic.py`：字段名语义映射与置信度增益/惩罚。
- 格式校验：身份证区域码与校验位、银行卡 Luhn、USCC 加权校验、VIN 字符规则、中文姓名姓氏表与排除词表。

### 3.7 导出治理（`exporters/`）

`ExportPipeline.run()` 串行执行：

1. `normalizer.py`：全角转半角、手机号去 `+86`/空格/横线、地址标准化。
2. `dedup.py`：同类型去重，按置信度保留最高；跨类型去重保留最高置信度标签。
3. `suppressor.py`：停用词、正则噪声模式、格式校验与上下文抑制。
4. `semantic_cleaner.py`：字段名语义冲突过滤与低置信度丢弃。
5. `final_boost.py`：竞赛场景定向补强与误报簇抑制。
6. `csv_writer.py`：按九列格式写出 UTF-8 CSV，并输出统计信息。

### 3.8 OCR（`ocr/`）

- `engine.py`：RapidOCR（ONNX Runtime）封装，懒加载，失败时退化为文本回退。
- `preprocessor.py`：CLAHE 对比度增强、自适应二值化、尺寸调整。
- `enhancer.py`：OCR 后处理与常见误读修复。

### 3.9 数据模型（`models/candidate.py`）

`Candidate` 为 dataclass，核心字段包括：

- `db_type`、`db_name`、`table_name`、`field_name`、`record_id`
- `data_form`、`sensitive_type`、`sensitive_level`、`extracted_value`、`confidence`

其 `key` 属性为七元组，与赛事评分的核心匹配维度对齐；`to_csv_row()` 输出九列结果。

### 3.10 工具模块（`utils/`）

- `logger.py`：Loguru 日志初始化与文件输出。
- `memory_guard.py`：psutil 监控 RSS，超阈值触发 `gc.collect()`。
- `text_utils.py`：文本清洗、噪声判断与通用处理。

## 4. 数据流

```text
1. 读取 config.yaml，建立 MySQL / PostgreSQL 连接
2. StructureScanner 读取库表结构与主键
3. FormRouter 将字段分流到六类形态
4. 各 Detector 产出 Candidate 列表
5. Matchers 执行正则、字段语义与格式校验
6. ExportPipeline 七步治理
7. CsvWriter 输出 output/upload.csv
```

## 5. 并发与内存

- 生产模式为串行扫描，保证数据库连接稳定与结果顺序可控。
- 调试模式 `--fast` 使用 `ThreadPoolExecutor` 并行处理多表，线程内使用 `threading.local()` 隔离数据库连接。
- BLOB 批大小 500，文本批大小 10,000；每批处理后检查内存并按需 GC。
- 默认内存上限 14GB，可通过 `--memory-limit` 调整。

## 6. 扩展点

1. **新增数据库类型**：扩展 `DatabaseConnector` 与 `StructureScanner`。
2. **新增敏感类型**：在 `matchers/patterns.py` 增加正则、关键词与校验函数。
3. **新增检测器**：继承 `detectors/base.py` 的基类并实现 `detect()`。
4. **新增解码器**：在 `decoders/` 添加解码实现并在 `EncodedDetector` 注册。
5. **调整导出策略**：在 `exporters/pipeline.py` 中编排新的处理阶段。

## 7. 交付与运行

- Windows 可执行程序：`release/NDS_V6.exe` + `release/config.yaml`
- 源码运行：`pip install -r src/requirements.txt && python src/main.py`
- 输出：`output/upload.csv`（九列，UTF-8）
