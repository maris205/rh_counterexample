# 短区间与素数间隙通道

`short_interval_dynamics.py` 是统一路线图中的第三条数值通道。它在线性筛得到
`p <= N` 的素数指示后，在均匀的 `u=log(x)` 网格上构造：

- `short_power_error`：窗口 `h=floor(x^theta)`（默认 `theta=1/2`）内的素数计数残差
  \((\pi(x+h)-\pi(x)-h/\log x)/\sqrt{h/\log x}\)；
- `short_fixed_log_error`：固定对数宽度窗口 `log(1+h/x)=0.5` 的同类残差；
- `gap_residual`：相邻素数间隙 `g_i` 的无量纲残差 `g_i log(p_i)-1`，再插值到
  对数网格，作为局部 gap-word/动力学特征的轻量代理。

三个通道都输出 FFT top spectrum、训练/留出频率、`d/du` 局部增量，以及前五个已知
临界线虚部的固定投影。全局置乱和大块置乱控制保留在同一 JSON 中；小块置乱只会
保留累计统计的局部形状，不能单独作为独立零假设。

## 最小运行

```powershell
py -3 research/2026-09-13-prime-dynamics-zero-hypotheses/short_interval_dynamics.py `
  --n 1000000 --samples 2048 --control-reps 4 `
  --theta 0.5 --log-width 0.5 `
  --block-sizes 100000,1000000 --splits 0.55,0.67,0.80 `
  --output runs/short-interval-1e6.json
```

如果环境中的 `python` 已经指向带 NumPy 的 Python 3，也可以将 `py -3` 换成
`python`。输出中的 `purpose` 明确写明这是 feature calibration；任何峰值都必须
经过真实 ζ 的高精度求根、残差和矩形计数认证，才有资格进入 RH 候选表。

## 解释边界

窗口计数使用 `h/log(x)` 作为一阶基线，低 `x` 区域只适合仪器调试；`gap_residual`
采用随机素数间隙启发式归一化，不是独立性定理。只有当频率在多个 `N`、多个留出
切分、大块/全局控制和局部增量上都稳定时，才把它交给 zeta 直接搜索。该脚本不
声称发现任何非临界线零点。
