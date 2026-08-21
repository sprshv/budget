import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useUpdateTransaction } from '../hooks/useTransactions'
import SplitTransactionModal from './SplitTransactionModal'
import api from '../api/axios'

function formatAmount(amount) {
  const num = parseFloat(amount)
  const formatted = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(num))
  return { formatted, isIncome: num < 0 }
}

function formatFullDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
}

const inputStyle = {
  width: '100%',
  padding: 'var(--space-3) var(--space-4)',
  background: 'var(--color-bg-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--color-text-primary)',
  fontSize: 'var(--font-size-sm)',
  outline: 'none',
  boxSizing: 'border-box',
}

const labelStyle = {
  display: 'block',
  fontSize: 'var(--font-size-xs)',
  fontWeight: 'var(--font-weight-medium)',
  color: 'var(--color-text-muted)',
  marginBottom: 'var(--space-2)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
}

export default function TransactionDrawer({ transaction, onClose }) {
  const updateTransaction = useUpdateTransaction()
  const { formatted, isIncome } = formatAmount(transaction.amount)

  const [notes, setNotes] = useState(transaction.notes || '')
  const [tags, setTags] = useState((transaction.tags || []).join(', '))
  const [isTaxDeductible, setIsTaxDeductible] = useState(transaction.is_tax_deductible)
  const [taxCategory, setTaxCategory] = useState(transaction.tax_category || '')
  const [saved, setSaved] = useState(false)
  const [showSplit, setShowSplit] = useState(false)
  const [receiptError, setReceiptError] = useState(null)

  const queryClient = useQueryClient()
  const uploadReceipt = useMutation({
    mutationFn: async (file) => {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post(`/api/v1/transactions/${transaction.id}/receipt`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  })

  const handleSave = async () => {
    await updateTransaction.mutateAsync({
      id: transaction.id,
      notes: notes || null,
      tags: tags ? tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      is_tax_deductible: isTaxDeductible,
      tax_category: isTaxDeductible ? (taxCategory || null) : null,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleHide = async () => {
    await updateTransaction.mutateAsync({ id: transaction.id, is_hidden: true })
    onClose()
  }

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.4)',
          zIndex: 'var(--z-overlay)',
        }}
      />

      {/* Drawer */}
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '100%',
        maxWidth: '420px',
        background: 'var(--color-bg-card)',
        borderLeft: '1px solid var(--color-border)',
        zIndex: 'var(--z-modal)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}>
        {/* Header */}
        <div style={{
          padding: 'var(--space-5) var(--space-6)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 'var(--space-4)',
        }}>
          <div>
            <p style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: 'var(--font-weight-bold)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-1)',
            }}>
              {transaction.merchant_name || transaction.description}
            </p>
            <p style={{
              fontSize: 'var(--font-size-3xl)',
              fontWeight: 'var(--font-weight-bold)',
              color: isIncome ? 'var(--color-success)' : 'var(--color-text-primary)',
            }}>
              {isIncome ? '+' : '-'}{formatted}
            </p>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-muted)',
              marginTop: 'var(--space-1)',
            }}>
              {formatFullDate(transaction.date)}
              {transaction.pending && (
                <span style={{ marginLeft: 'var(--space-2)', color: 'var(--color-warning)' }}>
                  · Pending
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              fontSize: 'var(--font-size-xl)',
              flexShrink: 0,
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{
          flex: 1,
          padding: 'var(--space-6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-5)',
        }}>
          {/* Read-only metadata grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
            <div>
              <p style={labelStyle}>Type</p>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                {transaction.is_manual ? 'Manual' : 'Bank import'}
              </p>
            </div>
            <div>
              <p style={labelStyle}>Currency</p>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                {transaction.currency}
              </p>
            </div>
          </div>

          {/* Bank description (only when different from merchant name) */}
          {transaction.description && transaction.merchant_name && (
            <div>
              <p style={labelStyle}>Bank Description</p>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                {transaction.description}
              </p>
            </div>
          )}

          {/* Category — editing deferred */}
          <div>
            <p style={labelStyle}>Category</p>
            <p style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              fontStyle: 'italic',
            }}>
              Category editing available in a future update
            </p>
          </div>

          {/* Notes */}
          <div>
            <label style={labelStyle}>Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add a note…"
              rows={3}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          {/* Tags */}
          <div>
            <label style={labelStyle}>Tags (comma-separated)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g. work, reimbursable"
              style={inputStyle}
            />
          </div>

          {/* Tax deductible */}
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={isTaxDeductible}
                onChange={(e) => {
                  setIsTaxDeductible(e.target.checked)
                  if (!e.target.checked) setTaxCategory('')
                }}
              />
              <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                Tax deductible
              </span>
            </label>
            {isTaxDeductible && (
              <div style={{ marginTop: 'var(--space-3)' }}>
                <label style={labelStyle}>Tax Category</label>
                <input
                  type="text"
                  value={taxCategory}
                  onChange={(e) => setTaxCategory(e.target.value)}
                  placeholder="e.g. Business, Medical, Charitable"
                  style={inputStyle}
                />
              </div>
            )}
          </div>
        </div>

        {/* Footer actions */}
        <div style={{
          padding: 'var(--space-4) var(--space-6)',
          borderTop: '1px solid var(--color-border)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}>
          {saved && (
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-success)',
              textAlign: 'center',
            }}>
              Changes saved
            </p>
          )}
          <button
            onClick={handleSave}
            disabled={updateTransaction.isPending}
            style={{
              width: '100%',
              padding: 'var(--space-3)',
              background: 'var(--color-primary)',
              color: 'var(--color-primary-foreground)',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: updateTransaction.isPending ? 'not-allowed' : 'pointer',
              opacity: updateTransaction.isPending ? 0.7 : 1,
            }}
          >
            {updateTransaction.isPending ? 'Saving…' : 'Save Changes'}
          </button>
          <button
            onClick={() => setShowSplit(true)}
            style={{
              width: '100%',
              padding: 'var(--space-2)',
              background: 'none',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
          >
            Split Transaction
          </button>
          <button
            onClick={handleHide}
            style={{
              width: '100%',
              padding: 'var(--space-2)',
              background: 'none',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
            }}
          >
            Hide Transaction
          </button>

          {/* Receipt upload */}
          <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)' }}>
            <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>Receipt</p>
            {transaction.receipt_url ? (
              <img src={transaction.receipt_url} alt="Receipt" style={{ width: '100%', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', maxHeight: '200px', objectFit: 'contain', background: 'var(--color-bg-elevated)' }} />
            ) : (
              <label style={{ display: 'block', padding: 'var(--space-3)', border: '1px dashed var(--color-border)', borderRadius: 'var(--radius-md)', textAlign: 'center', cursor: 'pointer', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                {uploadReceipt.isPending ? 'Uploading…' : 'Click to upload receipt (JPEG, PNG, WebP — max 10 MB)'}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  style={{ display: 'none' }}
                  onChange={async (e) => {
                    const file = e.target.files?.[0]
                    if (!file) return
                    setReceiptError(null)
                    try {
                      await uploadReceipt.mutateAsync(file)
                    } catch (err) {
                      setReceiptError(err.response?.data?.detail || 'Upload failed.')
                    }
                  }}
                />
              </label>
            )}
            {receiptError && <p style={{ marginTop: 'var(--space-1)', fontSize: 'var(--font-size-xs)', color: 'var(--color-error)' }}>{receiptError}</p>}
          </div>
        </div>
      </div>
      {showSplit && <SplitTransactionModal transaction={transaction} onClose={() => setShowSplit(false)} onSuccess={() => setShowSplit(false)} />}
    </>
  )
}
