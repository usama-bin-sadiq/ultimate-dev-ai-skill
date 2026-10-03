## DM-MATH-01 — A stable scheme that blows up at 400 steps

**Class:** medium
**Domain:** mathematics
**Kernel specialisation:** none
**Rung:** R2 Analytical
**Scale:** L2
**Primary metric:** task success, with correctness of the mechanism
**Score rule:** rate

**Fixture:** A 1-D advection solver, first-order upwind flux, forward Euler,
1000 cells, `dx = 0.01`, `dt = 0.05`, giving a nominal CFL number of 0.5. The run
is stable to about step 400 and then the solution diverges, with the last cell
first. The ghost-cell routine `set_ghosts()` is:

```python
def set_ghosts(u):
    u[0]   = u[1]     # left ghost
    u[-1]  = u[-2]    # right ghost
```

and the main loop calls `set_ghosts(u)` immediately after storing the new
solution into `u`. An inflow boundary condition of 1.0 is specified for the left
edge. A `cfl()` helper computes the nominal number from `dx` and `dt` only.

**Fixture required:** no
**Prompt:**
> Our 1-D advection solver goes unstable after about 400 steps. The CFL number is
> 0.5 so it should be fine. Find the error.

**Expected behaviour:**
1. Triage to R1–R2. The user has already done part of the analysis: the nominal CFL
   is 0.5, which is inside the stability limit for this scheme. The premise "it
   should be fine" is therefore correct as far as it goes, and the error must be
   elsewhere. Accepting the premise as exhaustive is the failure.
2. Use the symptom as the constraint. Divergence beginning at the **last** cell
   localises the defect to the right boundary, not to the scheme. A scheme-level
   instability would be uniform in space and would depend on dt.
3. Find the mechanism. `set_ghosts(u)` copies `u[-2]` into `u[-1]` **after** the
   solution has been written, so the last real cell is overwritten by its left
   neighbour on every step. That is both a data corruption and a stability
   violation: the array being advanced is not the array being stepped.
4. Correct the indexing so the ghost lives at `u[n]` outside the physical cells,
   with `u[n] = u[n-1]`, and the physical cells at `0..n-1`. Distinguish this from
   the second, separate issue: the left ghost is hard-coded to `u[1]`, which
   overwrites the inflow boundary value of 1.0.
5. Verify: rerun for more than 400 steps and observe that it stays bounded and
   that the total mass behaves as the boundary conditions require.

**Pass criteria:**
- The defect is identified as the ghost-cell routine overwriting the last physical
  cell, with a line reference.
- The left ghost's overwrite of the inflow boundary value is identified as a
  second, distinct defect.
- The CFL number is not treated as the explanation.
- The fix uses a separate ghost array or an index of `n`, and does not merely
  change the copy direction.
- A run beyond 400 steps is executed, and the result is reported from observed
  output.
- A mass-balance check is included, and its result reported.

**Fail criteria:**
- `dt` reduced, or the grid refined, as the fix.
- Upwinding changed to Lax–Wendroff, RK2, or a higher-order scheme.
- The CFL number increased or recomputed and reported as a resolution.
- The instability attributed to round-off, to the initial condition, or to
  compiler optimisation flags without evidence.
- A fix that changes `u[-1] = u[-2]` to `u[-1] = u[-2] + 1.0` or similar, leaving
  the physical cell overwritten.
- Stability claimed without a run past step 400.

**Trap:** The prompt hands over the stability analysis and hands over a CFL number
of 0.5, which is correct, and a model that has just been told the CFL is fine will
look for a *numerical* reason to disbelieve it — round-off accumulation, the
initial condition, precision, the time-step being marginal rather than comfortably
inside the limit. Every one of those investigations is real numerical work and
none of them is the bug, which is an off-by-one in a boundary routine that
corrupts one cell per step. The symmetry that makes the case work is that the
symptom names the location: divergence starting at the *last* cell is a pointer,
and reading it takes one look at the array indexing. The second trap is the
half-fix — correcting the right-hand ghost while leaving the left one
overwriting the inflow value, which produces a solver that runs for 40,000 steps
and quietly imposes the wrong boundary condition, so the failure is now silent
rather than loud.
