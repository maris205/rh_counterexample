# Cross-channel zero-frequency calibration

> This report is a calibration artifact. The tested frequencies are known critical-line ordinates; no entry below is evidence for a new or off-line zeta zero.

## Blind-search gate

A future unknown frequency may be passed to zeta only if it appears in at least three independent channels (Mertens increment, psi/theta increment, short-interval or gap channel), beats the 95th-percentile control distribution for each channel, survives splits 0.55/0.67/0.80 and two N scales, and has phase concentration R >= 0.80. It must then pass free-sigma Newton refinement, a local box exclusion/count, and high-precision residual checks for the actual Riemann zeta function.

The top FFT lists currently share grid buckets near 14.016, 14.385, 21.025 and 25.08 across Mertens/psi/theta. Because the channels use the same log grid and finite window, this overlap is treated as a grid/trend artifact until it survives independent grids, detrending, and block/global controls.

## Known-frequency joint diagnostic

| t | channel records | records beating control q95 | interpretation |
|---:|---:|---:|---|
| 14.134725141735 | 9 | 3 | known critical-line calibration only; not an unknown-zero candidate |
| 21.022039638772 | 9 | 0 | known critical-line calibration only; not an unknown-zero candidate |
| 25.010857580146 | 9 | 1 | known critical-line calibration only; not an unknown-zero candidate |
| 30.424876125860 | 9 | 0 | known critical-line calibration only; not an unknown-zero candidate |
| 32.935061587739 | 9 | 0 | known critical-line calibration only; not an unknown-zero candidate |

## Per-file details

### `runs\mertens-split-1e7.json`

Configuration: `{"n": 10000000, "samples": 4096, "seed": 20260913, "splits": [0.55, 0.67, 0.8]}`

| channel | t | signal holdout R2 mean | signal amplitude mean | phase resultant | control q95 R2 | beats q95 |
|---|---:|---:|---:|---:|---:|---|
| mertens | 14.134725 | 0.05466314605863021 | 2.414580040494405 | 0.9991806666720466 | 0.05416905482224863 | True |
| mertens | 21.022040 | 0.029937615314489595 | 1.7907176720511706 | 0.9999497128552868 | n/a | False |
| mertens | 25.010858 | 0.02292651940241257 | 1.5558649450955209 | 0.9996609130706416 | n/a | False |
| mertens | 30.424876 | 0.029305160102784934 | 1.761001898070672 | 0.9949098549019896 | n/a | False |
| mertens | 32.935062 | 0.024403048269301824 | 1.6080422996641002 | 0.9952248108256948 | n/a | False |

### `runs\mertens-null-5e7-v2.json`

Configuration: `{"n": 50000000, "samples": 8192, "seed": 20260913}`

| channel | t | signal holdout R2 mean | signal amplitude mean | phase resultant | control q95 R2 | beats q95 |
|---|---:|---:|---:|---:|---:|---|
| mertens | 14.134725 | 0.0329809539858947 | 2.4636949309631895 | 1.0 | 0.010762772091418647 | True |
| mertens | 21.022040 | 0.018005875472935688 | 1.8172662737442913 | 0.9999999999999999 | n/a | False |
| mertens | 25.010858 | 0.014076774076534357 | 1.6041289694515461 | 0.9999999999999999 | n/a | False |
| mertens | 30.424876 | 0.013851514833185504 | 1.5927126361613908 | 1.0 | n/a | False |
| mertens | 32.935062 | 0.010798296293987686 | 1.403205848643417 | 1.0 | n/a | False |

### `runs\lambda-psi-1e7.json`

Configuration: `{"n": 10000000, "samples": 4096, "seed": 20260913, "control_reps": 4, "block_sizes": [100000, 1000000], "splits": [0.55, 0.67, 0.8]}`

| channel | t | signal holdout R2 mean | signal amplitude mean | phase resultant | control q95 R2 | beats q95 |
|---|---:|---:|---:|---:|---:|---|
| psi_error | 14.134725 | 0.006962385982549561 | 1.8838526891286802 | 0.9972292594658472 | 0.010853431456258323 | False |
| psi_error | 21.022040 | 0.008855496866195663 | 2.130902497885954 | 0.9992971354163219 | 0.02751807873355598 | False |
| psi_error | 25.010858 | 0.008706398990031889 | 2.0965802162715024 | 0.9993521485583341 | 0.017672295722678512 | False |
| psi_error | 30.424876 | 0.009333308518307106 | 2.1789116195820277 | 0.9962329668787666 | 0.017650133000943893 | False |
| psi_error | 32.935062 | 0.0070696605155006415 | 1.894510780682066 | 0.9946135626804815 | 0.01439236728858184 | False |
| theta_error | 14.134725 | 0.007018271742155783 | 1.8941493070579203 | 0.9971915602363128 | 0.013359918506598284 | False |
| theta_error | 21.022040 | 0.008814445094918692 | 2.1299546399848572 | 0.9992455264817786 | 0.02051362859912384 | False |
| theta_error | 25.010858 | 0.008722304919166812 | 2.1019543348103005 | 0.9993719066489599 | 0.007316006692619413 | True |
| theta_error | 30.424876 | 0.009082604666523055 | 2.1526994222914375 | 0.9969997992486976 | 0.019703215093593504 | False |
| theta_error | 32.935062 | 0.006979340352953702 | 1.8860266393645724 | 0.9950011694899081 | 0.01540254194254393 | False |

### `runs\lambda-psi-5e7.json`

Configuration: `{"n": 50000000, "samples": 8192, "seed": 20260913, "control_reps": 8, "block_sizes": [1000000, 5000000], "splits": [0.55, 0.67, 0.8]}`

| channel | t | signal holdout R2 mean | signal amplitude mean | phase resultant | control q95 R2 | beats q95 |
|---|---:|---:|---:|---:|---:|---|
| psi_error | 14.134725 | 0.0033521123821380412 | 1.9393612900118193 | 0.9998864308961251 | 0.008384875925955906 | False |
| psi_error | 21.022040 | 0.004072141995401482 | 2.1296505439737623 | 0.9996580551161298 | 0.010116055682178368 | False |
| psi_error | 25.010858 | 0.004189719077087095 | 2.1564397844299386 | 0.9985696064260584 | 0.007375572499191322 | False |
| psi_error | 30.424876 | 0.003969164212088574 | 2.103993400141614 | 0.9997533449793764 | 0.00670011968497709 | False |
| psi_error | 32.935062 | 0.004104235606235222 | 2.13504175653902 | 0.9994871201556396 | 0.008151622493497296 | False |
| theta_error | 14.134725 | 0.003350946112415538 | 1.9410097093262884 | 0.9999128616574297 | 0.010817645756602918 | False |
| theta_error | 21.022040 | 0.004101340024548828 | 2.139277964650605 | 0.9994561015028625 | 0.00945329419506246 | False |
| theta_error | 25.010858 | 0.004244865709916989 | 2.1730703015771313 | 0.9986777663788551 | 0.005803808176685558 | False |
| theta_error | 30.424876 | 0.0038713361062197474 | 2.080402662525219 | 0.9998237612150488 | 0.009825159908054874 | False |
| theta_error | 32.935062 | 0.004091368453002238 | 2.134024932916279 | 0.9992890053576405 | 0.01639936588327754 | False |

### `runs\short-interval-5e7.json`

Configuration: `{"n": 50000000, "samples": 8192, "seed": 20260913, "control_reps": 8, "block_sizes": [1000000, 5000000], "splits": [0.55, 0.67, 0.8], "theta": 0.5, "log_width": 0.5}`

| channel | t | signal holdout R2 mean | signal amplitude mean | phase resultant | control q95 R2 | beats q95 |
|---|---:|---:|---:|---:|---:|---|
| short_power_error | 14.134725 | 0.000986612626084635 | 15.930890234916658 | 0.9998275013823847 | 0.0012579344652213624 | False |
| short_power_error | 21.022040 | 0.0009661145115697062 | 15.72863141187764 | 0.9996901745540226 | 0.0014708524074139148 | False |
| short_power_error | 25.010858 | 0.0011198967093839906 | 17.041107031875445 | 0.9997978339740384 | 0.0013310609490423538 | False |
| short_power_error | 30.424876 | 0.0010818037799881705 | 16.723939225216025 | 0.9994476629723973 | 0.0014852305766354158 | False |
| short_power_error | 32.935062 | 0.0011065393885811403 | 16.873344884579918 | 0.9996832173285004 | 0.0014430503308345062 | False |
| short_fixed_log_error | 14.134725 | 0.004770930952542564 | 68.66634659650437 | 0.9792682068249785 | 0.007172326847516401 | False |
| short_fixed_log_error | 21.022040 | 0.008286996002971293 | 92.45832497035194 | 0.9973690316424418 | 0.01198283807909128 | False |
| short_fixed_log_error | 25.010858 | 0.0018678687272894571 | 35.43561256241663 | 0.9575293527860024 | 0.005273377200780678 | False |
| short_fixed_log_error | 30.424876 | 0.003750183193539384 | 61.865969593186996 | 0.9934282787846032 | 0.005218732747348917 | False |
| short_fixed_log_error | 32.935062 | 0.0033726518738226075 | 58.71050061450731 | 0.9918250540692838 | 0.004277988571383638 | False |
| gap_residual | 14.134725 | 3.2897828818821016e-05 | 691.9488938816047 | 0.996523826121114 | 1.7786086764196236e-05 | True |
| gap_residual | 21.022040 | 4.441417531564636e-05 | 809.9825817937215 | 0.995816149329056 | 4.52142561829299e-05 | False |
| gap_residual | 25.010858 | 2.083593527156291e-05 | 553.3211928971085 | 0.9989738472108799 | 3.319278500937697e-05 | False |
| gap_residual | 30.424876 | 1.325514367994409e-06 | 138.08142108922237 | 0.8886365621815726 | 3.4117595737568026e-05 | False |
| gap_residual | 32.935062 | 3.11586082864359e-05 | 684.1205635540076 | 0.9994203475761875 | 3.856059278822748e-05 | False |

## Reading the current result

The report is intentionally conservative: a shared known frequency calibrates the measurement pipeline, while a putative RH counterexample requires an unknown frequency plus direct certification on zeta. Control overlap or split instability is a failure of the candidate-generation gate, not a zero.
