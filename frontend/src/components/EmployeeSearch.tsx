import type { FormEvent } from 'react'

type EmployeeSearchProps = {
  employeeId: string
  loading: boolean
  validationError: string
  onEmployeeIdChange: (value: string) => void
  onSubmit: () => void
}

export function EmployeeSearch({
  employeeId,
  loading,
  validationError,
  onEmployeeIdChange,
  onSubmit,
}: EmployeeSearchProps) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit()
  }

  return <form className="employee-search" onSubmit={submit} noValidate>
    <label htmlFor="retention-employee-id">Employee ID</label>
    <div className="employee-search-controls">
      <input
        id="retention-employee-id"
        value={employeeId}
        onChange={(event) => onEmployeeIdChange(event.target.value)}
        placeholder="e.g. PILOT-0002"
        autoComplete="off"
        aria-describedby={validationError ? 'employee-id-error' : 'employee-id-help'}
        aria-invalid={Boolean(validationError)}
      />
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? 'Analyzing employee…' : 'Analyze Employee'}
      </button>
    </div>
    {validationError
      ? <p className="field-error" id="employee-id-error" role="alert">{validationError}</p>
      : <p className="field-help" id="employee-id-help">Try a valid Module 1 identifier such as PILOT-0001, PILOT-0002, or PILOT-0003.</p>}
  </form>
}
