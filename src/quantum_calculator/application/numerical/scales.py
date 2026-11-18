import math
from fractions import Fraction

from quantum_calculator.domain.numerical.problems import PhysicalScales


def well_scales(mass: Fraction, width: Fraction, planck: Fraction) -> PhysicalScales:
    reduced_planck = float(planck) / (2 * math.pi)
    energy = reduced_planck**2 / (float(mass) * float(width) ** 2)
    return PhysicalScales(length=float(width), energy=energy, time=reduced_planck / energy)


def oscillator_scales(mass: Fraction, level_spacing: Fraction, planck: Fraction) -> PhysicalScales:
    reduced_planck = float(planck) / (2 * math.pi)
    energy = float(level_spacing)
    return PhysicalScales(
        length=reduced_planck / math.sqrt(float(mass) * energy),
        energy=energy,
        time=reduced_planck / energy,
    )
