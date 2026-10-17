export default function RiskBadge({ risk }) {
  return <span className={`risk risk-${risk.toLowerCase()}`}>{risk}</span>
}
