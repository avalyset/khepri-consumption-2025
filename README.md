# Khepri — consumption-based hourly carbon intensity for the Nordic bidding zones, 2025

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22893246.svg)](https://doi.org/10.5281/zenodo.22893246)

**v2.0.1 — archived at [10.5281/zenodo.22893246](https://doi.org/10.5281/zenodo.22893246)**
(concept DOI [10.5281/zenodo.21042581](https://doi.org/10.5281/zenodo.21042581), which
always resolves to the latest version). v2.0.1 adds Green Grid Compass as related work,
with a comparison and a factor diagnostic; **the data are unchanged from
[v2.0.0](https://doi.org/10.5281/zenodo.22892503)**.

Hourly **consumption-based** (import-adjusted) carbon intensity for the nine Nordic
bidding zones Khepri publishes production-based figures for — **NO1–NO5, SE1–SE4** —
for calendar year 2025, with **FI, DK1 and DK2 as control zones** outside the primary
scope.

This is the consumption layer that Khepri v1
([10.5281/zenodo.21042581](https://doi.org/10.5281/zenodo.21042581),
[arXiv:2608.29717](https://arxiv.org/abs/2608.29717)) deferred. v1 is
production-based and unchanged; this adds the import-adjusted layer on top of the same
factor base.

## Headline figures, 2025 (gCO2eq/kWh, consumption-weighted)

| Zone | Production (v1, published) | Consumption | Carbon-free share |
|---|---:|---:|---:|
| NO1 | 23.31 | **23.12** | 97.85 % |
| NO2 | 23.85 | **26.26** | 96.04 % |
| NO3 | 21.46 | **24.20** | 97.96 % |
| NO4 | 39.65 | **39.67** | 94.97 % |
| NO5 | 24.46 | **24.39** | 97.06 % |
| SE1 | 20.63 | **21.40** | 99.17 % |
| SE2 | 20.11 | **20.61** | 98.89 % |
| SE3 | 14.53 | **17.74** | 96.18 % |
| SE4 | 17.42 | **23.52** | 92.32 % |
| *FI (control)* | *48.20* | *44.93* | *85.05 %* |
| *DK1 (control)* | *88.55* | *83.14* | *80.62 %* |
| *DK2 (control)* | *157.41* | *102.28* | *71.45 %* |

A direct-emissions variant is under development (ADR-0016, still `Proposed`) and does
**not** form part of v2.0.0.

### What imports do

Consumption is **higher** than production in seven of the nine zones. The two
exceptions, NO1 and NO5, import mainly from other Norwegian hydro zones and from SE3,
so their imports are cleaner than their own mix. The largest gaps are **SE4 (+35 %)**
and **SE3 (+22 %)**, which import across the Baltic and from DK2, DE and PL.
**A production-based figure understates what Swedish consumption actually carries.**
Per-zone deltas: `validation/v1_production_vs_v2_consumption.csv`.

Note the opposite sign in the control zones: DK2 consumption (102.28) is far *below* its
production (157.41), because Denmark exports coal- and waste-fired power and imports
Nordic hydro.

## Method

**ADR-0015 (Accepted 2026-09-22).** Proportional sharing — flow tracing — on ENTSO-E
**A11 physical cross-border flows**, over the whole ENTSO-E region: 51 bidding zones,
103 border pairs, 8 760 hours. Not a two-hop cut-out. Commercial schedules (A09) are
kept as a future sensitivity, not the main path: proportional sharing is a statement
about physical power on a network, and applied to commercial schedules it traces
contracts rather than electrons.

For each hour and zone `i`:

```
T_i = P_i + Σ_j F_ji                    total inflow = generation + imports
T_i · m_ik = G_ik + Σ_j F_ji · m_jk     mix share of production type k
```

solved as `(diag(T) − Fᵀ) M = G`, one right-hand side per production type.
`Σ_k m_ik = 1` follows from the construction and is asserted at build time
(max deviation 1.7e-15). Net flow per border: only the positive direction is kept;
simultaneous physical flow both ways on one border is a reporting artefact that would
inflate the mix through loops.

**ADR-0010 (Accepted 2026-09-22).** Balancing family B: generation and flows as given,
consumption as the residual `C_i = T_i − Σ_j F_ij`. The decisive point is that the
**hourly intensity is invariant** under this choice — load never enters the system
above. Balancing affects only the annual weighting. Residual consumption was
cross-checked against reported ENTSO-E A65 load: within ±4.4 % for every Nordic zone
except DK1 (+9.2 %, expected from the Danish resolution break documented in ADR-0012).

**Emission factors are applied to the traced mix afterwards**, never inside the
tracing, so the network stays physically consistent regardless of factor set.

**Resolution.** All series are put on a 15-minute step grid (forward-fill limited to
60 minutes, the A03 step-curve semantics) and averaged to UTC hours; an hour with a gap
is `NaN`, not interpolated. ENTSO-E A03 curve expansion is already applied at parse time
by `entsoe-py` 0.8.0 (`series_parsers.py:109-114`); what remains are missing periods,
which are real holes and are logged.

### Factor set

**Exactly Khepri v1's published table and exclusion rules** — IPCC AR5 Annex III
Table A.III.2 lifecycle medians, ADR-0001 and ADR-0002. A type with no factor there is
excluded from numerator *and* denominator, as in v1, so the two layers are directly
comparable for the same zone.

Categories deliberately **excluded** from the primary figures, with the excluded share
reported per zone in `data/annual_2025.csv`: `Waste`, `Other`, `Other renewable`,
`Fossil Peat`, and every fossil type without an AR5 row. Three of these were examined
in detail and left out on purpose:

- **Peat.** Fingrid confirmed in writing (ENTSO-E case #9470141, 13 September 2026) that
  *"all generation is allocated to the 'Fossil peat' category if the plant is classified
  as a peat-fired plant"* — whole-plant accounting by primary fuel. The column carries
  wood, coal and refuse-derived fuel, so a peat factor applied to it overstates. AR5 has
  no peat median. Excluded; 820 remains a flagged sensitivity floor.
- **Swedish `Other`.** Sweden reports no `Biomass` and no `Waste` category to ENTSO-E at
  all; the entire thermal fleet lands in `B20 Other`. v1 excludes that category, and
  introducing a factor here would make v1 and this dataset incomparable for the same
  zones.
- **`Other renewable` in NO3/NO4.** This is waste-heat recovery from smelters (Elkem
  Thamshavn; Elkem Salten and Finnfjord), not bio and not geothermal. A biomass-like
  proxy would be empirically wrong, not merely uncertain.

## Validation

**Reproduction of v1.** The production-based figures for all nine zones recompute from
this extract to within **0.0046 gCO2eq/kWh** — below the 0.005 rounding threshold of the
published table. For NO1–NO5 the values are identical to v1's own raw extract to four
decimals. `validation/v1_production_reproduction.csv`.

**Internal cross-checks**, three that point in different directions
(`validation/cross_checks.json`):

| Test | Result |
|---|---|
| LU factorisation vs iterative proportional sharing, in memory | **1.1e-12** gCO2eq/kWh over 438 839 zone-hours |
| Independently rebuilt input vs stored output | 5.0e-4 — exactly the CSV write precision |
| Physical invariant `Σ_i C_i·m_ik = Σ_i G_ik` | **2.8e-16** |
| Mix closure `Σ_k m_ik = 1` | **1.7e-15** |

The invariant matters most: neither implementation is constructed to satisfy it, so a
replication that merely repeated the same error would fail it.

**External validation.** The same tracing was tested against Google's published 2025
grid carbon intensity for 13 European cloud regions, using Electricity Maps' own
emission factors. It reproduces their figures within 0.1–4 % in Germany, northern Italy
and Spain — the zones where Electricity Maps also takes production from ENTSO-E — and
confirms that those figures rest on **direct**, not lifecycle, factors, as Google's own
label states. `validation/google_multiregion_2025.csv`.

## Contents

```
data/hourly/<ZONE>_2025.csv   8 760 hourly rows per zone: consumption (MW), carbon
                              intensity, included share, carbon-free share, and pumped
                              storage / biomass / other-renewable shares separately
data/annual_2025.csv          annual figures per zone: consumption-weighted and
                              time-averaged CI, excluded share, CFE statistics
data/factor_sets.json         the factor set and its status
validation/                   v1 reproduction, cross-checks, Google multi-region test
build.py                      rebuilds everything
```

**Carbon-free** counts hydro, wind, solar and nuclear. **Pumped-storage discharge is
reported separately and not counted**: it is energy generated earlier somewhere else,
and counting it would double-count its origin. Biomass and `Other renewable` are
likewise reported separately, not as carbon-free.

## Credit

Flow tracing by proportional sharing is **Bialek's** method, introduced for transmission
loss allocation. Its application to European electricity carbon accounting is
**Tranberg, Corradi, Lajoie, Gibon, Staffell and Andresen (2019)**, *Real-time carbon
accounting method for the European electricity markets*, **Energy Strategy Reviews**
26:100367, [doi:10.1016/j.esr.2019.100367](https://doi.org/10.1016/j.esr.2019.100367).
This dataset is an application of that method, not a new one.

Per-bidding-zone Nordic carbon intensity is not new. **Clauß et al. (2019)**,
[doi:10.3390/en12071345](https://doi.org/10.3390/en12071345), computed hourly
import-adjusted CO2eq intensity for six Scandinavian bidding zones including NO1–NO5,
for 2015. **Engstam et al. (2023)** and **Papageorgiou et al. (2020)** cover the Swedish
zones. What this adds is an archived, versioned, independently recomputable 2025 series
on an openly documented factor base, with the tracing code included.

## Related work

### INATECH Freiburg

**INATECH Freiburg (Schäfer et al.)** work on the same method family, independently and
in parallel. Their `co2map` ([co2map.de](https://co2map.de)) publishes generation- and
consumption-based grid emission intensity time series for the German federal states, and
their **Open Energy Data Server** pipeline
([INATECH-CIG/OEDS-scrips](https://github.com/INATECH-CIG/OEDS-scrips),
`exchange_analysis`) implements aggregated coupling flow tracing.

The two efforts differ in what they trace and what they produce. **Theirs builds on
commercial flows** and documents the **origin of imports** — which zones and which
generation types an importing zone's inflow came from. **This dataset builds on physical
flows (ENTSO-E A11)** and computes a **consumption mix**, which requires a balancing
convention that the aggregated method deliberately leaves open; ours is stated in
ADR-0010 (family B). Neither result substitutes for the other: an import-origin
attribution and a consumption mix answer different questions, and the flow basis differs.

An INATECH article on import origin is in preparation. Nothing is attributed to it here.
**No claim of priority is made in either direction** — this is parallel work on a shared
method, and an independent second implementation is welcome precisely because it would
test this one.

### Green Grid Compass

**Green Grid Compass** (GGC) is run by the German TSOs **50Hertz Transmission** and
**TenneT TSO**, with **FfE München** as method developer; methodology report published
**17 December 2024**, platform launched 18 February 2025
([greengrid-compass.eu](https://www.greengrid-compass.eu/),
[methodology report](https://www.ffe.de/wp-content/uploads/2025/02/GGC_Methodology-report_en.pdf)).
It is the closest thing to a direct counterpart to this dataset.

**It uses the same inputs.** The report names ENTSO-E `Actual Generation per Production
Type [16.1.B C]` and **`Physical Flows [12.1.G]`** — A75 and A11, physical flow, as here
— and states that the core elements are *"the consideration of electricity imports and
exports using flow tracing and the inclusion of combined heat and power generation using
the efficiency method"*. It covers all twelve Nordic bidding zones hourly, and publishes
production and consumption on both an operational and a lifecycle basis.

**Three method differences, as GGC states them:**

1. **Scaling.** GGC scales ENTSO-E generation to Eurostat annual statistics. This dataset
   uses ENTSO-E as reported.
2. **CHP.** GGC allocates combined heat and power by the efficiency method (ISO 14067),
   using the European Commission's harmonised reference efficiencies (their Annex B,
   2024 update). This dataset takes A75 as reported, with no CHP allocation.
3. **Factor base.** GGC's operational factors come from the IPCC 2006 Guidelines and its
   lifecycle factors add upstream chains from **ecoinvent 3.9.1 (cut-off)**, with
   country-specific values derived via Eurostat's SIEC classification. This dataset uses
   **IPCC AR5 Annex III** medians throughout.

**The numeric factor table is not reproducible from the report.** Its change log states
that the emission-factor, scaling and self-consumption tables were *"removed from the
report due to it not being up to date"*, and ecoinvent is licence-restricted. GGC's
factors could therefore not be applied to this dataset's traced mix.

#### Comparison, 2025 consumption-based lifecycle (gCO2eq/kWh)

GGC annual figures read from its public ranking endpoint. The fourth column is a
**diagnostic, not GGC's method**: this dataset's own mix with the hydro factor replaced
by the single value that best fits the five Norwegian zones — **9.07**, against AR5's 24.

| Zone | GGC | This dataset | With implied hydro 9.07 | Residual | Deviation explained |
|---|---:|---:|---:|---:|---:|
| NO1 | 11 | 23.13 | 10.24 | -0.76 | 94 % |
| NO2 | 17 | 26.26 | 13.23 | -3.77 | 59 % |
| NO3 | 14 | 24.20 | 12.21 | -1.79 | 82 % |
| NO4 | 24 | 39.67 | 27.24 | +3.24 | 79 % |
| NO5 | 7 | 24.39 | 9.74 | +2.74 | 84 % |
| SE1 | 15 | 21.40 | 10.61 | -4.39 | 31 % |
| SE2 | 16 | 20.61 | 10.05 | -5.95 | -29 % |
| SE3 | 24 | 17.74 | 11.80 | -12.20 | -95 % |
| SE4 | 44 | 23.52 | 18.49 | -25.51 | -25 % |
| FI | 49 | 44.93 | 41.62 | -7.38 | -81 % |
| DK1 | 108 | 83.14 | 79.83 | -28.17 | -13 % |
| DK2 | 122 | 102.28 | 100.03 | -21.97 | -11 % |

**What the diagnostic shows.** A hydro factor near 9 accounts for **79–94 %** of the gap
in four of the five Norwegian zones, which is consistent with an ecoinvent-based hydro
value well below the AR5 median this dataset uses. It explains nothing in the Swedish,
Danish and Finnish zones. There the candidate is the categories this dataset **excludes**
(3.6 % of SE3, 6.6 % of SE4, 8.2 % of DK2): closing those residuals would require a
factor of roughly 220–700 gCO2eq/kWh on the excluded share, which is what assigning a
real thermal value to `B20 Other` and `Waste` would look like. **No residual is within
5 %.** The Eurostat scaling and the CHP allocation are equally plausible contributors and
are **not testable** from the published report.

**No claim is made about which figure is correct.** The two are built on the same
physical data with different, openly stated conventions, and they disagree in a way that
decomposes by zone mix. Underlying files: `validation/ggc_comparison_2025.csv`,
`validation/ggc_implied_factor_test.csv`.

## What this does not cover

- **Marginal emissions.** This is an average-mix method. It does not answer what an
  extra kilowatt-hour of demand causes.
- **Commercial flows.** Physical flows only; A09 remains a future sensitivity.
- **FI upstream.** The Finnish figure is a **control**, not a delivery. It does not go
  upstream to codecarbon while the condensing/CHP assignment behind the peat column is
  unresolved.
- **DK as measurement.** Energinet already publishes production-based hourly per-bidding-zone
  CO2 for DK1/DK2 with the CHP allocation exposed. This adds no measurement there; DK1 and
  DK2 are controls.
- **Years other than 2025.**
- **The excluded categories.** Between 0.4 % and 6.5 % of the lifecycle denominator per
  zone has no verified factor. The figure is only interpretable together with the excluded
  share, which is why it is in every output file.

## Licence

Code Apache-2.0 (`LICENSE`). Data and documentation CC BY 4.0 (`LICENSE-DATA`), as v1.
