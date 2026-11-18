INTEGRAL = "integral"

TRAJECTORY = "trajectory"

EXPECTATION_VALUE = "expectation_value"
MEASUREMENT = "measurement"
EIGENVALUE = "eigenvalue"
DEGENERACY = "degeneracy"
PROBABILITY = "probability"
PREPARED_STATE = "prepared_state"
REAL_PART = "real"
IMAGINARY_PART = "imaginary"

EIGENFUNCTIONS = "eigenfunctions"
POSITION = "position"
REFINEMENT = "refinement"
TRUNCATION = "truncation"
LEVEL = "level"
SUBINTERVALS = "subintervals"
HALF_WIDTH = "half_width"
ENERGY = "energy"

OBSERVABLES = "observables"
TIME = "time"
NORM = "norm"
RELATIVE_PHASE = "relative_phase"
REFERENCE_PHASE = "reference_phase"
TIME_REFINEMENT = "time_refinement"
STEPS = "steps"
PHASE_ERROR = "phase_error"
NORM_DRIFT = "norm_drift"
FINAL_DENSITY = "final_density"
DENSITY = "density"


def final_value(function: str) -> str:
    return f"final_{function}"


def energy_level(level: int) -> str:
    return f"energy_{level}"


def eigenfunction(level: int) -> str:
    return f"psi_{level}"


def population(level: int) -> str:
    return f"population_{level}"
