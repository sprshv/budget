import { useState } from 'react'
import { useSplitTransaction } from '../hooks/useTransactions'

const inputStyle = {
  width: '100%',
  padding: 'var(--space-2) var(--space-3)',
  background: 'var(--color-bg-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--color-text-primary)',
  fontSize: 'var(--font-size-sm)',
  outline: 'none',
}

export default function SplitTransactionModal({ transaction, onClose, onSuccess }) {
  const splitTransaction = useSplitTransaction()
  const originalAmount = parseFloat(transaction.amount)

  const [splits, setSplits] = useState([
    { category_id: '', amount: '', notes: '' },
    { category_id: '', amount: '', notes: '' },
  ])
  const [error, setError] = useState(null)

  const totalSplit = splits.reduce((sum, s) => sum + (parseFloat(s.amount) || 0), 0)
  const remaining = (originalAmount - totalSplit).toFixed(2)
  const isBalanced = Math.abs(originalAmount - totalSplit) <= 0.01

  const updateSplit = (index, field, value) => {
    setSplits((prev) => prev.map((s, i) => i === index ? { ...s, [field]: value } : s))
  }

  const addRow = () => setSplits((prev) => [...prev, { category_id: '', amount: '', notes: '' }])
  const removeRow = (index) => {
    if (splits.length <= 2) return
    setSplits((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!isBalanced) {
      setError(`Split amounts must equal $${Math.abs(originalAmount).toFixed(2)}. Remaining: $${remaining}`)
      return
    }

    const validSplits = splits.filter((s) => s.amount && parseFloat(s.amount) !== 0)
    if (validSplits.length < 2) {
      setError('At least 2 non-zero splits are required.')
      return
    }

    try {
      await splitTransaction.mutateAsync({
        transactionId: transaction.id,
        splits: validSplits.map((s) => ({
          category_id: s.category_id || '00000000-0000-0000-0000-000000000000',
          amount: parseFloat(s.amount),
          notes: s.notes || undefined,
        })),
      })
      onSuccess?.()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to split transaction.')
    }
  }

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 'var(--z-modal)', padding: 'var(--space-4)' }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: '100%', maxWidth: '520px', background: 'var(--color-bg-card)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--color-border)', padding: 'var(--space-6)', maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>Split Transaction</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 'var(--font-size-xl)' }}>×</button>
        </div>

        <div style={{ padding: 'var(--space-3)', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-5)' }}>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            {transaction.merchant_name || transaction.description}
          </p>
          <p style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
            ${Math.abs(originalAmount).toFixed(2)}
          </p>
        </div>

        {error && <div style={{ padding: 'var(--space-3)', marginBottom: 'var(--space-4)', background: 'var(--color-error-light)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-md)', color: 'var(--color-error)', fontSize: 'var(--font-size-sm)' }}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
            {splits.map((split, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr auto auto', gap: 'var(--space-2)', alignItems: 'center' }}>
                <input type="number" step="0.01" value={split.amount} onChange={(e) => updateSplit(i, 'amount', e.target.value)} placeholder="Amount" style={inputStyle} />
                <input type="text" value={split.notes} onChange={(e) => updateSplit(i, 'notes', e.target.value)} placeholder="Note" style={{ ...inputStyle, width: '120px' }} />
                <button type="button" onClick={() => removeRow(i)} disabled={splits.length <= 2} style={{ padding: 'var(--space-2)', background: 'none', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', color: 'var(--color-text-muted)', cursor: splits.length <= 2 ? 'not-allowed' : 'pointer', fontSize: 'var(--font-size-sm)' }}>×</button>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-5)' }}>
            <button type="button" onClick={addRow} style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-primary)', background: 'none', border: 'none', cursor: 'pointer' }}>+ Add row</button>
            <p style={{ fontSize: 'var(--font-size-sm)', color: isBalanced ? 'var(--color-success)' : 'var(--color-warning)' }}>
              {isBalanced ? '✓ Balanced' : `Remaining: $${remaining}`}
            </p>
          </div>

          <button type="submit" disabled={!isBalanced || splitTransaction.isPending} style={{ width: '100%', padding: 'var(--space-3)', background: (!isBalanced || splitTransaction.isPending) ? 'var(--color-bg-elevated)' : 'var(--color-primary)', color: (!isBalanced || splitTransaction.isPending) ? 'var(--color-text-muted)' : 'var(--color-primary-foreground)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-semibold)', cursor: (!isBalanced || splitTransaction.isPending) ? 'not-allowed' : 'pointer' }}>
            {splitTransaction.isPending ? 'Splitting…' : 'Split Transaction'}
          </button>
        </form>
      </div>
    </div>
  )
}
