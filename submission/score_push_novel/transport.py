"""Small, conservative transport models. No file IO or training on application labels.

Positive temporal shifts move a forecast curve later within its KST hour-ending
day. Every temporal scenario preserves that day's original group energy. Spatial
scenarios move energy between G1/G2 at the same timestamp without changing total.
Learned coefficients form a convex mixture including the untouched reference.
"""
from __future__ import annotations

import copy
import warnings

import numpy as np
import pandas as pd


VERSION = 1
RISK_ALLOWANCE = 0.001
COEFFICIENT_PENALTY = 0.0005
POWER_ATOL = 1e-7
ENERGY_ATOL = 1e-6


def configurations():
    result = []
    for shifts in ((-1, 1), (-2, -1, 1, 2)):
        for context in ("global", "cloud_trend3"):
            for budget in (0.10, 0.25):
                result.append(dict(id=f"t{len(result):03d}", family="temporal",
                                   shifts=list(shifts), context=context, budget=budget))
    for context in ("global", "cloud_contrast3"):
        for budget in (0.10, 0.25):
            result.append(dict(id=f"s{len(result)-8:03d}", family="spatial",
                               context=context, budget=budget, transfer_fraction=0.10))
    return result


configs = configurations


def _config(config):
    known = {item["id"]: item for item in configurations()}
    if config.get("id") not in known or config != known[config["id"]]:
        raise ValueError("Configuration must exactly match a declared transport arm")


def _arrays(frame):
    required = {"ts", "grp", "p_reference", "static_capacity", "night", "cosz", "wa_cloud"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing prediction inputs: {sorted(required-set(frame.columns))}")
    ts = pd.to_datetime(frame["ts"])
    if ts.dt.tz is None:
        raise ValueError("Timezone-aware timestamps are required")
    ts = ts.dt.tz_convert("Asia/Seoul")
    if frame.duplicated(["ts", "grp"]).any():
        raise ValueError("Duplicate timestamp/group keys")
    if not frame["grp"].isin(["G1", "G2"]).all():
        raise ValueError("Only G1/G2 groups are supported")
    if not frame["night"].isin([True, False]).all():
        raise ValueError("night must be boolean")
    p = frame["p_reference"].to_numpy(float)
    cap = frame["static_capacity"].to_numpy(float)
    night = frame["night"].to_numpy(bool)
    cosz = frame["cosz"].to_numpy(float)
    if not all(np.isfinite(x).all() for x in (p, cap, cosz)) or (cap < 0).any():
        raise ValueError("Invalid reference, capacity, or solar input")
    if (p < -POWER_ATOL).any() or (p > cap + POWER_ATOL).any() or (np.abs(p[night]) > POWER_ATOL).any():
        raise ValueError("Reference already violates physical bounds")
    return ts, p, cap, night, cosz, frame["wa_cloud"].to_numpy(float)


def solar_factor(cosz):
    cosine = np.maximum(np.asarray(cosz, dtype=float), 0.0)
    exponent = np.divide(-0.059, cosine, out=np.zeros_like(cosine), where=cosine > 0)
    return np.maximum(1.098 * cosine * np.exp(exponent), 0.05)


def project_energy(values, caps, energy):
    """Euclidean projection onto a nonnegative capped simplex with given sum."""
    values = np.asarray(values, float)
    caps = np.asarray(caps, float)
    if values.shape != caps.shape or not np.isfinite(values).all() or not np.isfinite(caps).all():
        raise ValueError("Invalid simplex inputs")
    if (caps < 0).any() or not np.isfinite(energy) or energy < 0 or energy > caps.sum() + ENERGY_ATOL:
        raise ValueError("Infeasible daily energy")
    if energy == 0:
        return np.zeros_like(values)
    if energy >= caps.sum():
        return caps.copy()
    low = float(np.min(-values))
    high = float(np.max(caps-values))
    for _ in range(80):
        middle = (low+high)/2
        if np.clip(values+middle, 0, caps).sum() < energy:
            low = middle
        else:
            high = middle
    projected = np.clip(values+(low+high)/2, 0, caps)
    # Correct only floating-point summation residue, never a material imbalance.
    remainder = float(energy-projected.sum())
    if remainder:
        room = caps-projected if remainder > 0 else projected
        index = int(np.argmax(room))
        if abs(remainder) <= room[index] + 1e-10:
            projected[index] += remainder
    if not np.isclose(projected.sum(), energy, rtol=1e-10, atol=ENERGY_ATOL):
        raise ArithmeticError("Daily energy projection did not converge")
    if projected.min() < -POWER_ATOL or (projected-caps).max() > POWER_ATOL:
        raise ArithmeticError("Energy projection violates physical bounds")
    return projected


def _bucket(value):
    # Fixed forecast-only thresholds; missing context falls back to neutral.
    return 1 if not np.isfinite(value) else (0 if value < -10 else 2 if value > 10 else 1)


def make_design(frame, config):
    """Return scenario-minus-reference design and JSON-serializable provenance.

    Application labels are deliberately never read. The returned dense matrix has
    one column per context/scenario, with zeros outside that fixed context.
    """
    _config(config)
    ts, p, cap, night, cosz, cloud = _arrays(frame)
    ncontext = 1 if config["context"] == "global" else 3
    scenario_names = [f"shift_{s:+d}" for s in config["shifts"]] if config["family"] == "temporal" else ["G2_to_G1", "G1_to_G2"]
    nscenario = len(scenario_names)
    columns = [dict(context=c, scenario=s) for c in range(ncontext) for s in scenario_names]
    design = np.zeros((len(frame), len(columns)), dtype=float)
    counts = [0]*ncontext
    metadata = dict(version=VERSION, config=copy.deepcopy(config), columns=columns,
                    context_count=ncontext, scenarios_per_context=nscenario,
                    context_counts=counts, fallback_incomplete_units=0,
                    fallback_zero_shift_shape=0, neutral_missing_context_units=0,
                    time_definition="KST hour-ending timestamp minus one hour",
                    positive_shift="later within the same KST day",
                    max_scenario_energy_error=0.0)
    if not len(frame):
        return design, metadata
    positions = np.arange(len(frame))
    if config["family"] == "temporal":
        local = ts.dt.tz_localize(None)-pd.Timedelta(hours=1)
        key = pd.DataFrame({"day":local.dt.normalize().to_numpy(), "grp":frame.grp.to_numpy(), "position":positions})
        hours = local.dt.hour.to_numpy()
        fullhour = ((local.dt.minute == 0) & (local.dt.second == 0) & (local.dt.microsecond == 0)).to_numpy()
        scale = solar_factor(cosz)
        for _, group in key.groupby(["day", "grp"], sort=False):
            ix = group.position.to_numpy()
            ix = ix[np.argsort(hours[ix])]
            if len(ix) != 24 or not np.array_equal(hours[ix], np.arange(24)) or not fullhour[ix].all():
                metadata["fallback_incomplete_units"] += 1
                continue
            c = 0
            if ncontext > 1:
                morning = ix[(hours[ix] < 12) & ~night[ix]]
                afternoon = ix[(hours[ix] >= 12) & ~night[ix]]
                valid = len(morning) and len(afternoon) and np.isfinite(cloud[np.r_[morning, afternoon]]).all()
                trend = float(cloud[afternoon].mean()-cloud[morning].mean()) if valid else float("nan")
                c = _bucket(trend)
                metadata["neutral_missing_context_units"] += int(not valid)
            counts[c] += 1
            energy = float(p[ix].sum())
            normalized = p[ix]/scale[ix]
            effective_cap = np.where(night[ix], 0.0, cap[ix])
            for j, shift in enumerate(config["shifts"]):
                shape = np.zeros(24)
                if shift > 0:
                    shape[shift:] = normalized[:-shift]
                else:
                    shape[:shift] = normalized[-shift:]
                shape *= scale[ix]
                shape[night[ix]] = 0.0
                if energy == 0 or shape.sum() <= 0:
                    scenario = p[ix].copy()
                    metadata["fallback_zero_shift_shape"] += int(energy > 0)
                else:
                    shape *= energy/shape.sum()
                    scenario = project_energy(shape, effective_cap, energy)
                design[ix, c*nscenario+j] = scenario-p[ix]
                metadata["max_scenario_energy_error"] = max(metadata["max_scenario_energy_error"], float(abs(scenario.sum()-energy)))
    else:
        key = pd.DataFrame({"ts":ts.to_numpy(), "position":positions})
        groups = frame.grp.to_numpy()
        for _, group in key.groupby("ts", sort=False):
            ix = group.position.to_numpy()
            if len(ix) != 2 or set(groups[ix]) != {"G1", "G2"}:
                metadata["fallback_incomplete_units"] += 1
                continue
            i1, i2 = int(ix[groups[ix] == "G1"][0]), int(ix[groups[ix] == "G2"][0])
            c = 0
            if ncontext > 1:
                contrast = cloud[i1]-cloud[i2]
                c = _bucket(contrast)
                metadata["neutral_missing_context_units"] += int(not np.isfinite(contrast))
            counts[c] += 1
            total = p[i1]+p[i2]
            cap1, cap2 = (0.0 if night[i] else cap[i] for i in [i1, i2])
            limit = config["transfer_fraction"]*total
            positive = max(0.0, min(limit, cap1-p[i1], p[i2]))
            negative = max(0.0, min(limit, p[i1], cap2-p[i2]))
            design[[i1, i2], c*nscenario] = [positive, -positive]
            design[[i1, i2], c*nscenario+1] = [-negative, negative]
    if not np.isfinite(design).all():
        raise ArithmeticError("Nonfinite transport design")
    return design, metadata


def _coefficients(config, model, metadata):
    if model.get("version") != VERSION or model.get("config") != config or model.get("columns") != metadata["columns"]:
        raise ValueError("Model/configuration/schema mismatch")
    theta = np.asarray(model["coefficients"], dtype=float)
    if theta.shape != (len(metadata["columns"]),) or not np.isfinite(theta).all():
        raise ValueError("Invalid coefficient shape or values")
    if (theta < -1e-12).any():
        raise ValueError("Negative mixture coefficient")
    sums = theta.reshape(metadata["context_count"], metadata["scenarios_per_context"]).sum(axis=1)
    if (sums > config["budget"]+1e-10).any():
        raise ValueError("Mixture budget exceeded")
    return theta


def predict(frame, config, model):
    design, metadata = make_design(frame, config)
    theta = _coefficients(config, model, metadata)
    return frame.p_reference.to_numpy(float)+design@theta


def fit(frame, config):
    """Fit one declared arm on caller-supplied PRIMARY rows only.

    The engine must enforce the outer training time boundary. This function has no
    access to validation/application data, writes no files, and tunes no grid.
    """
    from scipy import sparse
    from scipy.optimize import linprog, OptimizeWarning
    from threadpoolctl import threadpool_limits

    design, metadata = make_design(frame, config)
    ts, reference, _, _, _, _ = _arrays(frame)
    if not {"y", "smp", "k"}.issubset(frame.columns) or not len(frame):
        raise ValueError("Nonempty labeled fitting rows are required")
    y = frame.y.to_numpy(float)
    weight = (frame.smp*frame.k).to_numpy(float)
    if not np.isfinite(y).all() or not np.isfinite(weight).all() or (weight < 0).any():
        raise ValueError("Fit labels and monetary weights must be finite; weights nonnegative")
    residual = y-reference
    baseline = float(np.dot(weight, np.abs(residual)))
    n, m = design.shape
    model = dict(version=VERSION, config=copy.deepcopy(config), columns=metadata["columns"], coefficients=[0.0]*m)
    local = ts.dt.tz_localize(None)-pd.Timedelta(hours=1)
    labels = local.dt.strftime("%Y-%m").to_numpy()+"/"+frame.grp.to_numpy(dtype=str)
    environments, environment_names = pd.factorize(labels, sort=True)
    baseline_environment = np.bincount(environments, weights=weight*np.abs(residual))
    meta = dict(status="PASS", objective="sum(SMP*k*absolute_error)/reference_W + 0.0005*sum(nonidentity_weights)",
                risk_allowance=RISK_ALLOWANCE, coefficient_penalty=COEFFICIENT_PENALTY,
                rows=n, coefficient_count=m, design=metadata, baseline_W=baseline,
                training_first_ts=ts.min().isoformat(), training_last_ts=ts.max().isoformat(),
                solver="scipy.optimize.linprog/highs", solver_threads=1, blas_threads=1,
                application_labels_read=False, physical_constraints="Convex mixture of physically valid conserved scenarios",
                fit_boundary_responsibility="Caller enforces primary-only outer cutoff; no hidden train/validation split")
    if baseline <= 0 or not np.any(design):
        meta.update(solver_status="IDENTITY_DEGENERATE", solver_iterations=0, fitted_W=baseline,
                    environment_risks=[], identity_fallback=True, max_mixture_mass=0.0)
        return model, meta
    normalized_weight = weight/baseline
    identity = sparse.eye(n, format="csr")
    matrix = sparse.csr_matrix(design)
    group_rows = sparse.csr_matrix((normalized_weight, (environments, np.arange(n))), shape=(len(environment_names), n))
    context_constraint = sparse.kron(sparse.eye(metadata["context_count"]), np.ones((1, metadata["scenarios_per_context"])), format="csr")
    constraints = sparse.vstack([
        sparse.hstack([matrix, -identity]), sparse.hstack([-matrix, -identity]),
        sparse.hstack([sparse.csr_matrix((len(environment_names), m)), group_rows]),
        sparse.hstack([context_constraint, sparse.csr_matrix((metadata["context_count"], n))]),
    ], format="csr")
    bounds = np.r_[residual, -residual, baseline_environment/baseline*(1+RISK_ALLOWANCE),
                   np.repeat(config["budget"], metadata["context_count"])]
    objective = np.r_[np.repeat(COEFFICIENT_PENALTY, m), normalized_weight]
    # highs receives threads directly; scipy warns because it does not enumerate it.
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Unrecognized options detected.*", category=OptimizeWarning)
        result = linprog(objective, A_ub=constraints, b_ub=bounds,
                         bounds=[(0, config["budget"])]*m+[(0, None)]*n,
                         method="highs", options=dict(threads=1, presolve=True,
                             primal_feasibility_tolerance=1e-9, dual_feasibility_tolerance=1e-9))
    if not result.success:
        raise RuntimeError(f"Transport LP failed (status={result.status}): {result.message}")
    theta = result.x[:m]
    if (theta < -1e-10).any():
        raise ArithmeticError("Solver returned negative mixture")
    # Canonicalize only floating-point solver residue; never tune after validation.
    theta = np.maximum(theta, 0)
    chunks = theta.reshape(metadata["context_count"], metadata["scenarios_per_context"])
    for row in chunks:
        if row.sum() > config["budget"]:
            if row.sum()-config["budget"] > 1e-7:
                raise ArithmeticError("Solver exceeded mixture budget")
            row *= config["budget"]/row.sum()
    model["coefficients"] = theta.tolist()
    _coefficients(config, model, metadata)
    predicted = reference+design@theta
    actual_error = weight*np.abs(y-predicted)
    candidate_environment = np.bincount(environments, weights=actual_error)
    risks = []
    for name, before, after in zip(environment_names, baseline_environment, candidate_environment):
        allowed = before*(1+RISK_ALLOWANCE)
        if after > allowed+max(1e-5, baseline*2e-8):
            raise ArithmeticError("Solver solution violates fitted month/group risk constraint")
        risks.append(dict(environment=str(name), reference_W=float(before), candidate_W=float(after),
                          ratio=None if before == 0 else float(after/before)))
    meta.update(solver_status=int(result.status), solver_message=result.message,
                solver_iterations=int(result.nit), normalized_objective=float(result.fun),
                fitted_W=float(actual_error.sum()), environment_risks=risks, identity_fallback=False,
                max_mixture_mass=float(chunks.sum(axis=1).max()))
    return model, meta
