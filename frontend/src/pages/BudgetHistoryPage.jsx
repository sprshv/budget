import { useState } from 'react'
import { useBudgetHistory } from '../hooks/useBudgets'

export default function BudgetHistoryPage() {
  const [months, setMonths] = useState(6)
  const { data: history = [], isLoading } = useBudgetHistory({ months })

  const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>Budget History</h1>
        <select
          value={months}
          onChange={(e) => setMonths(Number(e.target.value))}
          style={{ padding: 'var(--space-2) var(--space-3)', background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}
        >
          {[3, 6, 12].map((m) => <option key={m} value={m}>Last {m} months</option>)}
        </select>
      </div>

      {isLoading ? (
        <p style={{ color: 'var(--color-text-muted)' }}>Loading…</p>
      ) : history.length === 0 ? (
        <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: 'var(--space-12)' }}>No budget history found.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {history.map((month) => (
            <div key={`${month.period_year}-${month.period_month}`} style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', overflow: 'hidden' }}>
              <div style={{ padding: 'var(--space-4) var(--space-5)', borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg-elevated)' }}>
                <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
                  {MONTH_NAMES[month.period_month - 1]} {month.period_year}
                </h2>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                      {['Category', 'Budgeted', 'Actual', 'Variance'].map((h) => (
                        <th key={h} style={{ padding: 'var(--space-2) var(--space-4)', textAlign: 'left', color: 'var(--color-text-secondary)', fontWeight: 'var(--font-weight-medium)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {month.budgets.map((b) => (
                      <tr key={b.budget_id} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)', fontFamily: 'monospace' }}>{b.category_id.slice(0, 8)}…</td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-primary)' }}>${b.budgeted.toFixed(2)}</td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: b.over_budget ? 'var(--color-error)' : 'var(--color-text-primary)' }}>${b.actual.toFixed(2)}</td>
                        <td style={{ padding: 'var(--space-3) var(--space-4)', color: b.variance >= 0 ? 'var(--color-success)' : 'var(--color-error)', fontWeight: 'var(--font-weight-medium)' }}>
                          {b.variance >= 0 ? '+' : ''}${b.variance.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
