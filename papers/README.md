# 原始论文与 Markdown 阅读版

这里收录本项目起步时使用的五份原稿，共 **109 个 PDF 物理页**。
PDF 保持原文件内容；Markdown 为按页提取的全文检索版，每页都有对应的 PDF 链接。

| 编号 | 论文 | 页数 | Markdown | 原始 PDF | 既有审读笔记 |
|---|---|---:|---|---|---|
| 1 | The emergence of prime distribution from low-dimensional deterministic chaos | 24 | [正文](markdown/paper-01.md) | [PDF](pdf/paper-01.pdf) | [第 1、2 篇](notes/audit-papers-1-2.md) |
| 2 | Transient Chaos and Topological Bounds in Prime Dynamics: Revisiting the One-Dimensional Sieve Mapping | 25 | [正文](markdown/paper-02.md) | [PDF](pdf/paper-02.pdf) | [第 1、2 篇](notes/audit-papers-1-2.md) |
| 3 | A Sequential Birkhoff Theorem for Slow Logarithmic Drift in Non-Uniformly Expanding Unimodal Maps | 8 | [正文](markdown/paper-03.md) | [PDF](pdf/paper-03.pdf) | [第 3 篇](notes/audit-paper-3.md) |
| 4 | Spectral Isomorphism between Renormalization Flow in Non-Autonomous Quadratic Maps and Riemann Zeros | 35 | [正文](markdown/paper-04.md) | [PDF](pdf/paper-04.pdf) | [第 4 篇](notes/audit-paper-4.md) |
| 5 | An Area-Preserving Hénon-Map Model for the Riemann Zeros: A Deterministic-Dynamics Approach with Quantum and Dissipative Solvers | 17 | [正文](markdown/paper-05.md) | [PDF](pdf/paper-05.pdf) | [第 5 篇](notes/audit-paper-5.md) |

与当前符号异常选窗最直接相关的是第 2 篇；第 1 篇给出早期模型，第 3 篇讨论慢漂移，第 4、5 篇提供此前的零点拟合思路。
原稿中的命题、猜想和数值结论均按原文归档，未在本次上传中修订。审读笔记是 2026-09-08 的历史分析，单独保存在 notes 中。

## 文本提取的范围

此前保存的是全文 TXT 和四份 Markdown 审读笔记。本次补齐了五篇正文的 Markdown 容器。
为避免错误改写公式，正文保留 Poppler 版式提取的行序和空格，使用等宽文本块展示。
这不是人工校订的 LaTeX/Markdown 排版稿：上下标、特殊符号、双栏阅读顺序和图像内容需查看原 PDF。
正文中的图题会出现在提取文本中，原图保留在 PDF 中。
第 4 篇 PDF 第 21 页的小节标题在提取时出现 1 个替换字符 `�`，对应位置须核对原 PDF；数量已写入提取清单，未猜测填补。

文件名、页数及原 PDF 哈希见 [目录数据](catalog.json)，各页文本与输出文件哈希见 [提取清单](EXTRACTION_MANIFEST.json)。
原论文中的署名、参考文献及版权文字均保留。

## 重新导出与核对

需要 Python 3 和 Poppler 的 `pdftotext`、`pdfinfo`，不需要增加数值实验的 Python 依赖。
在仓库根目录运行：

```bash
python tools/export_papers.py
python tools/export_papers.py --check
```

`--check` 重新提取后逐字节核对已发布 Markdown、PDF 哈希和清单，不改写文件。
要复现相同字节，应使用提取清单记录的 Poppler 版本。
审读笔记中提到的旧 PC 渲染图片和完整研究工作目录没有全部归档；已有的小型检查证据位于 [notes](notes/README.md)。
