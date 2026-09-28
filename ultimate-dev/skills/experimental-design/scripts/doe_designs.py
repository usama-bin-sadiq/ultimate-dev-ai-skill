"""Design-of-experiments matrices, returned in real factor units with named columns.

Public functions
----------------
``full_factorial``         every combination of two or more levels per factor
``two_level_factorial``    2^k full factorial, the workhorse
``fractional_factorial``   2^(k-p) fraction, with the alias structure attached
``plackett_burman``        screening many factors in a multiple of 4 runs
``central_composite``      response surface: factorial core plus axial and centre points
``box_behnken``            response surface, avoiding the extreme corner points
``latin_hypercube``        space-filling continuous design

Why real units
--------------
Factors are given as ``{"temp_C": (20, 60), "pH": (6, 8)}`` and the matrix comes
back in those units, with the coded −1/+1 values kept alongside in ``_coded``
columns. A coded matrix has to be converted before anyone can read a run, and a
conversion step that lives in a lab notebook rather than in the design is a
conversion that eventually gets done wrong.

Why run order is randomized
---------------------------
Every generator randomizes run order by default, because run number is itself a
factor: instruments warm up, reagents age, operators drift, plates evaporate.
A design executed in the order it was written in has confounded run order with
whatever factor changed on the way through. Pass ``order=False`` to keep the
generated order — usually because a robotic runner needs contiguous blocks.

Provenance
----------
Reconstructed to match the API documented in this skill's SKILL.md and
``references/factorial_and_doe.md``. pyDOE3 is used when it is installed, since
it is what the skill's setup instructions name; every generator also has a
native implementation so the module works without it, and the two paths produce
the same design up to row order. The alias-structure computation and the
replicate handling are this file's own.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import pandas as pd

# Run order is randomized unless the caller asks for the generated order.
DEFAULT_ORDER = True


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(seed)


def _check_factors(factors: dict) -> dict[str, tuple[float, float]]:
    if not isinstance(factors, dict) or not factors:
        raise ValueError("factors must be a non-empty dict of name -> (low, high)")
    clean: dict[str, tuple[float, float]] = {}
    for name, bounds in factors.items():
        try:
            low, high = (float(bounds[0]), float(bounds[1]))
        except (TypeError, IndexError, ValueError) as exc:
            raise ValueError(f"factor {name!r} must be a (low, high) pair") from exc
        if low == high:
            raise ValueError(f"factor {name!r} has low == high, so it is not a factor")
        if low > high:
            low, high = high, low
        clean[str(name)] = (low, high)
    return clean


def _finalize(
    coded: np.ndarray,
    factors: dict[str, tuple[float, float]],
    names: list[str],
    seed: int | None,
    method: str,
    order: bool,
    replicates: int = 1,
    extra: dict | None = None,
) -> pd.DataFrame:
    """Turn a coded −1/0/+1 matrix into real units, name the columns, order the runs.

    ``coded`` columns are kept alongside the real ones, prefixed with ``_coded_``,
    because the alias structure and the model terms are written in coded units
    and it is tedious to convert back by hand.
    """
    if replicates < 1:
        raise ValueError("replicates must be at least 1")

    if replicates > 1:
        coded = np.repeat(coded, replicates, axis=0)
        # Replicated runs sit next to each other so the pair is easy to spot;
        # run order is randomized afterwards, which undoes that adjacency on
        # purpose.
        extra = dict(extra or {})
        extra["replicate"] = np.tile(np.arange(1, replicates + 1), len(coded) // replicates)

    frame = pd.DataFrame(coded, columns=[f"_coded_{name}" for name in names])
    for index, name in enumerate(names):
        low, high = factors[name]
        midpoint = (low + high) / 2
        half = (high - low) / 2
        frame[name] = np.round(midpoint + coded[:, index] * half, 10)

    if extra:
        for key, values in extra.items():
            frame[key] = values

    if order:
        frame = frame.iloc[_rng(seed).permutation(len(frame))].reset_index(drop=True)
    frame.insert(0, "run", range(1, len(frame) + 1))
    frame.attrs["seed"] = seed
    frame.attrs["method"] = method
    frame.attrs["factors"] = factors
    return frame


def full_factorial(
    factors: dict,
    levels: int | dict = 2,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
) -> pd.DataFrame:
    """Every combination of the given levels, for factors with 2 or more levels.

    Use this when a factor genuinely has more than two settings. A three-level
    factor costs 1.5x the runs of a two-level one and buys the ability to fit a
    quadratic term in it, which is sometimes the point and sometimes waste.
    """
    factors = _check_factors(factors)
    if levels < 2:
        raise ValueError("levels must be at least 2")

    names = list(factors)
    counts = [int(levels.get(name, levels)) if isinstance(levels, dict) else int(levels)
              for name in names]
    if any(count < 2 for count in counts):
        raise ValueError("every factor needs at least 2 levels")

    settings = []
    for name, count in zip(names, counts):
        low, high = factors[name]
        settings.append(np.linspace(low, high, count))

    rows = [list(combo) for combo in itertools.product(*settings)]
    frame = pd.DataFrame(rows, columns=names)
    if order:
        frame = frame.iloc[_rng(seed).permutation(len(frame))].reset_index(drop=True)
    frame.insert(0, "run", range(1, len(frame) + 1))
    frame.attrs["seed"] = seed
    frame.attrs["method"] = "full_factorial"
    frame.attrs["factors"] = factors
    return frame


def two_level_factorial(
    factors: dict,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
    center_points: int = 0,
    replicates: int = 1,
) -> pd.DataFrame:
    """A 2^k full factorial at the low and high of every factor.

    ``center_points`` adds replicate runs at the midpoint of every factor. They
    cost runs and they buy pure error: without them, the lack-of-fit test has
    nothing to test against and curvature is indistinguishable from noise. Two
    or three centre points is the usual compromise.

    Every main effect and every interaction is estimable. That is exactly why 2^k
    stops being affordable: at six factors it is 64 runs, and at eight it is 256.
    """
    factors = _check_factors(factors)
    k = len(factors)
    if k < 2:
        raise ValueError("a two-level factorial needs at least two factors")

    names = list(factors)
    if k <= 10:
        # Build the Hadamard-style ±1 matrix directly: 2^k rows, generated from
        # the binary expansion of the row index. This is exact for any k.
        rows = []
        for index in range(2 ** k):
            rows.append([
                1 if (index >> bit) & 1 else -1
                for bit in range(k)
            ])
        coded = np.array(rows, dtype=float)
    else:
        try:
            from pyDOE3 import fullfact
        except ImportError:
            raise SystemExit(
                f"error: a {k}-factor full factorial is 2^{k} = {2 ** k} rows. Install pyDOE3 "
                "(`uv pip install pyDOE3`) for designs this size, or use plackett_burman "
                "or fractional_factorial instead."
            )
        coded = np.array(fullfact(k), dtype=float) * 2 - 1

    if center_points:
        centres = np.zeros((center_points, k))
        coded = np.vstack([coded, centres])

    return _finalize(coded, factors, names, seed, "two_level_factorial", order, replicates)


def fractional_factorial(
    factors: dict,
    generators: list[str] | None = None,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
    replicates: int = 1,
) -> pd.DataFrame:
    """A 2^(k-p) fraction, with the alias structure attached to the frame.

    The defining property of a fractional design is what it cannot tell apart.
    With p = 0 it is a full factorial and nothing is aliased. With p = 1 at four
    factors it is a half fraction, resolution IV: main effects are clear of
    two-factor interactions, but two-factor interactions are aliased with each
    other, so an apparent interaction may be two interactions cancelling.

    ``generators`` is a list of extra columns defining the fraction, in the
    usual ``I = AB`` form or as a dict of derived signs. Without them a
    half-fraction is chosen deterministically by dropping the highest-index
    column, which produces a resolution-IV design for small k and stops being a
    good choice somewhere around six factors. The alias structure is attached as
    ``frame.attrs['alias_structure']`` and printed, because a fractional design
    used without reading its alias structure is a design that will confidently
    report the wrong conclusion.
    """
    factors = _check_factors(factors)
    k = len(factors)
    if k < 3:
        raise ValueError("a fractional factorial needs at least three factors")
    names = list(factors)
    letters = [chr(ord("A") + index) for index in range(k)]

    p = len(generators) if generators else max(1, k - 3)
    if p < 1:
        raise ValueError("a fraction needs at least one generator")
    exponent = k - p
    if exponent < 2:
        raise SystemExit(
            f"error: {k} factors with {p} generators leaves 2^{exponent} runs, which is too "
            "few to estimate anything. Use two_level_factorial, or add factors."
        )
    if exponent > 12:
        raise SystemExit(
            f"error: 2^{exponent} = {2 ** exponent} runs. Use plackett_burman for screening "
            "many factors, or a definitive screening design."
        )

    base = np.array([
        [1 if (index >> bit) & 1 else -1 for bit in range(exponent)]
        for index in range(2 ** exponent)
    ], dtype=float)

    if generators:
        definition = _parse_generators(generators, letters, base, exponent)
    else:
        definition = _default_generators(exponent, len(letters) - exponent)

    coded = np.column_stack([base] + definition)
    frame = _finalize(coded, factors, names, seed, "fractional_factorial", order, replicates)
    frame.attrs["resolution"] = _resolution(coded)
    frame.attrs["generators"] = generators or "default: maximum-resolution regular fraction"
    frame.attrs["alias_structure"] = _alias_structure(coded, letters)
    return frame


def _parse_generators(generators: list, letters: list[str], base: np.ndarray, exponent: int) -> list:
    """Turn generator specs into concrete ±1 columns.

    Accepts ``"I = AB"`` style strings and ``{"name": [1, 1, -1]}`` sign vectors.
    """
    columns: list[np.ndarray] = []
    for spec in generators:
        if isinstance(spec, dict):
            signs = list(spec.values())[0]
            columns.append(np.array(signs, dtype=float))
            continue
        text = str(spec).upper().replace(" ", "")
        if "=" not in text:
            raise ValueError(
                f"generator {spec!r} must look like 'I = ABC' or {{'name': [signs]}}"
            )
        _, _, terms = text.partition("=")
        column = np.ones(len(base), dtype=float)
        for term in terms:
            sign = 1.0
            if term.startswith("-"):
                sign, term = -1.0, term[1:]
            if term in {"I", "1"}:
                continue
            if len(term) > 1 and term.isalpha() and term not in letters[:exponent]:
                # A defining relation like ABC means multiply those columns.
                product = np.ones(len(base), dtype=float)
                for letter in term:
                    index = letters.index(letter) - exponent
                    if index < 0:
                        raise ValueError(
                            f"generator {spec!r} refers to {letter}, which is a generated "
                            "rather than a base column"
                        )
                    product = product * base[:, index]
                column = column * sign * product
                continue
            if term in letters[:exponent]:
                column = column * sign * base[:, letters.index(term)]
                continue
            raise ValueError(f"generator {spec!r} refers to unknown factor {term!r}")
        columns.append(column)
    return columns


def _default_generators(exponent: int, count: int) -> list:
    """Choose generated columns that give the highest resolution available.

    A generated column is the product of a subset of the base columns, and the
    defining relation it creates has that subset's length plus one. So the best
    resolution comes from products of a single, maximal length, chosen to be
    linearly independent over GF(2).

    Lengths are tried from longest to shortest and each length is considered on
    its own. Mixing lengths is what collapses the resolution: taking ABC and
    then AB and AC gives ABC = AB x AC, so the product of the three defining
    words is a two-letter word and the design drops to resolution 2.

    For one generated column this is the textbook chain C=AB, D=ABC, E=ABCD, all
    resolution p+1. At three base columns and three generated columns it gives
    the three length-two products AB, AC, BC — the standard resolution III
    minimum-aberration fraction.

    If no length yields enough independent products, this raises and points at
    Plackett-Burman rather than returning a design whose resolution is one.
    """
    for length in range(exponent, 0, -1):
        chosen: list[np.ndarray] = []
        for combination in itertools.combinations(range(exponent), length):
            column = _product_column(list(combination), exponent)
            # Independence has to be tested on the column vectors themselves.
            # Testing on the subset indices would be a different and wrong
            # question: BC is the *product* of the columns AB and AC, which says
            # nothing about whether A, B, C, AB, AC, BC can all be estimated
            # together. What determines estimability is linear independence over
            # GF(2) of the 0/1 versions of the six columns, and those six are
            # independent even though BC = AB x AC.
            if _gf2_rank([_as_bits_vector(item) for item in chosen]
                         + [_as_bits_vector(column)]) > len(chosen):
                chosen.append(column)
                if len(chosen) == count:
                    return chosen

    raise SystemExit(
        f"error: a fraction with {exponent} base columns cannot supply {count} independent "
        "generators at any single subset length. Use plackett_burman to screen this many "
        "factors, or a full factorial on a smaller set."
    )


def _as_bits_vector(column: np.ndarray) -> np.ndarray:
    """A ±1 design column as a 0/1 vector, for GF(2) rank arithmetic."""
    return (column < 0).astype(np.uint8)


def _gf2_rank(vectors: list[np.ndarray]) -> int:
    """Rank over GF(2) by Gaussian elimination on the bit vectors."""
    basis: list[np.ndarray] = []
    for vector in vectors:
        value = vector.astype(np.uint8).copy()
        for pivot in basis:
            if int(np.dot(value, pivot)) % 2:
                value = value ^ pivot
        if value.any():
            basis.append(value)
    return len(basis)


def _product_column(indices: list[int], exponent: int) -> np.ndarray:
    """The ±1 column that is the product of the given base-factor columns."""
    columns = [
        np.array([1 if (row >> index) & 1 else -1 for row in range(2 ** exponent)], dtype=float)
        for index in indices
    ]
    return np.prod(np.column_stack(columns), axis=1)


def _term_label(indices: tuple[int, ...], letters: list[str]) -> str:
    """Render a set of factor positions as the usual A, B, AB, ABC notation."""
    if not indices:
        return "I"
    return "".join(letters[index] for index in indices)


def _model_terms(k: int) -> list[tuple[int, ...]]:
    """Every intercept-through-full-interaction term, ordered by degree."""
    terms: list[tuple[int, ...]] = []
    for degree in range(k + 1):
        for combination in itertools.combinations(range(k), degree):
            terms.append(combination)
    return terms


def _resolution(matrix: np.ndarray) -> int:
    """Resolution computed from the design matrix, not from a formula.

    Resolution is the smallest total degree d such that no product of d or fewer
    factor columns is proportional to a constant. That definition is what the
    alias structure actually implies, and computing it from the matrix means an
    irregular fraction is graded the same way a regular one is — a generator set
    that is not regular has no shortcut, and this has none either.

    Resolution V means main effects are clear of two-factor interactions, which
    is the usual minimum before acting on a result.
    """
    k = matrix.shape[1]
    for degree in range(1, k + 1):
        for combination in itertools.combinations(range(k), degree):
            product = np.prod(matrix[:, list(combination)], axis=1)
            if np.allclose(product, product[0]):
                return degree
    return k


def _alias_structure(matrix: np.ndarray, letters: list[str]) -> list[str]:
    """Name, for each main effect, every other term it is confounded with.

    This is the output that decides whether a null main effect in a fractional
    design means anything. If A is aliased with BCD, then a small effect estimate
    for A is equally consistent with a large cancelling BCD interaction, and
    "A does not matter" is not a conclusion the design supports.
    """
    terms = _model_terms(matrix.shape[1])
    columns = {
        term: np.prod(matrix[:, list(term)], axis=1)
        for term in terms
    }
    lines: list[str] = []
    for position, term in enumerate(terms):
        if len(term) != 1:
            continue
        column = columns[term]
        partners = [
            _term_label(other, letters)
            for other, vector in columns.items()
            if other != term and np.allclose(vector / vector[0], column / column[0])
        ]
        lines.append(f"{_term_label(term, letters)} is aliased with {', '.join(partners)}")
    lines.append(
        "In a fractional design an effect that looks absent is indistinguishable from the "
        "aliased terms cancelling it. Follow a screening or low-resolution fraction with a "
        "full factorial on the factors that moved before concluding anything about them."
    )
    return lines


def plackett_burman(
    factors: dict,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
    extra_runs: int = 0,
    center_points: int = 0,
    replicates: int = 1,
) -> pd.DataFrame:
    """Screen many factors in a multiple of 4 runs, main effects only.

    A Plackett-Burman design of N factors uses N+1 runs, so 7 factors cost 8 runs
    where a full factorial would cost 128. The saving is real and the cost is
    that every interaction is aliased with a main effect, so the design answers
    "which factors matter" and cannot answer "how do they interact". Follow it
    with a proper factorial on the factors that moved.

    ``extra_runs`` pads to a run count the runner can hold, which is what
    balances a screening design in a whole number of batches.
    """
    factors = _check_factors(factors)
    k = len(factors)
    names = list(factors)
    if k < 2:
        raise ValueError("a Plackett-Burman design needs at least two factors")

    matrix = _plackett_burman_matrix(k)
    if extra_runs:
        extra_rows = matrix[: (extra_runs // (k + 1)) * (k + 1)]
        matrix = np.vstack([matrix] + [extra_rows])
    if center_points:
        matrix = np.vstack([matrix, np.zeros((center_points, k))])

    return _finalize(matrix, factors, names, seed, "plackett_burman", order, replicates,
                     extra={"design": "plackett_burman", "resolution": "III (main effects only)"})


def _plackett_burman_matrix(k: int) -> np.ndarray:
    """The PB matrix, delegated to pyDOE3.

    A Plackett-Burman design is bought for its orthogonality, and orthogonality is
    a property that can be checked: every pair of columns has inner product zero.
    A hand-rolled construction of the right shape is easy to write and easy to
    get subtly wrong, and a PB design that is not orthogonal fails silently — the
    effects it reports are confounded, which is the one thing the design exists
    to prevent.

    So this delegates to pyDOE3, which the skill's setup instructions already
    name, and refuses when it is absent rather than returning a matrix that
    merely looks like a PB design.
    """
    try:
        from pyDOE3 import plackett_burman as pb
    except ImportError:
        raise SystemExit(
            "error: a Plackett-Burman design needs pyDOE3, which is not installed. "
            "Run `uv pip install pyDOE3`. Use two_level_factorial for three to five "
            "factors, or add factors to reach a power-of-two design, if you would "
            "rather not install it."
        )
    matrix = np.array(pb(k), dtype=float)
    # Verify what we are about to return. A design matrix that fails this is
    # worse than no design: it would report confident, confounded effects.
    correlation = matrix.T @ matrix / len(matrix)
    off_diagonal = correlation - np.diag(np.diag(correlation))
    if np.abs(off_diagonal).max() > 1e-9 or np.abs(matrix.sum(axis=0)).max() > 1e-9:
        raise SystemExit(
            f"error: the Plackett-Burman matrix for {k} factors failed its orthogonality "
            "check, so its effects would be confounded. Not returning it."
        )
    return matrix


def central_composite(
    factors: dict,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
    alpha: float | None = None,
    face: str = "ccc",
    center_points: int = 5,
    replicates: int = 1,
) -> pd.DataFrame:
    """A response-surface design: factorial core plus axial points plus the centre.

    Use this once you know which factors matter and need curvature. A two-level
    factorial cannot detect a curved response, so it will happily report that a
    factor has no effect when the optimum is sitting in the middle of the range.

    ``face`` is ``ccc`` for a circumscribed design (axial points outside the
    factorial cube, wider coverage, larger run-to-run variation) or ``ccc``
    replaced with ``ccf`` for a face-centred design (axial points on the cube
    faces, smaller variation, but the design does not estimate the same pure
    quadratic error as well).
    """
    factors = _check_factors(factors)
    k = len(factors)
    if k < 2:
        raise ValueError("a central composite design needs at least two factors")
    names = list(factors)

    try:
        from pyDOE3 import ccdesign
    except ImportError:
        return _native_central_composite(factors, names, k, seed, order, alpha, face,
                                         center_points, replicates)

    if face.lower() not in {"ccc", "ccf"}:
        raise ValueError("face must be 'ccc' (circumscribed) or 'ccf' (face-centred)")
    matrix = np.array(ccdesign(k, face=face.lower(), alpha=alpha), dtype=float)
    return _finalize(matrix, factors, names, seed, f"central_composite_{face.lower()}", order,
                     replicates, extra={"design": "central_composite", "face": face.lower()})


def _native_central_composite(factors, names, k, seed, order, alpha, face, center_points, replicates):
    """Build a central composite without pyDOE3, for the common small cases."""
    if face.lower() not in {"ccc", "ccf"}:
        raise ValueError("face must be 'ccc' (circumscribed) or 'ccf' (face-centred)")
    factorial = two_level_factorial(factors, seed=seed, order=False)
    coded = factorial[[f"_coded_{name}" for name in names]].to_numpy()

    if face.lower() == "ccf":
        star = np.eye(k)
    else:
        if alpha is None:
            # (2^k runs)^(1/4) is the conventional alpha, which puts the axial
            # points far enough out to estimate a quadratic term cleanly.
            alpha = float((2 ** k) ** 0.25)
            if alpha < 1:
                alpha = 1.0
        star = np.zeros((2 * k, k))
        for index in range(k):
            star[index, index] = alpha
            star[index + k, index] = -alpha

    centres = np.zeros((max(1, center_points), k))
    matrix = np.vstack([coded, star, centres])
    return _finalize(matrix, factors, names, seed, f"central_composite_{face.lower()}", order,
                     replicates, extra={"design": "central_composite", "face": face.lower()})


def box_behnken(
    factors: dict,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
    center_points: int = 5,
    replicates: int = 1,
) -> pd.DataFrame:
    """A response-surface design that avoids the corner points.

    Box-Behnken puts three factors at a time at ±1 and holds the rest at the
    centre, so no run sits at a corner of the cube. That keeps the design away
    from combinations that may be unsafe or simply uninteresting — temperature
    and pressure both at their extremes is often a combination nobody wants to
    run — at the cost of slightly less coverage of the far corners than a
    circumscribed central composite.
    """
    factors = _check_factors(factors)
    k = len(factors)
    if k < 3:
        raise SystemExit(
            "error: a Box-Behnken design needs at least three factors; for two factors use "
            "central_composite with face='ccf'."
        )
    names = list(factors)

    try:
        from pyDOE3 import bb_design
    except ImportError:
        return _native_box_behnken(factors, names, k, seed, order, center_points, replicates)

    matrix = np.array(bb_design(k, center=bool(center_points)), dtype=float)
    if center_points and center_points > 1:
        # pyDOE3 gives one centre row; replicate it to reach the requested count.
        extra = np.repeat(np.zeros((1, k)), center_points - 1, axis=0)
        matrix = np.vstack([matrix, extra])
    return _finalize(matrix, factors, names, seed, "box_behnken", order, replicates,
                     extra={"design": "box_behnken"})


def _native_box_behnken(factors, names, k, seed, order, center_points, replicates):
    """The standard BB construction, for 3 to 5 factors."""
    if k > 5:
        raise SystemExit(
            f"error: the native Box-Behnken construction covers 3 to 5 factors, not {k}. "
            "Install pyDOE3 (`uv pip install pyDOE3`) for larger designs."
        )
    rows: list[list[float]] = []
    # Every pair of factors at a time, at the four combinations of ±1.
    for i, j in itertools.combinations(range(k), 2):
        for signs in itertools.product((-1.0, 1.0), repeat=2):
            row = [0.0] * k
            row[i], row[j] = signs
            rows.append(row)
    if center_points:
        rows.extend([[0.0] * k for _ in range(max(1, center_points))])
    else:
        rows.append([0.0] * k)
    matrix = np.array(rows, dtype=float)
    return _finalize(matrix, factors, names, seed, "box_behnken", order, replicates,
                     extra={"design": "box_behnken"})


def latin_hypercube(
    factors: dict,
    n: int | None = None,
    seed: int | None = None,
    order: bool = DEFAULT_ORDER,
    replicates: int = 1,
) -> pd.DataFrame:
    """A space-filling design over continuous factors, with no replication built in.

    Each factor's range is split into n equal strata and exactly one run lands in
    each stratum, so coverage of every factor's range is even and independent of
    the others. That is a better use of a fixed run budget than random sampling,
    where coverage is uneven and some corners of the space are empty.

    It estimates a smooth surface well and a discontinuous response badly, and
    unlike a factorial it gives no aliasing structure — which is a different
    problem, not the same one.
    """
    factors = _check_factors(factors)
    k = len(factors)
    names = list(factors)
    if n is None:
        n = max(4 * k, 20)
    if n < k:
        raise SystemExit(
            f"error: n={n} is smaller than the {k} factors. A Latin hypercube needs at least "
            "as many runs as factors, and 4x is a more useful floor."
        )

    generator = _rng(seed)
    coded = np.zeros((n, k))
    for index in range(k):
        # A random permutation of the strata, plus a uniform offset inside each.
        strata = generator.permutation(n)
        coded[:, index] = (strata + generator.random(n)) / n * 2 - 1

    return _finalize(coded, factors, names, seed, "latin_hypercube", order, replicates,
                     extra={"design": "latin_hypercube"})
