# NDS V5 - 敏感信息识别系统

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Database](https://img.shields.io/badge/database-MySQL%20%7C%20PostgreSQL-orange)

> 多模态数据库敏感信息检测系统，实现从数据结构扫描、形态路由、多引擎协同检测到语义清洗的全自动化隐私数据识别管道。

---

## 项目简介

NDS V5（Network Data Scanner V5）是一个企业级敏感信息识别系统，用于扫描数据库并自动发现、分类、提取敏感数据。系统支持 MySQL 和 PostgreSQL 数据库，能够检测 20+ 种敏感类型，覆盖结构化、半结构化、编码、非结构化、二进制等多种数据形态。

## 核心特性

- **六步自动化管道**：结构扫描 → 形态路由 → 并行检测 → 模式匹配 → 语义清洗 → 结果输出
- **六大检测引擎**：每个引擎专注于一种数据形态的敏感信息识别
  - StructuredDetector：结构化列（姓名、电话、身份证等）
  - SemiStructuredDetector：JSON/JSONB 字段
  - EncodedDetector：Base64/Hex/URL 编码内容
  - UnstructuredDetector：自由文本字段（OCR + 模式匹配）
  - BinaryBlobDetector：图片、文件等二进制数据
  - DbObjectDetector：存储过程、视图、函数
- **三级敏感度分类**：L2（低）/ L3（中）/ L4（高）自动分级
- **多数据库支持**：MySQL + PostgreSQL 统一抽象接口
- **高性能**：多线程并行扫描，内存监控与垃圾回收

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        NDS V5 管道架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────────────┐ │
│  │ 结构扫描  │──>│ 形态路由  │──>│     并行检测引擎          │ │
│  │Structure │   │ FormRouter│   │ ┌────────────────────┐  │ │
│  │ Scanner  │   │          │   │ │ StructuredDetector  │  │ │
│  └──────────┘   └──────────┘   │ │ SemiStructuredDet.  │  │ │
│                                 │ │ EncodedDetector     │  │ │
│                                 │ │ UnstructuredDetector│  │ │
│                                 │ │ BinaryBlobDetector  │  │ │
│                                 │ │ DbObjectDetector    │  │ │
│                                 │ └────────────────────┘  │ │
│                                 └───────────┬─────────────┘ │
│                                             │               │
│                                 ┌───────────▼─────────────┐ │
│                                 │    模式匹配引擎           │ │
│                                 │  20+ 正则 + 字段语义分析  │ │
│                                 └───────────┬─────────────┘ │
│                                             │               │
│                                 ┌───────────▼─────────────┐ │
│                                 │     语义清洗管道          │ │
│                                 │ 去重 → 标准化 → 过滤     │ │
│                                 └───────────┬─────────────┘ │
│                                             │               │
│                                 ┌───────────▼─────────────┐ │
│                                 │     CSV 报告输出          │ │
│                                 └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 支持的敏感类型

| 级别 | 敏感类型 |
|------|---------|
| L2（低） | GPS坐标、IP地址、MAC地址 |
| L3（中） | 中文姓名、电话号码、邮箱、地址、车牌号、社保号、公积金号、医保号、车架号、病历号、统一社会信用代码、营业执照号 |
| L4（高） | 身份证号、银行卡号、护照号、军人证件号、密码/密钥 |

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+ / PostgreSQL 12+

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd Zerone01

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r src/requirements.txt
```

### 配置

编辑 `src/config.yaml` 文件，配置数据库连接：

```yaml
databases:
  mysql:
    host: "your_host"
    port: 3306
    user: "your_user"
    password: "your_password"
    databases:
      - "your_database_1"
      - "your_database_2"

  postgresql:
    host: "your_host"
    port: 5432
    user: "your_user"
    password: "your_password"
    databases:
      - "your_database_1"
```

### 运行

```bash
# 生产模式（扫描所有配置的数据库）
python src/main.py

# 调试模式（针对特定数据库/表）
python src/main.py --debug --db your_database --table your_table

# 快速扫描模式（多线程并行）
python src/main.py --debug --fast --workers 12 --db your_database

# 自定义内存限制
python src/main.py --memory-limit 8.0
```

### 输出

扫描结果导出至 `src/output/upload.csv`，包含以下字段：
- db_type, db_name, table_name, field_name
- data_form, sensitive_type, sensitive_level, extracted_value

## 项目结构

```
Zerone01/
├── src/
│   ├── main.py                 # 程序入口
│   ├── config.py               # 配置管理
│   ├── config.yaml             # 配置文件
│   ├── requirements.txt        # 依赖列表
│   ├── CLAUDE.md               # 开发指南
│   │
│   ├── scanners/               # 数据库扫描模块
│   │   ├── structure_scanner.py  # 表结构发现
│   │   ├── form_router.py       # 数据形态路由
│   │   └── db_object_scanner.py # 数据库对象扫描
│   │
│   ├── detectors/              # 检测引擎
│   │   ├── base.py              # 检测器基类
│   │   ├── structured.py        # 结构化检测
│   │   ├── semi_structured.py   # 半结构化检测
│   │   ├── encoded.py           # 编码内容检测
│   │   ├── unstructured.py      # 非结构化检测
│   │   ├── binary_blob.py       # 二进制检测
│   │   └── db_object.py         # 数据库对象检测
│   │
│   ├── matchers/               # 模式匹配
│   │   ├── patterns.py          # 正则表达式模式
│   │   ├── core.py              # 核心匹配引擎
│   │   └── field_semantic.py    # 字段语义分析
│   │
│   ├── exporters/              # 导出管道
│   │   ├── pipeline.py          # 主管道
│   │   ├── normalizer.py        # 标准化
│   │   ├── dedup.py             # 去重
│   │   ├── suppressor.py        # 抑制过滤
│   │   ├── semantic_cleaner.py  # 语义清洗
│   │   └── csv_writer.py        # CSV输出
│   │
│   ├── ocr/                    # OCR引擎
│   │   ├── engine.py            # RapidOCR封装
│   │   ├── preprocessor.py      # 图像预处理
│   │   └── enhancer.py          # 图像增强
│   │
│   ├── decoders/               # 解码器
│   │   ├── base64_decoder.py
│   │   ├── hex_decoder.py
│   │   └── url_decoder.py
│   │
│   ├── utils/                  # 工具模块
│   │   ├── db_connector.py      # 数据库连接
│   │   ├── logger.py            # 日志
│   │   ├── text_utils.py        # 文本处理
│   │   └── memory_guard.py      # 内存管理
│   │
│   ├── models/                 # 数据模型
│   │   └── candidate.py         # 候选项模型
│   │
│   └── output/                 # 输出目录
│       ├── upload.csv           # 扫描结果
│       └── nds_v5.log           # 日志文件
│
├── docs/                       # 文档
│   └── ARCHITECTURE.md          # 架构设计文档
│
├── LICENSE                     # MIT许可证
└── README.md                   # 本文件
```

## 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--debug` | 启用调试模式 | `--debug` |
| `--db` | 指定目标数据库 | `--db ecommerce_db` |
| `--table` | 指定目标数据表 | `--table users` |
| `--fast` | 启用快速扫描（多线程） | `--fast` |
| `--workers` | 线程数（默认12） | `--workers 8` |
| `--memory-limit` | 内存上限GB（默认14） | `--memory-limit 8.0` |

## 扩展开发

### 添加新的敏感类型

1. 在 `src/matchers/patterns.py` 中添加正则表达式
2. 在 `SENSITIVE_KEYWORDS` 中添加字段关键词
3. 更新 `config.yaml` 中的 sensitive_levels 映射
4. 在 `validate_sensitive_value()` 中添加验证逻辑

### 添加新的数据库支持

1. 在 `src/utils/db_connector.py` 中创建连接器
2. 更新 `StructureScanner` 支持新数据库类型
3. 在 `FormRouter` 中添加类型映射

## 技术栈

- **数据库**：pymysql, psycopg2-binary
- **OCR**：rapidocr-onnxruntime, opencv-python-headless, Pillow
- **数据处理**：pandas, numpy
- **配置**：PyYAML
- **日志**：loguru
- **系统**：psutil

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
