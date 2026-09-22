"""Khepri consumption-based layer, 2025 — dataset builder.

Produces hourly consumption-based carbon intensity for the nine Nordic bidding zones
Khepri v1 publishes production-based figures for (NO1-NO5, SE1-SE4), plus FI, DK1 and
DK2 as control zones outside the primary scope.

Method: ADR-0015 (Accepted 2026-09-22) — proportional sharing on ENTSO-E A11 physical
flows across the whole ENTSO-E region. ADR-0010 (Accepted 2026-09-22) — balancing
family B: generation and flows as given, consumption as residual.

Factor set: EXACTLY Khepri v1's published set and exclusion rules (ADR-0001/0002).
A type with no factor in that table is excluded from both numerator and denominator,
as in v1.

A direct-emissions variant (ADR-0016) exists but is still Proposed and is NOT part of
v2.0.0. Its builder is kept out of the release in `utkast/build_with_direct_variant.py`.

Run:  python3 build.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.expanduser("~/khepri-data/flowtracing"))
sys.path.insert(0, os.path.expanduser("~/khepri/v2"))
sys.path.insert(0, os.path.expanduser("~/khepri/src"))
from kryssjekk_tracing import bygg_input                       # noqa: E402
from khepri.factors import FACTORS as V1_FACTORS               # noqa: E402
from khepri.factors import EXCLUDED_NO_VERIFIED_FACTOR as V1_EXCL  # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
PRIMARY = {"NO_1": "NO1", "NO_2": "NO2", "NO_3": "NO3", "NO_4": "NO4", "NO_5": "NO5",
           "SE_1": "SE1", "SE_2": "SE2", "SE_3": "SE3", "SE_4": "SE4"}
CONTROL = {"FI": "FI", "DK_1": "DK1", "DK_2": "DK2"}
ALL = {**PRIMARY, **CONTROL}

# Carbon-free = hydro (reservoir + run-of-river), wind, solar, nuclear.
# Pumped-storage discharge is reported SEPARATELY: it is energy generated earlier
# somewhere else, so counting it as carbon-free would double-count its origin.
# Biomass and `Other renewable` are NOT counted carbon-free (ADR-0016 correction:
# `Other renewable` in NO3/NO4 is smelter waste heat, not bio).
CFE = ["Hydro Water Reservoir", "Hydro Run-of-river and poundage",
       "Wind Onshore", "Wind Offshore", "Solar", "Nuclear"]
SEPARATE = ["Hydro Pumped Storage", "Biomass", "Other renewable"]

SETS = {
    "lifecycle": (V1_FACTORS, set(V1_EXCL),
                  "Khepri v1 published set: IPCC AR5 Annex III Table A.III.2 lifecycle "
                  "medians, v1 exclusion rules (ADR-0001, ADR-0002). Accepted."),
}


def main():
    os.makedirs(f"{OUT}/data/hourly", exist_ok=True)
    G, Fm, types, zones, hours = bygg_input()
    T = G.sum(2) + Fm.sum(1)
    act = T > 1e-9
    C = T - Fm.sum(2)
    H, nz = len(hours), len(zones)

    M = np.full((H, nz, len(types)), np.nan)
    for h in range(H):
        a = act[h]
        if a.any():
            M[h, a] = np.linalg.solve(np.diag(T[h][a]) - Fm[h][np.ix_(a, a)].T, G[h][a])
    dev = float(np.max(np.abs(np.nansum(M[act], axis=1) - 1)))
    assert dev < 1e-9, f"mix does not sum to 1 (max deviation {dev:.2e})"
    print(f"traced {nz} zones x {H} hours; Sum_k m_ik = 1 to {dev:.1e}")

    rows = []
    for zid, name in ALL.items():
        i = zones.index(zid)
        w = np.clip(np.nan_to_num(C[:, i]), 0, None)
        mix = pd.DataFrame(M[:, i, :], index=hours, columns=types)
        df = pd.DataFrame(index=hours)
        df.index.name = "datetime_utc"
        df["consumption_mw"] = C[:, i]
        rec = dict(zone=name, scope="primary" if zid in PRIMARY else "control",
                   hours=int(np.isfinite(C[:, i]).sum()),
                   consumption_twh=float(np.nansum(C[:, i]) / 1e6))
        for sname, (fac, excl, _doc) in SETS.items():
            f = np.array([fac.get(t, np.nan) if (t in fac and t not in excl) else np.nan
                          for t in types])
            inc = np.isfinite(f)
            num = (mix.to_numpy() * np.where(inc, np.nan_to_num(f), 0.0)).sum(1)
            den = (mix.to_numpy() * inc).sum(1)
            ci = np.divide(num, den, out=np.full(H, np.nan), where=den > 1e-12)
            df[f"ci_{sname}_gco2eq_per_kwh"] = ci
            df[f"included_share_{sname}"] = den
            rec[f"ci_{sname}_consumption_weighted"] = float(np.nansum(num * w) /
                                                            np.nansum(den * w))
            rec[f"ci_{sname}_time_average"] = float(np.nanmean(ci))
            rec[f"excluded_share_{sname}_pct"] = float(100 * (1 - np.nansum(den * w) / w.sum()))
        cfe = mix[[c for c in CFE if c in mix.columns]].sum(axis=1)
        df["carbon_free_share"] = cfe
        for c in SEPARATE:
            df[f"share_{c.lower().replace(' ', '_')}"] = mix[c] if c in mix.columns else 0.0
        rec["cfe_consumption_weighted_pct"] = float(100 * (cfe * w).sum() / w.sum())
        rec["cfe_time_average_pct"] = float(100 * cfe.mean())
        rec["cfe_hours_ge_99pct"] = float(100 * (cfe >= 0.99).mean())
        rec["cfe_min_hour_pct"] = float(100 * cfe.min())
        rec["cfe_p05_pct"] = float(100 * np.percentile(cfe.dropna(), 5))
        for c in SEPARATE:
            k = c.lower().replace(" ", "_")
            rec[f"share_{k}_pct"] = float(100 * (mix[c] * w).sum() / w.sum()) if c in mix.columns else 0.0
        df.round(8).to_csv(f"{OUT}/data/hourly/{name}_2025.csv")
        rows.append(rec)
        print(f"  {name:4} {rec['scope']:8} CI {rec['ci_lifecycle_consumption_weighted']:7.2f} "
              f"CFE {rec['cfe_consumption_weighted_pct']:5.2f} % "
              f"excluded {rec['excluded_share_lifecycle_pct']:4.2f} %")

    ann = pd.DataFrame(rows)
    ann.round(4).to_csv(f"{OUT}/data/annual_2025.csv", index=False)
    json.dump({k: v[2] for k, v in SETS.items()},
              open(f"{OUT}/data/factor_sets.json", "w"), indent=1)
    return ann


if __name__ == "__main__":
    main()
