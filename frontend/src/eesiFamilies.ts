export const familyName = (id: string, fallback = id) => ({
  economic: 'A — Economic Baseline',
  additive: 'B — Additive Financial Exposure · Basic',
  interaction: 'C — Financial Interaction · Basic',
  real_wage: 'D — Real-Wage / Purchasing Power',
}[id] ?? fallback)

export const EXTENSION_VERSION = 'synthetic-financial-extension-v1'
