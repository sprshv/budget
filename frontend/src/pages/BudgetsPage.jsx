import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useBudgets, useCreateBudget, useDeleteBudget, useBudgetProgress, useIncomeSummary, useBudgetForecast, useZeroBasedSummary } from '../hooks/useBudgets'
import { useForecast, useBudgetRecommendations } from '../hooks/useInsights'
import api from '../api/axios'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function ComparisonTable({ budgets, progressMap }) {
  const [sortBy, setSortBy] = useState('overage')

  const rows = budgets.map((b) => {
    const p = progressMap[b.id] || {}
    const budgeted = p.effective_limit || parseFloat(b.amount) || 0
    const actual = p.spent || 0
    const overage = actual - budgeted
    return { ...b, budgeted, actual, overage }
  })

  const sorted = [...rows].sort((a, b) => {
    if (sortBy === 'overage') return b.overage - a.overage
    if (sortBy === 'actual') return b.actual - a.actual
    if (sortBy === 'budgeted') return b.budgeted - a.budgeted
    return 0
  })

  const thStyle = (col) => ({
    padding: 'var(--space-3) var(--space-4)',
    textAlign: 'left',
    color: sortBy === col ? 'var(--color-primary)' : 'var(--color-text-secondary)',
    fontWeight: 'var(--font-weight-medium)',
    fontSize: 'var(--font-size-sm)',
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  })

  return (
    <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'left', color: 'var(--color-text-secondary)', fontWeight: 'var(--font-weight-medium)', fontSize: 'var(--font-size-sm)' }}>Category</th>
              <th style={thStyle('budgeted')} onClick={() => setSortBy('budgeted')}>Budgeted {sortBy === 'budgeted' ? '↓' : ''}</th>
              <th style={thStyle('actual')} onClick={() => setSortBy('actual')}>Actual {sortBy === 'actual' ? '↓' : ''}</th>
              <th style={thStyle('overage')} onClick={() => setSortBy('overage')}>Overage {sortBy === 'overage' ? '↓' : ''}</th>
              <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'left', color: 'var(--color-text-secondary)', fontWeight: 'var(--font-weight-medium)', fontSize: 'var(--font-size-sm)' }}>Visual</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => {
              const isOver = row.overage > 0
              const pct = row.budgeted > 0 ? Math.min((row.actual / row.budgeted) * 100, 100) : 0
              return (
                <tr key={row.id} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)', fontFamily: 'monospace' }}>{row.category_id.slice(0, 8)}…</td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--color-text-primary)' }}>${row.budgeted.toFixed(2)}</td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: isOver ? 'var(--color-error)' : 'var(--color-text-primary)', fontWeight: isOver ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)' }}>${row.actual.toFixed(2)}</td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: isOver ? 'var(--color-error)' : 'var(--color-success)', fontWeight: 'var(--font-weight-medium)' }}>
                    {isOver ? '+' : ''}{row.overage.toFixed(2)}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', minWidth: '120px' }}>
                    <div style={{ height: '8px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-full)' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: isOver ? 'var(--color-error)' : 'var(--color-primary)', borderRadius: 'var(--radius-full)' }} />
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const EMPTY_FORM = {
  category_id: '',
  amount: '',
  rollover_enabled: false,
  alert_threshold: '0.80',
}

export default function BudgetsPage() {
  const today = new Date()
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [year, setYear] = useState(today.getFullYear())

  const { data: budgets = [], isLoading } = useBudgets({ month, year })
  const { data: progress = [] } = useBudgetProgress({ month, year })
  const { data: income } = useIncomeSummary({ month, year })
  const { data: forecast = [] } = useBudgetForecast({ month, year })
  const progressMap = Object.fromEntries(progress.map((p) => [p.budget_id, p]))
  const forecastMap = Object.fromEntries(forecast.map((f) => [f.budget_id, f]))
  const createBudget = useCreateBudget()
  const deleteBudget = useDeleteBudget()

  const { data: zeroBasedData } = useZeroBasedSummary({ month, year })
  const { data: forecastInsights } = useForecast()
  const { data: recommendations } = useBudgetRecommendations()
  const queryClient = useQueryClient()

  const applyMutation = useMutation({
    mutationFn: ({ categoryId, amount }) =>
      api.post('/api/v1/budgets', {
        category_id: categoryId,
        amount,
        period_month: new Date().getMonth() + 1,
        period_year: new Date().getFullYear(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['budget-recommendations'] })
    },
  })

  const [view, setView] = useState('cards')
  const [showZeroBased, setShowZeroBased] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState(null)

  const handleCreate = async (e) => {
    e.preventDefault()
    setFormError(null)
    if (!form.category_id || !form.amount) {
      setFormError('Category ID and amount are required.')
      return
    }
    try {
      await createBudget.mutateAsync({
        ...form,
        amount: parseFloat(form.amount),
        alert_threshold: parseFloat(form.alert_threshold),
        period_month: month,
        period_year: year,
      })
      setShowForm(false)
      setForm(EMPTY_FORM)
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create budget.')
    }
  }

  const inputStyle = {
    width: '100%',
    padding: 'var(--space-2) var(--space-3)',
    background: 'var(--color-bg-elevated)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--color-text-primary)',
    fontSize: 'var(--font-size-sm)',
    boxSizing: 'border-box',
  }

  const labelStyle = {
    fontSize: 'var(--font-size-xs)',
    color: 'var(--color-text-secondary)',
    display: 'block',
    marginBottom: 'var(--space-1)',
  }

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--space-6)',
        }}
      >
        <h1
          style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 'var(--font-weight-bold)',
            color: 'var(--color-text-primary)',
            margin: 0,
          }}
        >
          Budgets
        </h1>
        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-sm)',
            }}
          >
            {MONTHS.map((m, i) => (
              <option key={i} value={i + 1}>
                {m}
              </option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={2020}
            max={2100}
            style={{
              width: '80px',
              padding: 'var(--space-2) var(--space-3)',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-sm)',
            }}
          />
          <div style={{ display: 'flex', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
            {['cards', 'compare'].map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                style={{
                  padding: 'var(--space-2) var(--space-3)',
                  background: view === v ? 'var(--color-primary)' : 'var(--color-bg-card)',
                  color: view === v ? 'var(--color-primary-foreground)' : 'var(--color-text-secondary)',
                  border: 'none',
                  fontSize: 'var(--font-size-sm)',
                  cursor: 'pointer',
                  fontWeight: view === v ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)',
                }}
              >
                {v === 'cards' ? 'Cards' : 'Compare'}
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowZeroBased((p) => !p)}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: showZeroBased ? 'var(--color-primary)' : 'var(--color-bg-card)',
              color: showZeroBased ? 'var(--color-primary-foreground)' : 'var(--color-text-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              cursor: 'pointer',
            }}
          >
            Zero-Based
          </button>
          <button
            onClick={() => setShowForm((p) => !p)}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'var(--color-primary)',
              color: 'var(--color-primary-foreground)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: 'pointer',
            }}
          >
            + Add Budget
          </button>
        </div>
      </div>

      {/* Add budget form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-xl)',
            padding: 'var(--space-5)',
            marginBottom: 'var(--space-5)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr auto',
            gap: 'var(--space-3)',
            alignItems: 'end',
          }}
        >
          <div>
            <label style={labelStyle}>Category ID</label>
            <input
              type="text"
              value={form.category_id}
              onChange={(e) => setForm((p) => ({ ...p, category_id: e.target.value }))}
              placeholder="UUID"
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Monthly Limit ($)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.amount}
              onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
              placeholder="0.00"
              style={inputStyle}
            />
          </div>
          <button
            type="submit"
            disabled={createBudget.isPending}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'var(--color-primary)',
              color: 'var(--color-primary-foreground)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: 'pointer',
              opacity: createBudget.isPending ? 0.7 : 1,
            }}
          >
            {createBudget.isPending ? 'Saving…' : 'Save'}
          </button>
          {formError && (
            <p
              style={{
                gridColumn: '1/-1',
                color: 'var(--color-error)',
                fontSize: 'var(--font-size-xs)',
                margin: 0,
              }}
            >
              {formError}
            </p>
          )}
        </form>
      )}

      {/* Income Summary */}
      {income && (
        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: 'var(--space-5)', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: '0 0 var(--space-4) 0' }}>Income</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
            <div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)', margin: '0 0 var(--space-1) 0' }}>Planned</p>
              <p style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', margin: 0 }}>${income.planned_income.toFixed(2)}</p>
            </div>
            <div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)', margin: '0 0 var(--space-1) 0' }}>Actual</p>
              <p style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-primary)', margin: 0 }}>${income.actual_income.toFixed(2)}</p>
            </div>
            <div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)', margin: '0 0 var(--space-1) 0' }}>Variance</p>
              <p style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: income.variance >= 0 ? 'var(--color-success)' : 'var(--color-error)', margin: 0 }}>
                {income.variance >= 0 ? '+' : ''}${income.variance.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Month-end Forecast */}
      {forecastInsights && (
        <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: 'var(--space-5)', marginBottom: 'var(--space-5)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <div>
              <h2 style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>Month-end Forecast</h2>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: '2px 0 0 0' }}>Day {forecastInsights.days_elapsed} of {forecastInsights.days_in_month}</p>
            </div>
            {(() => {
              const hasOverBudget = forecastInsights.categories.some((c) => c.status === 'over_budget')
              const hasNearLimit = forecastInsights.categories.some((c) => c.status === 'near_limit')
              const chipColor = hasOverBudget ? 'var(--color-error)' : hasNearLimit ? 'var(--color-warning)' : 'var(--color-success)'
              const chipBg = hasOverBudget ? 'var(--color-error-light)' : hasNearLimit ? 'var(--color-warning-light)' : 'var(--color-success-light)'
              const chipLabel = hasOverBudget ? 'Over Budget' : hasNearLimit ? 'Near Limit' : 'On Track'
              return (
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', margin: '0 0 var(--space-1) 0' }}>
                    ${forecastInsights.total_projected.toFixed(2)}
                  </p>
                  <span style={{ display: 'inline-flex', alignItems: 'center', padding: 'var(--space-1) var(--space-2)', background: chipBg, border: `1px solid ${chipColor}`, borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', color: chipColor, fontWeight: 'var(--font-weight-medium)' }}>
                    {chipLabel}
                  </span>
                </div>
              )
            })()}
          </div>
          {forecastInsights.categories.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {[...forecastInsights.categories]
                .sort((a, b) => b.projected_month_total - a.projected_month_total)
                .slice(0, 5)
                .map((cat) => {
                  const chipColor = cat.status === 'over_budget' ? 'var(--color-error)' : cat.status === 'near_limit' ? 'var(--color-warning)' : 'var(--color-success)'
                  const chipBg = cat.status === 'over_budget' ? 'var(--color-error-light)' : cat.status === 'near_limit' ? 'var(--color-warning-light)' : 'var(--color-success-light)'
                  const chipLabel = cat.status === 'over_budget' ? 'Over Budget' : cat.status === 'near_limit' ? 'Near Limit' : 'On Track'
                  return (
                    <div key={cat.category_id || cat.category_name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-2) var(--space-3)', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: cat.category_color || 'var(--color-primary)', flexShrink: 0 }} />
                        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{cat.category_name}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexShrink: 0 }}>
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                          Spent ${cat.spent_so_far.toFixed(2)} &rarr; Projected ${cat.projected_month_total.toFixed(2)}
                        </span>
                        <span style={{ display: 'inline-flex', alignItems: 'center', padding: '2px var(--space-2)', background: chipBg, border: `1px solid ${chipColor}`, borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', color: chipColor, fontWeight: 'var(--font-weight-medium)', whiteSpace: 'nowrap' }}>
                          {chipLabel}
                        </span>
                      </div>
                    </div>
                  )
                })}
            </div>
          )}
          {forecastInsights.categories.length === 0 && (
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', margin: 0 }}>No spending data for this month yet.</p>
          )}
        </div>
      )}

      {/* Zero-Based Budget Banner */}
      {showZeroBased && zeroBasedData && (
        <div style={{ padding: 'var(--space-4) var(--space-5)', background: zeroBasedData.unallocated > 0 ? 'var(--color-success-light)' : zeroBasedData.unallocated < 0 ? 'var(--color-error-light)' : 'var(--color-bg-elevated)', border: `1px solid ${zeroBasedData.unallocated > 0 ? 'var(--color-success)' : zeroBasedData.unallocated < 0 ? 'var(--color-error)' : 'var(--color-border)'}`, borderRadius: 'var(--radius-xl)', marginBottom: 'var(--space-4)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <p style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)', marginBottom: 'var(--space-1)' }}>
              {zeroBasedData.is_fully_allocated
                ? '✓ Every dollar is assigned'
                : zeroBasedData.unallocated > 0
                ? `$${zeroBasedData.unallocated.toFixed(2)} left to assign`
                : `$${Math.abs(zeroBasedData.unallocated).toFixed(2)} over-allocated`}
            </p>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
              Income: ${zeroBasedData.total_income.toFixed(2)} · Budgeted: ${zeroBasedData.total_budgeted.toFixed(2)}
            </p>
          </div>
        </div>
      )}

      {/* Budget list */}
      {view === 'cards' && (
        isLoading ? (
          <p style={{ color: 'var(--color-text-muted)' }}>Loading…</p>
        ) : budgets.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: 'var(--space-12)',
              color: 'var(--color-text-muted)',
            }}
          >
            <p style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-2)' }}>
              No budgets for {MONTHS[month - 1]} {year}
            </p>
            <p style={{ fontSize: 'var(--font-size-sm)' }}>
              Add a budget to start tracking your spending.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {budgets.map((budget) => (
              <div
                key={budget.id}
                style={{
                  background: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-xl)',
                  padding: 'var(--space-4) var(--space-5)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 'var(--space-4)',
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--color-text-secondary)',
                      marginBottom: 'var(--space-1)',
                      margin: '0 0 var(--space-1) 0',
                    }}
                  >
                    Category
                  </p>
                  <p
                    style={{
                      fontSize: 'var(--font-size-base)',
                      fontWeight: 'var(--font-weight-medium)',
                      color: 'var(--color-text-primary)',
                      margin: 0,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {budget.category_id}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p
                    style={{
                      fontSize: 'var(--font-size-xl)',
                      fontWeight: 'var(--font-weight-bold)',
                      color: 'var(--color-text-primary)',
                      margin: 0,
                    }}
                  >
                    ${parseFloat(budget.amount).toFixed(2)}
                  </p>
                  {budget.rollover_enabled && (
                    <p
                      style={{
                        fontSize: 'var(--font-size-xs)',
                        color: 'var(--color-text-muted)',
                        margin: 0,
                      }}
                    >
                      Rollover on
                    </p>
                  )}
                  {(() => {
                    const p = progressMap[budget.id]
                    if (!p) return null
                    const barColor = p.status === 'over' ? 'var(--color-error)' : p.status === 'warning' ? 'var(--color-warning)' : 'var(--color-primary)'
                    return (
                      <div style={{ marginTop: 'var(--space-3)', width: '200px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>${p.spent.toFixed(2)} spent</span>
                          <span style={{ fontSize: 'var(--font-size-xs)', color: barColor, fontWeight: 'var(--font-weight-semibold)' }}>{p.percentage}%</span>
                        </div>
                        <div style={{ height: '6px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-full)' }}>
                          <div style={{ height: '100%', width: `${Math.min(p.percentage, 100)}%`, background: barColor, borderRadius: 'var(--radius-full)', transition: 'width 0.3s ease' }} />
                        </div>
                        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                          ${p.remaining.toFixed(2)} remaining
                        </p>
                      </div>
                    )
                  })()}
                  {(() => {
                    const f = forecastMap[budget.id]
                    if (!f) return null
                    const chipColor = f.will_exceed ? 'var(--color-error)' : 'var(--color-success)'
                    const chipBg = f.will_exceed ? 'var(--color-error-light)' : 'var(--color-success-light)'
                    return (
                      <div style={{ marginTop: 'var(--space-2)' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-1)', padding: 'var(--space-1) var(--space-2)', background: chipBg, border: `1px solid ${chipColor}`, borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', color: chipColor, fontWeight: 'var(--font-weight-medium)' }}>
                          {f.will_exceed ? '⚠ On pace to exceed' : '✓ On track'} — projected ${f.projected_total.toFixed(2)}
                        </span>
                      </div>
                    )
                  })()}
                </div>
                <button
                  onClick={() => deleteBudget.mutate(budget.id)}
                  disabled={deleteBudget.isPending}
                  style={{
                    padding: 'var(--space-2) var(--space-3)',
                    background: 'none',
                    border: '1px solid var(--color-error)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--color-error)',
                    fontSize: 'var(--font-size-xs)',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )
      )}

      {/* Comparison table */}
      {view === 'compare' && (
        <ComparisonTable budgets={budgets} progressMap={progressMap} />
      )}

      {/* Budget Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div style={{ marginTop: 'var(--space-6)' }}>
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-3)', color: 'var(--color-text-primary)' }}>
            Budget Recommendations
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {recommendations.slice(0, 5).map((rec) => (
              <div key={rec.category_id} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: 'var(--space-3) var(--space-4)',
                background: 'var(--color-bg-card)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: rec.category_color || 'var(--color-primary)', flexShrink: 0 }} />
                  <div>
                    <div style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-sm)' }}>
                      {rec.category_name}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{rec.message}</div>
                  </div>
                </div>
                <button
                  onClick={() => applyMutation.mutate({ categoryId: rec.category_id, amount: rec.suggested_amount })}
                  disabled={applyMutation.isPending}
                  style={{
                    padding: 'var(--space-1) var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--color-primary)',
                    background: 'transparent',
                    color: 'var(--color-primary)',
                    cursor: 'pointer',
                    fontSize: 'var(--font-size-xs)',
                    fontWeight: 'var(--font-weight-medium)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Apply ${rec.suggested_amount}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
