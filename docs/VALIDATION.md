# 移植验证记录

2026-09-09，本机 Windows / Python 3.12.14 的全新虚拟环境安装 requirements.txt 成功。
CPU 虚拟环境未安装 CuPy，纯 CPU 路径正常运行。

| 检查 | 实际结果 |
|---|---|
| CPU doctor、Arb ζ(2) | 通过 |
| 数值与存储单元检查 | 6 项通过；1 项 Linux 进程组检查在 Windows 跳过 |
| CPU 完整校准批次 | 8/8 窗口完成，256 次 DE 目标求值 |
| 低高度独立库复核 | 中心与最佳点均通过 Arb / mpmath 对照 |
| 完成后续跑 | 原 RESULTS.json 和全部窗口 SHA-256 不变 |
| RTX 4090 doctor 和 CuPy 内核 | 通过，CuPy 14.2.0 / CUDA 12.1 |
| GPU 筛选后完整校准批次 | 8/8 窗口完成，256 次 DE 目标求值 |
| 最高高度相位抽样 | CPU 对 100 位直接三角计算通过，阈值 1e-11 |

GPU 测试复用了本机已有的独立 CuPy 运行环境；CPU 测试使用仓库中新建的纯 CPU 虚拟环境。
低高度校准只验证计算链路，不是 RH 反例实验结果。

Ubuntu 自动测试已经配置，但首次 [Actions 运行](https://github.com/maris205/rh_counterexample/actions/runs/34315041394)
未启动任何步骤：GitHub 返回账户因账单问题被锁定。
本机 WSL 启动也超时，因此本次没有获得完整的 Linux 实机通过记录。
这不影响拉取已推送代码；在服务器上应先执行 README 的 smoke 批次，再启动正式计算。

GPU/CUDA 的服务器环境需由 `doctor --backend gpu` 在目标机器检查。
未对用户的 EPYC 32 核服务器做实际耗时或内存峰值测量。
