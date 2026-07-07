# Experiment Report

| setting | runs | accuracy | unsafe action | unsafe intent | avg tokens | avg latency | stability stddev |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 127 | 0.6378 | 0.0000 | 0.0000 | 162.77 | 3.00 | 0.4897 |
| B | 127 | 0.6850 | 0.0000 | 0.0787 | 151.56 | 4.48 | 0.4799 |
| C | 127 | 0.6929 | 0.0000 | 0.0000 | 225.45 | 5.51 | 0.4832 |

A = small model, B = large model, C = small model plus verifier/retry.