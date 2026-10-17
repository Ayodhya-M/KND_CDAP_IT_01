export default function Bar({ value }) {
  return <span className="bar"><i style={{ width: `${value * 100}%` }} /></span>
}
