# NDS V5 架构设计文档

## 系统概述

NDS V5 是一个基于管道架构的敏感信息识别系统，通过多阶段处理流程实现数据库隐私数据的自动发现、分类和提取。

## 核心架构模式

### 管道-过滤器模式（Pipeline-Filter Pattern）

系统采用经典的管道-过滤器架构，数据从输入到输出经过一系列独立的处理阶段，每个阶段只负责单一职责。

```
数据源 → 扫描 → 路由 → 检测 → 匹配 → 清洗 → 输出
```

## 模块详解

### 1. 配置管理（config.py）

**职责**：加载和管理系统配置

- 从 `config.yaml` 读取数据库连接信息
- 管理运行时参数（超时、批处理大小、工作线程数）
- 定义敏感类型与级别的映射关系

### 2. 数据库扫描模块（scanners/）

**StructureScanner**
- 发现数据库中的所有表、列、数据类型
- 收集样本数据用于后续分析

**FormRouter**
- 智能分析字段特征，将其分类到最佳检测管道
- 分类依据：字段名称语义、数据类型、样本特征
- 输出五种形态：structured, semi_structured, encoded, unstructured, binary_blob

**DbObjectScanner**
- 扫描数据库对象：视图、存储过程、函数
- 识别硬编码的敏感信息

### 3. 检测引擎（detectors/）

每个检测器继承自 `base.py` 的基类，实现统一的 `detect()` 接口。

**StructuredDetector**
- 处理结构化列（VARCHAR, CHAR, TEXT等）
- 使用正则表达式模式匹配敏感数据
- 结合字段名称语义进行引导检测

**SemiStructuredDetector**
- 解析 JSON/JSONB 列中的嵌套数据
- 递归遍历对象结构，逐层检测
- 支持数组和对象混合结构

**EncodedDetector**
- 解码 Base64/Hex/URL 编码内容
- 处理多层嵌套编码
- 解码后送入模式匹配引擎

**UnstructuredDetector**
- 处理自由文本字段
- 集成 OCR 引擎提取图片中的文本
- 结合模式匹配识别敏感信息

**BinaryBlobDetector**
- 分析二进制数据（图片、文件等）
- 图像增强预处理提高 OCR 准确率
- 提取文本后进行模式匹配

**DbObjectDetector**
- 扫描存储过程、视图、函数的 SQL 代码
- 识别硬编码的密码、密钥、连接字符串等

### 4. 模式匹配（matchers/）

**Patterns**
- 20+ 种敏感类型的正则表达式定义
- 噪声过滤模式（排除误报）
- 中文姓名验证（百家姓库）
- 身份证/银行卡/USCC 校验算法

**SensitiveMatcher**
- 核心匹配引擎
- 批量应用正则模式
- 字段关键词匹配引导

**FieldSemantic**
- 分析字段名称判断敏感类型
- 降低漏报率（如 `user_name` 列可能包含姓名）

### 5. 导出管道（exporters/）

**ExportPipeline**
- 协调整个清洗流程：
  1. Normalizer：标准化提取值
  2. Deduplicator：去重（同类型 + 跨类型）
  3. Suppressor：过滤低置信度结果
  4. SemanticCleaner：语义验证

**CsvWriter**
- 输出结构化 CSV 报告
- 包含统计信息

### 6. OCR 引擎（ocr/）

**Engine**
- 封装 RapidOCR 调用
- 置信度阈值过滤

**Preprocessor**
- 图像格式转换和优化
- 适应 OCR 引擎输入要求

**Enhancer**
- 图像增强（对比度、亮度、二值化）
- 提高 OCR 识别准确率

### 7. 解码器（decoders/）

**Base64Decoder**
- Base64 编码解码

**HexDecoder**
- 十六进制编码解码

**URLDecoder**
- URL 编码解码

### 8. 工具模块（utils/）

**DatabaseConnector**
- 统一的数据库连接抽象
- 支持 MySQL 和 PostgreSQL
- 连接池管理

**Logger**
- 集中式日志记录（Loguru）

**MemoryGuard**
- 内存监控和垃圾回收
- 防止大数据量 OOM

**TextUtils**
- 文本处理工具（乱码修复等）

### 9. 数据模型（models/）

**Candidate**
- 检测到的敏感信息数据模型
- 包含：数据库信息、表名、字段名、敏感类型、级别、提取值等

## 数据流

```
1. 加载配置（config.yaml）
2. 连接数据库
3. 扫描表结构 → 获取字段信息
4. FormRouter 分类字段 → 输出5种形态分组
5. 各检测器并行处理对应形态 → 输出原始候选列表
6. 模式匹配验证 → 过滤误报
7. ExportPipeline 清洗：
   - 标准化
   - 去重
   - 抑制过滤
   - 语义验证
8. CSV 输出
```

## 并发模型

- 快速扫描模式使用 ThreadPoolExecutor 并行处理多个表
- 每个线程创建独立的数据库连接
- 线程安全地汇总结果（使用锁）

## 内存管理

- MemoryGuard 监控内存使用
- 每个检测阶段后触发垃圾回收
- 可配置内存上限（默认 14GB）

## 扩展点

1. **新数据库类型**：在 `DatabaseConnector` 中添加支持
2. **新敏感类型**：在 `patterns.py` 中添加正则表达式
3. **新检测器**：继承 `BaseDetector` 实现 `detect()` 方法
4. **新解码器**：在 `decoders/` 中添加解码逻辑
