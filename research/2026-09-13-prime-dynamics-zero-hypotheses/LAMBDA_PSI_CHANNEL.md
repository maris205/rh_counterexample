# Lambda/Psi/theta 数值通道

`lambda_psi_dynamics.py` 是 Mertens 通道的并行校准脚本。它用线性筛生成
von Mangoldt 权重 `Lambda(n)` 和素数权重 `log(p)`，在 `u=log(x)` 等距网格
上计算

\[
  \psi(x)=\sum_{n\le x}\Lambda(n),\qquad
  \vartheta(x)=\sum_{p\le x}\log p,
\]

并输出 `(psi(x)-x)/sqrt(x)`、`(theta(x)-x)/sqrt(x)` 的频谱、训练/留出投影和
对数增量 `d/du`。默认固定投影使用前五个已知临界线零点虚部，只作为仪器校准。

脚本同时生成全局置乱和大块置乱的重复控制；小块置乱会保留累计函数的局部形状，
因此不能单独当作独立零假设。只有在大块/全局控制中仍有差异，并且跨多个留出
切分和多个 `N` 稳定时，才值得把频率交给真实 ζ 的独立求根程序复核。

## 最小运行

```powershell
python research/2026-09-13-prime-dynamics-zero-hypotheses/lambda_psi_dynamics.py `
  --n 1000000 --samples 2048 --control-reps 4 `
  --block-sizes 100000,1000000 --splits 0.55,0.67,0.80 `
  --output runs/lambda-psi-1e6.json
```

Windows 上若 `python` 指向 Python 2，请使用提供 NumPy 的 Python 3 环境（例如
`py -3` 或项目虚拟环境）。输出 JSON 的 `purpose` 明确标注为
`feature calibration; not a zeta-zero certificate`：任何投影峰都不是 RH 反例，
更不能替代 Arb/mpmath 高精度残差、Newton 复核和矩形计数认证。

## 当前校准结果

在 `N=5*10^7`、8 组重复和切分 `0.55,0.67,0.80` 下
(`runs/lambda-psi-5e7.json`)，首个已知临界线频率的 `psi`/`theta` 对数增量
投影约为 `R^2=0.0032--0.0037`。大块置乱的均值通常较低，但部分重复会与
真实值重叠。因此该通道目前的结论是“可复现的仪器校准与零假设压力测试”，
还没有进入未知频率搜索，更没有产生 RH 反例候选。
