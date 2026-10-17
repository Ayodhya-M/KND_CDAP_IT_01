export const employees = [
  { id: 'EMP001', name: 'Olivia Bennett', department: 'Sales', role: 'Sales Executive', years: 3, income: 'LKR 85,000', overtime: 'Yes', satisfaction: 'Low', risk: 'High', probability: 72 },
  { id: 'EMP002', name: 'Noah Silva', department: 'Human Resources', role: 'HR Specialist', years: 6, income: 'LKR 120,000', overtime: 'No', satisfaction: 'High', risk: 'Low', probability: 19 },
  { id: 'EMP003', name: 'Ava Perera', department: 'Research & Development', role: 'Research Scientist', years: 2, income: 'LKR 95,000', overtime: 'Yes', satisfaction: 'Medium', risk: 'Medium', probability: 48 },
  { id: 'EMP004', name: 'Ethan Fernando', department: 'Sales', role: 'Sales Representative', years: 1, income: 'LKR 72,000', overtime: 'Yes', satisfaction: 'Low', risk: 'High', probability: 81 },
]

export const factors = [
  ['Overtime', 0.31, 'Increases turnover risk'],
  ['Monthly income', 0.21, 'Increases turnover risk'],
  ['Job satisfaction', 0.16, 'Increases turnover risk'],
  ['Years at company', 0.08, 'Increases turnover risk'],
  ['Job level', 0.03, 'Slightly increases risk'],
]

export const navigation = [
  ['Dashboard', '▦'], ['Employees', '♙'], ['New prediction', '＋'], ['Explainability', '⌁'],
]
