# RH counterexample numerical lab

从第 3、第 5 阶段的有限素数筛符号异常出发，启发式选窗，再搜索**实际黎曼 ζ 函数**。
这是可重复的数值探索工具，目前没有找到或认证 RH 反例。

流程：整数重建符号 → 原序列与固定置乱对照 → 模型网格筛选 → 高精度细化并冻结窗口 → CPU 并行计算实际 ζ → 保存需复查的候选。
GPU 只加速符号模型筛选；Arb 的高精度 ζ 计算使用 CPU。

## Linux 服务器快速开始

需要 Python **3.11–3.13**，建议 Python 3.12。下面命令中的 `python3.12` 可替换成服务器实际的兼容解释器。
CPU 模式不需要 NVIDIA GPU 或 CUDA，适合 32 核、60GB 的服务器。

```bash
git clone https://github.com/maris205/rh_counterexample.git
cd rh_counterexample
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py doctor
```

先跑一个低高度校准批次，检查依赖、子进程、实际 ζ 和存储：

```bash
python server.py init runs/smoke --profile smoke --workers 2
python server.py run runs/smoke
python tests/check_smoke.py runs/smoke
```

校准使用已知低高度区域，只检验程序链路，不是 RH 反例搜索结果。

然后启动服务器正式批次。32 核先开 **28 个 ζ 工作进程**，每进程限制 BLAS 为 1 线程：

```bash
python server.py init runs/server01 --backend cpu --workers 28
nohup .venv/bin/python -u server.py run runs/server01 > runs/server01/console.log 2>&1 &
python server.py status runs/server01
```

默认范围与预算：

| 项目 | 默认值 |
|---|---|
| 高度锚点 | 3×10¹²、10¹³、3×10¹³、10¹⁴ |
| 每锚点的局部基底 | 锚点 + 2097152 + 4096j，j=0…255 |
| 模型区域 | 1024 个不相连区域，每个宽 128 |
| 实部搜索 | 0.55 ≤ σ ≤ 0.65 |
| 分层与窗口 | 每锚点 4 层，最多 128 个实际 ζ 搜索窗 |
| 每窗高度范围 | 模型极值 t* ± 0.05 |
| 差分进化 | maxiter=15，popsize=8，最多 256 次目标求值/窗 |
| 真 ζ 目标求值总预算 | 最多 32768 次，另有点值复核及小盒求值 |
| 每窗超时 / CPU 会话上限 | 1800 秒 / 24 小时 |
| 模型筛选会话上限 | 4 小时 |

默认高度区间避开此前 PC 的那批区域。筛选枚举是分块、单 CPU 进程进行，随后才启动 28 个 ζ 进程；筛选阶段 CPU 没占满是预期行为。
60GB 可用于这类分块运行，但实际峰值和耗时应以服务器首批记录为准，不承诺与 PC 按核数线性加速。

## 看进度、暂停、断点续跑

```bash
python server.py status runs/server01
tail -f runs/server01/console.log
python server.py stop runs/server01
# 当前区域/窗口完成后暂停；之后继续：
nohup .venv/bin/python -u server.py run runs/server01 --resume > runs/server01/resume.log 2>&1 &
```

机器重启后，激活同一虚拟环境，运行同一 `run ... --resume` 命令。
已提交的筛选区域和已保存的窗口阶段会保留；中断时尚未保存的差分进化阶段重新计算。
同一目录有排他锁，防止两次启动互相覆盖。完成后的重跑会校验并跳过已完成结果。
`status` 展示保存的进度，重启后残留的 RUNNING 本身不能证明进程还活着。

每次 `init` 将代码和参数复制进运行目录并记录 SHA-256，后续 `git pull` 不会改变已启动实验。
续跑要求 Python 主次版本和依赖版本一致；不要修改运行副本里的参数或代码。
ERROR/TIMEOUT 为保留的终态，不会在每次续跑中自动重试。修复后用新目录重跑相应范围，避免覆盖证据。
不要使用 `python -O` 或 `PYTHONOPTIMIZE`，这会关闭必要的断言检查。

每个运行目录的主要文件都在 `research/2026-09-09-gpu-wide-survey/`：

| 文件 | 含义 |
|---|---|
| `PIPELINE_STATUS.json` | 总阶段、日志位置、错误 |
| `GPU_STATUS.json` | 模型筛选进度；CPU 模式也沿用该文件名，以 backend 字段为准 |
| `survey.sqlite3` | 每区域筛选检查点 |
| `FROZEN_WINDOWS_GPU.json` | 实际 ζ 计算之前冻结的候选 |
| `true_zeta/JOB_STATUS.json` | ζ 工作进程与完成计数 |
| `true_zeta/RESULTS.md`、`RESULTS.json` | 分组结果、标记列表、窗口哈希 |
| `true_zeta/windows/*.json` | 每窗坐标、优化过程、点值和小盒复核 |

## 更多范围与 GPU

扩大模型覆盖并同时增加实际 ζ 窗口，必须创建一个新实验：

```bash
python server.py init runs/server02 --workers 28 \
  --regions-per-anchor 1024 --strata 16 --first-offset 4194304
```

这会创建 4096 个模型区域、最多 512 个 ζ 窗口。只增加 `--regions-per-anchor` 而不增加 `--strata`，会扩大筛选范围，但不增加最终 ζ 窗口数。
可用 `--anchors`、`--sigma-min`、`--sigma-max`、`--maxiter` 等参数设置新批次，详见 `python server.py init --help`。
默认实部范围没有覆盖整个临界带；可以在 1/2<σ<1 内指定其他范围。

若服务器有兼容的 NVIDIA GPU、驱动和 CUDA 12 工具链，可额外安装 GPU 依赖：

```bash
python -m pip install -r requirements-gpu.txt
python server.py doctor --backend gpu
python server.py init runs/gpu01 --backend gpu --workers 28
nohup .venv/bin/python -u server.py run runs/gpu01 > runs/gpu01/console.log 2>&1 &
```

GPU 模式额外检查 NumPy/CuPy 的索引、交叉数和分数一致性。遇到 CuPy/CUDA 配置问题，可以新建 CPU 模式批次。
Windows 同样可运行 CLI；使用 `.venv\Scripts\python.exe`，后台启动脚本应使用隐藏窗口。

## 怎样解释结果

- k=3、k=5 是符号模型阶段，不是 ζ 零点的实部。
- 模型筛选很快或信号很强，不意味着实际 ζ 很小；原序列与置乱始终分别报告。
- `NEEDS_CHECK` 只表示点值低于预设阈值或小盒区间包围暂时未能排零，不是反例。
- 40/80 位 Arb 复核属于同一实现；高高度默认没有独立数值库复核。
- 小盒严格排零仅覆盖最佳点周围的小盒。局部优化、离散扫描都不能证明完整窗口无零。
- 严格矩形零点计数接口位于 [rectangle_count.py](research/2026-09-08-zero-lab/certification/rectangle_count.py)。只有对实际 ζ、完全离开临界线的矩形认证正零点数，才构成相应的反例证据。

算法细节见 [实验说明](research/2026-09-09-gpu-wide-survey/EXPERIMENT_PLAN.md)，此前 PC 结果见 [历史摘要](docs/PC_RESULTS.md)。

## 验证

```bash
python -m unittest discover -s tests -v
```

检查高高度相位对 100 位直接计算、精确基底加偏移、越过临界线的浮点拒绝、真实/合成零点计数、选窗并列和缺额、冻结源码损坏拒绝。
GitHub Actions 在 Ubuntu / Python 3.12 执行这些检查、完整 CPU 校准批次与完成后续跑；结果以仓库 Actions 页面为准。
