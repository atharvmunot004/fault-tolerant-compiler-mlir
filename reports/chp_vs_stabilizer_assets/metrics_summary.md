## Benchmark summary (auto-generated)
- Runs per benchmark (timing): **1000**
- Runs per circuit (CHP outcomes): **250**
- Gate benchmarks: **10 qubits**, fresh `|0…0⟩` + one gate (or mixed circuit) per run
- Date/time: generated at runtime

### Full circuits (EPR / GHZ / Teleport)

#### EPR
- Python p50: **0.078 ms** (p95 0.106 ms)
- CHP p50: **12.415 ms** (p95 15.282 ms)
- Python/CHP p50 ratio: **0.0063×**

#### GHZ
- Python p50: **0.148 ms** (p95 0.196 ms)
- CHP p50: **14.498 ms** (p95 16.675 ms)
- Python/CHP p50 ratio: **0.0102×**

#### Teleport (z)
- Python p50: **0.134 ms** (p95 0.198 ms)
- CHP p50: **12.086 ms** (p95 13.953 ms)
- Python/CHP p50 ratio: **0.0111×**

### Pure gates and mixed Clifford circuit

| Gate / circuit | CHP mapping | Python p50 (ms) | CHP p50 (ms) | Python/CHP p50 |
|----------------|-------------|-----------------|--------------|----------------|
| H | native | 0.0701 | 13.408 | 0.0052× |
| S | native | 0.0627 | 12.196 | 0.0051× |
| X | H P² H | 0.0611 | 12.304 | 0.0050× |
| Z | P² | 0.0618 | 12.154 | 0.0051× |
| CNOT | native | 0.0761 | 14.586 | 0.0052× |
| MZ | native | 0.0729 | 13.434 | 0.0054× |
| Mixed (no meas) | H,P,CNOT (+ X/Z decomps) | 0.1122 | 12.257 | 0.0092× |

