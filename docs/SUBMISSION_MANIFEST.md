# 最终提交包对照说明

本仓库按交付类型整理了「广州软件学院-Zerone01-20265412010-NDS_V6-最终提交包」的全部核心内容，原包与仓库路径对照如下。

> 公开仓库中的作品文档、答辩材料及仓库文本已对团队成员姓名进行脱敏处理；原始提交包保留在本地。

## 文件对照

| 原提交包路径 | 仓库路径 | 说明 |
| --- | --- | --- |
| `源码/nds v6/` | `src/` | NDS V6 完整 Python 源码 |
| `可执行文件/NDS_V6.exe` | `release/NDS_V6.exe` | Windows 单文件可执行程序 |
| `可执行文件/config.yaml` | `release/config.yaml` | 外置数据库配置 |
| `可执行文件/output/upload.csv` | `results/upload.csv` | 与根目录 `upload.csv` 内容一致 |
| `upload.csv` | `results/upload.csv` | 正式提交结果 |
| `文档/作品简介.pdf` | `docs/NDS_V6_作品简介.pdf` | 作品简介 |
| `文档/研究报告.pdf` | `docs/NDS_V6_研究报告.pdf` | 研究报告 |
| `文档/操作手册.pdf` | `docs/NDS_V6_操作手册.pdf` | 操作手册 |
| `文档/作品原创性说明.pdf` | `docs/NDS_V6_作品原创性说明.pdf` | 原创性说明 |
| `PPT/NDS_V6答辩PPT.pptx` | `ppt/NDS_V6答辩PPT.pptx` | 答辩 PPT |
| `PPT/NDS_V6_6分钟答辩讲稿.pdf` | `ppt/NDS_V6_6分钟答辩讲稿.pdf` | 答辩讲稿 |
| `演示视频/Desktop 2026.06.23 - 05.48.37.02.mp4` | `video/NDS_V6_演示视频.mp4` | 演示视频 |

> 原包中的 `PPT/NDS_V6答辩PPT.backup-20260626.pptx` 为编辑备份文件，未纳入仓库；`可执行文件/output/upload.csv` 与根目录 `upload.csv` 为同一文件，仓库中仅保留一份 `results/upload.csv`。

## 完整性校验

| 文件 | 校验值 |
| --- | --- |
| `results/upload.csv` | MD5 `030BA3A2F1BEDFCC512EF32A0EF3FE42`，55,352 行（含表头） |
| `release/NDS_V6.exe` | SHA256 `F2EF7471E74C7C9FCFB4BD86BFA1CC0A1CB070537D477526C448D9D2079081DA`，100,503,899 bytes |
| `video/NDS_V6_演示视频.mp4` | SHA256 `87306B3EDA5A241CA458400AD9F81FCC33CA0BC363100F02842B2794A15ED85F`，22,179,793 bytes |
| `ppt/NDS_V6答辩PPT.pptx` | SHA256 `C50580CFDE8A1FCEFE09C538CDE8FE923D8470015C8C7F26545C83607AAC1D6C`，313,165 bytes |

校验命令示例：

```bash
# Windows PowerShell
Get-FileHash .\results\upload.csv -Algorithm MD5
Get-FileHash .\release\NDS_V6.exe -Algorithm SHA256
```

## 获奖信息

- 赛事：2026 年广东省大学生计算机设计大赛（网络与数据安全挑战赛）
- 奖项：省级三等奖（省三）
- 队伍：广州软件学院 · Zerone01
- 作品编号：20265412010
- 参赛成员：Zerone01 团队（姓名已脱敏）
- 指导教师：已脱敏
