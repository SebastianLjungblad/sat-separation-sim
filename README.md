# sepsim — Satellite Separation Simulator

Simulates the relative motion of multiple satellites after separation from a
launch vehicle dispenser, to assess re-contact and collision risk between
satellites and the upper stage in the hours and days after deployment.

## Motivation

Multi-satellite dispensers release payloads in a predefined sequence. Orbital
relative motion is counterintuitive: a satellite pushed radially outward
returns to the dispenser after one orbit, and a satellite pushed forward ends
up *behind* it. This project explores how separation sequence, direction and
velocity affect the minimum distance between objects.

## Status

- [x] Physical constants with sources (WGS84, EGM2008, IAU)
- [x] Clohessy–Wiltshire analytic propagation
- [x] Validation tests for the CW model
- [ ] Multi-satellite scenarios and conjunction analysis
- [ ] Plots of relative distance over time
- [ ] Numerical propagator with J2 and atmospheric drag
- [ ] CW vs. full model comparison: where does the linear model break down?
- [ ] Separation sequence optimization
- [ ] Monte Carlo collision probability

## Model

**Reference frame:** LVLH / Hill frame (RIC), centered on the dispenser:
- x: radial, outward from Earth
- y: along-track, direction of motion
- z: cross-track, along the orbit normal

**Clohessy–Wiltshire equations** (n = mean motion of the reference orbit):

    ẍ − 3n²x − 2nẏ = 0
    ÿ + 2nẋ = 0
    z̈ + n²z = 0

The closed-form solution is used, so no numerical integration is needed.

**Assumptions and limitations:**
- Circular reference orbit
- Relative distances small compared to orbit radius
- No perturbations (J2, drag, solar radiation pressure), to be added in the
  numerical model
- All units SI (m, s, kg)

## Validation

The CW implementation is verified against known analytic behavior:

| Test | Expected result |
|---|---|
| Radial push, 1 m/s | Returns to origin after one orbit |
| Along-track push, 1 m/s | Drifts 6π/n ≈ 17 km *behind* after one orbit (500 km altitude) |
| Cross-track push | Pure oscillation in z, no coupling to x/y |
| Orbital period at 500 km | ≈ 94.6 min |

## Getting started

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

## Project structure

```
src/sepsim/
├── constants.py        # physical constants with sources
└── dynamics/
    └── cw.py           # Clohessy–Wiltshire propagation
tests/
├── test_constants.py
└── test_cw.py
```

## References

- Clohessy, W. H. & Wiltshire, R. S. (1960). *Terminal Guidance System for
  Satellite Rendezvous.* Journal of the Aerospace Sciences, 27(9).
- Curtis, H. D. (2014). *Orbital Mechanics for Engineering Students* (3rd ed.).
- Vallado, D. A. *Fundamentals of Astrodynamics and Applications.*
- NIMA (2000). *WGS84 — Department of Defense World Geodetic System 1984.*