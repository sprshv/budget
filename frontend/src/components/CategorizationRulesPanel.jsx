import { useState } from 'react'
import {
  useCategorizationRules,
  useCreateRule,
  useDeleteRule,
} from '../hooks/useCategorizationRules'

const OPERATORS = ['contains', 'equals', 'starts_with', 'greater_than']
const MATCH_FIELDS = ['description', 'merchant_name', 'amount']

const inputStyle = {
  padding: 'var(--space-2) var(--space-3)',
  background: 'var(--color-bg-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--color-text-primary)',
  fontSize: 'var(--font-size-sm)',
  outline: 'none',
  width: '100%',
}

const selectStyle = { ...inputStyle }

export default function CategorizationRulesPanel() {
  const { data: rules = [], isLoading } = useCategorizationRules()
  const createRule = useCreateRule()
  const deleteRule = useDeleteRule()

  const [form, setForm] = useState({
    match_field: 'description',
    operator: 'contains',
    match_value: '',
    category_id: '',
    priority: 0,
  })
  const [error, setError] = useState(null)

  const handleCreate = async (e) => {
    e.preventDefault()
    setError(null)
    if (!form.match_value || !form.category_id) {
      setError('Match value and category ID are required.')
      return
    }
    try {
      await createRule.mutateAsync({ ...form, priority: parseInt(form.priority) || 0 })
      setForm({
        match_field: 'description',
        operator: 'contains',
        match_value: '',
        category_id: '',
        priority: 0,
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create rule.')
    }
  }

  return (
    <div>
      <h3
        style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: 'var(--font-weight-semibold)',
          color: 'var(--color-text-primary)',
          marginBottom: 'var(--space-4)',
        }}
      >
        Auto-Categorization Rules
      </h3>

      {/* Add rule form */}
      <form
        onSubmit={handleCreate}
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr 1fr auto',
          gap: 'var(--space-2)',
          marginBottom: 'var(--space-5)',
          alignItems: 'end',
        }}
      >
        <div>
          <label
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
              display: 'block',
              marginBottom: 'var(--space-1)',
            }}
          >
            Match field
          </label>
          <select
            value={form.match_field}
            onChange={(e) => setForm((p) => ({ ...p, match_field: e.target.value }))}
            style={selectStyle}
          >
            {MATCH_FIELDS.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
              display: 'block',
              marginBottom: 'var(--space-1)',
            }}
          >
            Operator
          </label>
          <select
            value={form.operator}
            onChange={(e) => setForm((p) => ({ ...p, operator: e.target.value }))}
            style={selectStyle}
          >
            {OPERATORS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
              display: 'block',
              marginBottom: 'var(--space-1)',
            }}
          >
            Value
          </label>
          <input
            type="text"
            value={form.match_value}
            onChange={(e) => setForm((p) => ({ ...p, match_value: e.target.value }))}
            placeholder="e.g. Starbucks"
            style={inputStyle}
          />
        </div>

        <div>
          <label
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
              display: 'block',
              marginBottom: 'var(--space-1)',
            }}
          >
            Category ID
          </label>
          <input
            type="text"
            value={form.category_id}
            onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value }))}
            placeholder="UUID"
            style={inputStyle}
          />
        </div>

        <button
          type="submit"
          disabled={createRule.isPending}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'var(--color-primary)',
            color: 'var(--color-primary-foreground)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: createRule.isPending ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Add Rule
        </button>
      </form>

      {error && (
        <div
          style={{
            padding: 'var(--space-3)',
            marginBottom: 'var(--space-4)',
            background: 'var(--color-error-light)',
            border: '1px solid var(--color-error)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-error)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {error}
        </div>
      )}

      {/* Rules list */}
      {isLoading ? (
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
          Loading rules…
        </p>
      ) : rules.length === 0 ? (
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
          No rules yet. Add one above to auto-categorize transactions.
        </p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['Field', 'Operator', 'Value', 'Priority', ''].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: 'var(--space-2) var(--space-3)',
                      textAlign: 'left',
                      color: 'var(--color-text-secondary)',
                      fontWeight: 'var(--font-weight-medium)',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <td
                    style={{
                      padding: 'var(--space-2) var(--space-3)',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    {rule.match_field}
                  </td>
                  <td
                    style={{
                      padding: 'var(--space-2) var(--space-3)',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    {rule.operator}
                  </td>
                  <td
                    style={{
                      padding: 'var(--space-2) var(--space-3)',
                      color: 'var(--color-text-primary)',
                      fontFamily: 'monospace',
                    }}
                  >
                    {rule.match_value}
                  </td>
                  <td
                    style={{
                      padding: 'var(--space-2) var(--space-3)',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    {rule.priority}
                  </td>
                  <td style={{ padding: 'var(--space-2) var(--space-3)' }}>
                    <button
                      onClick={() => deleteRule.mutate(rule.id)}
                      disabled={deleteRule.isPending}
                      style={{
                        padding: 'var(--space-1) var(--space-2)',
                        background: 'none',
                        border: '1px solid var(--color-error)',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--color-error)',
                        fontSize: 'var(--font-size-xs)',
                        cursor: 'pointer',
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
