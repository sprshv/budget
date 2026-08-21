import { useState, useEffect } from 'react'
import { useCreateTransaction } from '../hooks/useTransactions'
import { useAccounts } from '../hooks/useAccounts'

const inputStyle = {
  width: '100%',
  padding: 'var(--space-3) var(--space-4)',
  background: 'var(--color-bg-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--color-text-primary)',
  fontSize: 'var(--font-size-base)',
  outline: 'none',
  boxSizing: 'border-box',
}

const labelStyle = {
  display: 'block',
  fontSize: 'var(--font-size-sm)',
  fontWeight: 'var(--font-weight-medium)',
  color: 'var(--color-text-secondary)',
  marginBottom: 'var(--space-2)',
}

export default function AddTransactionModal({ onClose, onSuccess }) {
  const createTransaction = useCreateTransaction()
  const { data: accounts = [] } = useAccounts()
  const today = new Date().toISOString().split('T')[0]

  const [form, setForm] = useState({
    description: '',
    merchant_name: '',
    amount: '',
    date: today,
    account_id: '',
    notes: '',
    is_tax_deductible: false,
    currency: 'USD',
  })
  const [error, setError] = useState(null)
  const [warning, setWarning] = useState(null)

  useEffect(() => {
    if (accounts.length > 0 && !form.account_id) {
      setForm((f) => ({ ...f, account_id: accounts[0].id }))
    }
  }, [accounts])

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setWarning(null)
    if (!form.account_id) { setError('Please select an account.'); return }

    const payload = {
      description: form.description,
      merchant_name: form.merchant_name || undefined,
      amount: parseFloat(form.amount),
      date: form.date,
      account_id: form.account_id,
      notes: form.notes || undefined,
      is_tax_deductible: form.is_tax_deductible,
      currency: form.currency,
    }

    try {
      const result = await createTransaction.mutateAsync(payload)
      if (result.duplicate_warning) {
        setWarning(result.duplicate_warning.message)
      } else {
        onSuccess?.()
        onClose()
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add transaction.')
    }
  }

  return (
    <div
      onClick={onClose}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 'var(--z-modal)', padding: 'var(--space-4)' }}
    >
      <div onClick={(e) => e.stopPropagation()} style={{ width: '100%', maxWidth: '480px', background: 'var(--color-bg-card)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--color-border)', padding: 'var(--space-6)', maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-5)' }}>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>Add Transaction</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 'var(--font-size-xl)' }}>x</button>
        </div>

        {error && <div style={{ padding: 'var(--space-3)', marginBottom: 'var(--space-4)', background: 'var(--color-error-light)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-md)', color: 'var(--color-error)', fontSize: 'var(--font-size-sm)' }}>{error}</div>}

        {warning && (
          <div style={{ padding: 'var(--space-3)', marginBottom: 'var(--space-4)', background: 'var(--color-warning-light)', border: '1px solid var(--color-warning)', borderRadius: 'var(--radius-md)', color: 'var(--color-warning)', fontSize: 'var(--font-size-sm)' }}>
            {warning}
            <button onClick={onClose} style={{ display: 'block', marginTop: 'var(--space-2)', background: 'none', border: 'none', color: 'var(--color-warning)', cursor: 'pointer', fontSize: 'var(--font-size-sm)', textDecoration: 'underline' }}>Close anyway</button>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={labelStyle}>Description *</label>
            <input type="text" value={form.description} onChange={set('description')} required placeholder="e.g. Coffee at corner store" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Merchant Name</label>
            <input type="text" value={form.merchant_name} onChange={set('merchant_name')} placeholder="e.g. Starbucks" style={inputStyle} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
            <div>
              <label style={labelStyle}>Amount * (positive = expense)</label>
              <input type="number" step="0.01" value={form.amount} onChange={set('amount')} required placeholder="0.00" style={inputStyle} />
            </div>
            <div>
              <label style={labelStyle}>Date *</label>
              <input type="date" value={form.date} onChange={set('date')} required style={inputStyle} />
            </div>
          </div>
          <div>
            <label style={labelStyle}>Account *</label>
            <select value={form.account_id} onChange={set('account_id')} required style={{ ...inputStyle, cursor: 'pointer' }}>
              <option value="">Select account...</option>
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.nickname || a.name} ({a.account_type})</option>)}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Notes</label>
            <textarea value={form.notes} onChange={set('notes')} placeholder="Optional notes..." rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', cursor: 'pointer' }}>
            <input type="checkbox" checked={form.is_tax_deductible} onChange={(e) => setForm((f) => ({ ...f, is_tax_deductible: e.target.checked }))} />
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Tax deductible</span>
          </label>
          <button type="submit" disabled={createTransaction.isPending} style={{ width: '100%', padding: 'var(--space-3)', background: createTransaction.isPending ? 'var(--color-bg-elevated)' : 'var(--color-primary)', color: createTransaction.isPending ? 'var(--color-text-muted)' : 'var(--color-primary-foreground)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', cursor: createTransaction.isPending ? 'not-allowed' : 'pointer' }}>
            {createTransaction.isPending ? 'Adding...' : 'Add Transaction'}
          </button>
        </form>
      </div>
    </div>
  )
}
