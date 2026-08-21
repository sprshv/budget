import { useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useTransactions, useBulkUpdateTransactions } from '../hooks/useTransactions'
import { useAnomalies } from '../hooks/useInsights'
import ReauthBanner from '../components/ReauthBanner'
import AddTransactionModal from '../components/AddTransactionModal'
import TransactionDrawer from '../components/TransactionDrawer'
import api from '../api/axios'

function formatAmount(amount) {
  const num = parseFloat(amount)
  const formatted = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(num))
  return { formatted, isIncome: num < 0 }
}

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short', day: 'numeric',
  })
}

function TransactionRow({ txn, onClick, isSelected, onSelect, isAnomaly }) {
  const { formatted, isIncome } = formatAmount(txn.amount)
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: 'var(--space-3) var(--space-5)',
        borderBottom: '1px solid var(--color-border)',
        gap: 'var(--space-3)',
        transition: 'var(--transition-fast)',
        cursor: 'pointer',
      }}
    >
      {/* Checkbox */}
      <input
        type="checkbox"
        checked={isSelected}
        onChange={(e) => {
          e.stopPropagation()
          onSelect(txn.id, e.target.checked)
        }}
        onClick={(e) => e.stopPropagation()}
        style={{ marginRight: 'var(--space-3)', accentColor: 'var(--color-primary)', cursor: 'pointer' }}
      />
      {/* Merchant icon */}
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: 'var(--radius-md)',
        background: 'var(--color-bg-elevated)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '16px',
        flexShrink: 0,
      }}>
        {isIncome ? '💵' : '💳'}
      </div>

      {/* Name + pending indicator */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', minWidth: 0 }}>
          <p style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: 'var(--font-weight-medium)',
            color: 'var(--color-text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            margin: 0,
          }}>
            {txn.merchant_name || txn.description}
          </p>
          {isAnomaly && (
            <span style={{
              fontSize: '10px',
              padding: '1px 6px',
              borderRadius: '9999px',
              background: '#fef08a',
              color: '#854d0e',
              fontWeight: '600',
              marginLeft: 'var(--space-2)',
              flexShrink: 0,
            }}>
              Unusual
            </span>
          )}
        </div>
        {txn.pending && (
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)' }}>Pending</span>
        )}
      </div>

      {/* Date */}
      <span style={{
        fontSize: 'var(--font-size-xs)',
        color: 'var(--color-text-muted)',
        whiteSpace: 'nowrap',
        flexShrink: 0,
      }}>
        {formatDate(txn.date)}
      </span>

      {/* Amount */}
      <span style={{
        fontSize: 'var(--font-size-sm)',
        fontWeight: 'var(--font-weight-semibold)',
        color: isIncome ? 'var(--color-success)' : 'var(--color-text-primary)',
        whiteSpace: 'nowrap',
        flexShrink: 0,
        minWidth: '80px',
        textAlign: 'right',
      }}>
        {isIncome ? '+' : '-'}{formatted}
      </span>
    </div>
  )
}

export default function TransactionsPage() {
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const debounceRef = useRef(null)
  const [showAdd, setShowAdd] = useState(false)
  const [selectedTxn, setSelectedTxn] = useState(null)
  const [selected, setSelected] = useState(new Set())
  const [taxDeductibleOnly, setTaxDeductibleOnly] = useState(false)
  const bulkUpdate = useBulkUpdateTransactions()
  const { data: anomalyData } = useAnomalies()
  const anomalyIds = new Set((anomalyData ?? []).map((a) => a.transaction_id))

  const handleSearch = (val) => {
    setSearch(val)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedSearch(val), 300)
  }

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading } = useTransactions({
    search: debouncedSearch || undefined,
    taxDeductible: taxDeductibleOnly || undefined,
  })

  const allTransactions = data?.pages.flatMap((p) => p.transactions) ?? []
  const total = data?.pages[0]?.total ?? 0

  async function handleExport() {
    try {
      const response = await api.get('/api/v1/transactions/export', {
        params: {},
        responseType: 'blob',
      })
      const url = URL.createObjectURL(response.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'transactions.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed', err)
    }
  }

  // Infinite scroll sentinel
  const observerRef = useRef(null)
  const sentinelRef = useCallback((node) => {
    if (observerRef.current) observerRef.current.disconnect()
    if (!node) return
    observerRef.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage()
      }
    })
    observerRef.current.observe(node)
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-bg)' }}>
      <ReauthBanner />

      {/* Header */}
      <div style={{
        padding: 'var(--space-5) var(--space-6)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 'var(--space-4)',
      }}>
        <button onClick={() => setShowAdd(true)} style={{ padding: 'var(--space-2) var(--space-4)', background: 'var(--color-primary)', color: 'var(--color-primary-foreground)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', cursor: 'pointer' }}>
          + Add Transaction
        </button>
        <div>
          <Link
            to="/dashboard"
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              textDecoration: 'none',
              display: 'block',
              marginBottom: 'var(--space-1)',
            }}
          >
            &larr; Dashboard
          </Link>
          <h1 style={{
            fontSize: 'var(--font-size-2xl)',
            fontWeight: 'var(--font-weight-bold)',
            color: 'var(--color-text-primary)',
          }}>
            Transactions
            {total > 0 && (
              <span style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: 'var(--font-weight-normal)',
                color: 'var(--color-text-muted)',
                marginLeft: 'var(--space-3)',
              }}>
                {total.toLocaleString()} total
              </span>
            )}
          </h1>
        </div>
      </div>

      {/* Search bar + filters */}
      <div style={{
        padding: 'var(--space-4) var(--space-6)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-4)',
        flexWrap: 'wrap',
      }}>
        <div style={{ position: 'relative', maxWidth: '480px', flex: '1 1 240px' }}>
          <span style={{
            position: 'absolute',
            left: 'var(--space-3)',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--color-text-muted)',
            pointerEvents: 'none',
          }}>
            🔍
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search transactions…"
            style={{
              width: '100%',
              padding: 'var(--space-3) var(--space-4) var(--space-3) var(--space-10)',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-sm)',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', cursor: 'pointer', flexShrink: 0 }}>
          <input
            type="checkbox"
            checked={taxDeductibleOnly}
            onChange={(e) => setTaxDeductibleOnly(e.target.checked)}
            style={{ accentColor: 'var(--color-primary)', cursor: 'pointer' }}
          />
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', whiteSpace: 'nowrap' }}>
            Tax Deductible Only
          </span>
        </label>
        <button
          onClick={handleExport}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'var(--color-bg-card)',
            color: 'var(--color-text-secondary)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 'var(--font-weight-medium)',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
            flexShrink: 0,
          }}
        >
          Export CSV
        </button>
      </div>

      {/* Transaction list */}
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {selected.size > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', padding: 'var(--space-3) var(--space-4)', background: 'var(--color-bg-card)', border: '1px solid var(--color-primary)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-3)' }}>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>{selected.size} selected</span>
            <button
              onClick={async () => {
                try {
                  await bulkUpdate.mutateAsync({ transactionIds: Array.from(selected), updates: { is_hidden: true } })
                  setSelected(new Set())
                } catch (err) {
                  console.error('Bulk hide failed', err)
                }
              }}
              disabled={bulkUpdate.isPending}
              style={{ padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', color: 'var(--color-text-secondary)', cursor: 'pointer' }}
            >
              Hide Selected
            </button>
            <button
              onClick={() => setSelected(new Set())}
              style={{ padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--font-size-sm)', background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
            >
              Clear
            </button>
          </div>
        )}
        {isLoading ? (
          <div style={{
            padding: 'var(--space-8)',
            textAlign: 'center',
            color: 'var(--color-text-muted)',
          }}>
            Loading transactions…
          </div>
        ) : allTransactions.length === 0 ? (
          <div style={{ padding: 'var(--space-16)', textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--space-4)' }}>📄</div>
            <h2 style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: 'var(--font-weight-semibold)',
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--space-2)',
            }}>
              {debouncedSearch ? 'No results found' : 'No transactions yet'}
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
              {debouncedSearch
                ? 'Try a different search term.'
                : 'Connect a bank account to import your transactions.'}
            </p>
          </div>
        ) : (
          <div style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            margin: 'var(--space-4)',
            overflow: 'hidden',
          }}>
            {allTransactions.map((txn) => (
              <TransactionRow
                key={txn.id}
                txn={txn}
                onClick={() => setSelectedTxn(txn)}
                isSelected={selected.has(txn.id)}
                isAnomaly={anomalyIds.has(txn.id)}
                onSelect={(id, checked) => {
                  setSelected((prev) => {
                    const next = new Set(prev)
                    checked ? next.add(id) : next.delete(id)
                    return next
                  })
                }}
              />
            ))}
            {/* Infinite scroll sentinel */}
            <div ref={sentinelRef} style={{ height: '1px' }} />
            {isFetchingNextPage && (
              <div style={{
                padding: 'var(--space-4)',
                textAlign: 'center',
                color: 'var(--color-text-muted)',
                fontSize: 'var(--font-size-sm)',
              }}>
                Loading more…
              </div>
            )}
          </div>
        )}
      </div>
      {showAdd && <AddTransactionModal onClose={() => setShowAdd(false)} onSuccess={() => setShowAdd(false)} />}
      {selectedTxn && <TransactionDrawer transaction={selectedTxn} onClose={() => setSelectedTxn(null)} />}
    </div>
  )
}
