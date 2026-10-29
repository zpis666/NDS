# NDS V6 Windows 可执行交付

> 2026 年广东省大学生计算机设计大赛（网络与数据安全挑战赛）**省级三等奖**

本目录包含 NDS V6 的 Windows 单文件可执行程序与外置配置文件。

## 文件

| 文件 | 说明 |
| --- | --- |
| `NDS_V6.exe` | Windows 10/11 64 位单文件可执行程序（PyInstaller 打包） |
| `config.yaml` | 数据库连接与运行参数配置 |

`NDS_V6.exe` 与 `config.yaml` **必须放在同一目录**。程序在 exe 所在目录读取配置，并在 `output/upload.csv` 写出结果。

## 运行

```bat
REM 1. 编辑 config.yaml，填写 MySQL / PostgreSQL 连接信息
REM 2. 查看帮助
NDS_V6.exe --help

REM 3. 完整扫描
NDS_V6.exe

REM 4. 常用调试参数
NDS_V6.exe --debug --db ecommerce_db
NDS_V6.exe --debug --fast --workers 12 --db ecommerce_db
NDS_V6.exe --memory-limit 14
```

## 环境要求

- Windows 10/11 64 位
- 无需安装 Python
- 建议内存 8GB 以上
- 可访问 MySQL 8.0 与 PostgreSQL 15 数据库

## 校验值

```text
NDS_V6.exe
SHA256: F2EF7471E74C7C9FCFB4BD86BFA1CC0A1CB070537D477526C448D9D2079081DA
Size:   100,503,899 bytes
```
