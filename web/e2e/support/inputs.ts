import path from 'node:path'

const REPOSITORY = path.resolve(import.meta.dirname, '../../..')
const REFERENCE_CASES = path.join(REPOSITORY, 'reference_cases')

export const INPUTS = {
  wellEnergy: path.join(REFERENCE_CASES, 'quantum/electron_box_1nm.json'),
  discreteSpectrum: path.join(REFERENCE_CASES, 'numerical/electron_box_1nm_discrete.json'),
  coarseSpectrum: path.join(REFERENCE_CASES, 'numerical/electron_box_1nm_coarse.json'),
  beatEvolution: path.join(REFERENCE_CASES, 'numerical/electron_box_1nm_beat.json'),
  longEvolution: path.join(REPOSITORY, 'tests/fixtures/inputs/long_time_evolution.json'),
} as const

export const CARDS = {
  wellEnergy: {
    identifier: 'quantum.infinite_square_well.energy_level',
    title: 'Nível de energia de uma partícula em um poço infinito unidimensional',
  },
  discreteSpectrum: {
    identifier: 'quantum.infinite_square_well.discrete_spectrum',
    title: 'Níveis e autofunções do poço infinito por diferenças finitas',
  },
  timeEvolution: {
    identifier: 'quantum.infinite_square_well.time_evolution',
    title: 'Evolução de uma superposição de estados do poço infinito por Crank-Nicolson',
  },
  candidateReview: {
    identifier: 'ode.first_order_linear.candidate_review',
    title: 'Revisão de uma solução candidata de um problema de valor inicial',
  },
  generalSolution: {
    identifier: 'ode.first_order_linear.general_solution',
    title: 'Solução geral de uma EDO linear de primeira ordem com coeficientes constantes',
  },
} as const

export type Card = (typeof CARDS)[keyof typeof CARDS]
