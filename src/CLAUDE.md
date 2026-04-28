# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

NDS V5（敏感信息识别系统）是一个敏感信息检测系统，用于扫描数据库并识别和分类敏感数据。它支持 MySQL 和 PostgreSQL 数据库，能够检测各种类型的敏感信息，包括个人身份信息（PII）、金融数据、医疗记录等。

## 构建和开发命令

### 运行应用程序
```bash
# 运行主流程（扫描所有配置的数据库）
python src/main.py

# 以调试模式运行（针对特定数据库/表的详细输出）
python src/main.py --debug --db ecommerce_db --table users

# 使用自定义内存限制运行
python src/main.py --memory-limit 8.0

# 快速扫描模式（多线程并行，仅调试模式有效）
python src/main.py --debug --fast --workers 12 --db ecommerce_db
```

**注意**: 所有命令都需要在项目根目录下执行，或者使用完整路径 `src/main.py`。

### 安装依赖
```bash
# 安装依赖包
pip install -r src/requirements.txt
```

## 架构概览

系统采用管道架构，包含以下核心阶段：

### 1. 配置管理 (`src/config.py`)
- 从 `config.yaml` 加载数据库连接和运行时设置
- 管理敏感数据类型分类（L2-L4 级别）
- 处理 MySQL 和 PostgreSQL 配置

### 2. 数据库扫描 (`src/scanners/`)
- **StructureScanner**：发现表、列和数据类型
- **FormRouter**：将字段分类为数据形式（结构化、半结构化、编码、非结构化、二进制）
- **DbObjectScanner**：扫描数据库对象（视图、存储过程、函数）

### 3. 检测引擎 (`src/detectors/`)
- **StructuredDetector**：检测结构化列中的 PII（电话、邮箱、身份证等）
- **SemiStructuredDetector**：解析 JSON/JSONB 列中的敏感数据
- **EncodedDetector**：解码并检测 Base64、Hex、URL 编码内容
- **UnstructuredDetector**：使用 OCR 和模式匹配处理文本字段
- **BinaryBlobDetector**：提取和分析二进制数据（图像、文件）
- **DbObjectDetector**：扫描存储过程、视图、函数

### 4. 模式匹配 (`src/matchers/`)
- **SensitiveMatcher**：核心匹配引擎，包含 20+ 种敏感类型的正则表达式模式
- **Patterns**：中文姓名、电话号码、身份证、地址等预定义模式
- **Field Semantic**：字段名称分析，用于引导检测

### 5. 导出管道 (`src/exporters/`)
- **ExportPipeline**：协调去重、标准化、抑制和语义清理
- **CSVWriter**：输出结果到 CSV 格式
- **Dedup**：移除重复候选项
- **Normalizer**：标准化检测到的值
- **Suppressor**：过滤低置信度结果
- **SemanticCleaner**：验证和清理提取的值

### 6. OCR 引擎 (`src/ocr/`)
- **Engine**：使用 RapidOCR 从图像中提取文本
- **Enhancer**：图像预处理以提高 OCR 准确性
- **Preprocessor**：图像格式转换和优化

## 核心数据流

1. **配置** → 加载数据库连接和设置
2. **扫描** → 发现数据库结构（表、列、类型）
3. **路由** → 将字段分类到适当的检测管道
4. **检测** → 应用特定类型的检测器提取候选项
5. **匹配** → 使用模式匹配和验证规则
6. **导出** → 去重、清理、标准化并输出结果

## 配置文件

- `config.yaml`：数据库连接、运行时参数、OCR 设置、敏感类型映射
- `requirements.txt`：Python 依赖包
- `NDS_V5.spec`：PyInstaller 构建配置

## 常见开发任务

### 添加新的敏感类型
1. 在 `src/matchers/patterns.py` 中添加正则表达式模式
2. 在 `SENSITIVE_KEYWORDS` 映射中添加字段关键词
3. 如需要，更新 `config.yaml` 中的 sensitive_levels
4. 在 `validate_sensitive_value()` 中添加验证逻辑

### 添加新的数据库支持
1. 在 `src/utils/db_connector.py` 中创建连接器
2. 更新 `StructureScanner` 以支持新的数据库类型
3. 在 `FormRouter` 中添加类型映射
4. 在 `config.yaml` 中添加新的数据库配置

### 调试检测问题
1. 使用调试模式：`python src/main.py --debug --db <database_name>`
2. 检查 `output/` 目录中的日志
3. 查看调试输出中的候选项样本
4. 验证 `src/matchers/patterns.py` 中的模式匹配

### 使用快速扫描模式优化调试流程
```bash
# 第一步：快速扫描单个数据库（预期 1-2 分钟）
python src/main.py --debug --fast --workers 6 --db ecommerce_db

# 第二步：分析输出，优化代码

# 第三步：再次扫描验证效果
python src/main.py --debug --fast --workers 6 --db ecommerce_db

# 第四步：扫描下一个数据库
python src/main.py --debug --fast --workers 6 --db fintech_db
```

**快速扫描模式特点**：
- 多线程并行处理数据库表（预期提升 3-5 倍）
- 仅在 `--debug` 模式下有效
- 与内存限制功能完全隔离
- 线程数可配置（建议 4-6，不超过 CPU 核心数）

## 敏感数据分类

- **L2**：低敏感度（GPS 坐标、IP/MAC 地址）
- **L3**：中敏感度（姓名、电话号码、邮箱、地址）
- **L4**：高敏感度（身份证、银行卡、护照、密码）

## 核心组件

- **Candidate**：检测到的敏感信息的数据模型
- **DatabaseConnector**：数据库连接和查询执行
- **MemoryGuard**：内存使用监控和垃圾回收
- **Logger**：使用 Loguru 的集中式日志记录

## 依赖项

- **数据库**：pymysql, psycopg2-binary
- **OCR**：rapidocr-onnxruntime, opencv-python-headless, Pillow
- **数据处理**：pandas, numpy
- **配置**：PyYAML
- **日志**：loguru
- **系统**：psutil

## 输出

结果导出到 `src/output/upload.csv`，包含以下列：
- db_type, db_name, table_name, field_name, record_id
- data_form, sensitive_type, sensitive_level, extracted_value

**注意**: 所有输出文件都保存在 `src/output/` 目录下，包括：
- `upload.csv`：扫描结果
- `nds_v5.log`：日志文件

## 备份策略

- **不需要自动备份**：项目不自动创建备份文件
- **手动备份**：如需备份，请在 `src/` 目录下创建子目录（如 `src/backups/`）
- **版本控制**：建议使用 Git 进行版本控制，而不是手动备份
