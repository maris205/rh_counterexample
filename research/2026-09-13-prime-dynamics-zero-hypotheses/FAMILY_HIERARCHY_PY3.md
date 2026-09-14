# Python 3.10 L-function family hierarchy

This report is a detector calibration, not an RH certificate. It compares the same Hurwitz-periodic evaluator for zeta, chi4, chi5, and the Davenport--Heilbronn fixture.

- Python requirement: `Python >=3.10; run with py -3.10`
- mpmath: `1.4.1`
- precision: `70 decimal digits`

## Refined roots

| family | sigma | t | distance from 1/2 | status |
|---|---:|---:|---:|---|
| zeta | 0.5 | 84.73549298051705010573531120682774141710662793424081870273552968904527 | 0.0 | CONVERGED |
| chi4 | 0.5 | 84.73174036378162860821757760454962948302105665664536292509909430828806 | 0.0 | CONVERGED |
| chi5 | 0.5 | 83.69915700187411316288328839224005567648071241029983942096363963382589 | 4.318084277547222312693175931400199785558e-77 | CONVERGED |
| dh | 0.8085171824566373855533519606068441278506702683050165728775753009160611 | 85.69934848537759217192926770894172903798782942340757667362756774163077 | 0.3085171824566373855533519606068441278507 | CONVERGED |

The DH control lands at sigma about 0.808517, while the three RH-style controls land at sigma=1/2 in these windows. This demonstrates that the free-sigma minimizer is not hard-coded to the critical line.

## Cross-family residuals

Each entry is `|F_target(s_source)|`; diagonal values are tiny because each source point was refined for its own family.

| source \ target | zeta | chi4 | chi5 | dh |
|---|---:|---:|---:|---:|
| zeta | 4.42103259142846911558779393097e-69 | 0.0121256260287419974403205881877 | 0.91818163676233214618380946083 | 3.02043906477428219513310153812 |
| chi4 | 0.00810782067553503481472234926051 | 4.14153724989878640448452344253e-69 | 0.931399591424864332721391772423 | 3.0340978597528688015244098314 |
| chi5 | 1.22555917598317319936762192894 | 0.118978812312686006286877135369 | 2.20374269790059848755683977532e-68 | 2.94821778388587178956742369019 |
| dh | 1.29251118534213975130178339509 | 1.38801740182648486465871960457 | 1.9986894925748344708706822755 | 5.21794475774695169422219700868e-69 |

## Boundary of the inference

The positive result is only detector sensitivity: the pipeline can recover a known off-line zero of the DH control family. It does not transfer that zero to zeta. A zeta candidate must be evaluated directly, refined independently at higher precision, and enclosed by an interval or argument-principle count before any mathematical claim is made.
