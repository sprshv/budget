import { useState } from 'react'
import { useCategories, useCreateCategory, useDeleteCategory } from '../hooks/useCategories'

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

export default function CategoriesPanel() {
  const { data: categories = [], isLoading } = useCategories()
  const createCategory = useCreateCategory()
  const deleteCategory = useDeleteCategory()

  const [form, setForm] = useState({
    name: '',
    color: '#22b780',
    icon: '',
    parent_id: '',
    is_income: false,
  })
  const [error, setError] = useState(null)

  const systemCats = categories.filter((c) => c.is_system)
  const customCats = categories.filter((c) => !c.is_system)

  const handleCreate = async (e) => {
    e.preventDefault()
    setError(null)
    if (!form.name.trim()) {
      setError('Name is required.')
      return
    }
    try {
      await createCategory.mutateAsync({
        name: form.name,
        color: form.color || undefined,
        icon: form.icon || undefined,
        parent_id: form.parent_id || undefined,
        is_income: form.is_income,
      })
      setForm({ name: '', color: '#22b780', icon: '', parent_id: '', is_income: false })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create category.')
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
        Categories
      </h3>

      {/* Create form */}
      <form
        onSubmit={handleCreate}
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto auto auto auto auto',
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
            Name
          </label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="e.g. Travel"
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
            Color
          </label>
          <input
            type="color"
            value={form.color}
            onChange={(e) => setForm((p) => ({ ...p, color: e.target.value }))}
            style={{
              width: '44px',
              height: '38px',
              padding: '2px',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
            }}
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
            Icon
          </label>
          <input
            type="text"
            value={form.icon}
            onChange={(e) => setForm((p) => ({ ...p, icon: e.target.value }))}
            placeholder="✈️"
            style={{ ...inputStyle, width: '60px' }}
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
            Parent
          </label>
          <select
            value={form.parent_id}
            onChange={(e) => setForm((p) => ({ ...p, parent_id: e.target.value }))}
            style={{ ...inputStyle, width: '120px' }}
          >
            <option value="">None</option>
            {systemCats.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
            paddingTop: 'var(--space-4)',
          }}
        >
          <input
            type="checkbox"
            id="is_income"
            checked={form.is_income}
            onChange={(e) => setForm((p) => ({ ...p, is_income: e.target.checked }))}
            style={{ accentColor: 'var(--color-primary)' }}
          />
          <label
            htmlFor="is_income"
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
              whiteSpace: 'nowrap',
            }}
          >
            Income
          </label>
        </div>
        <button
          type="submit"
          disabled={createCategory.isPending}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            background: 'var(--color-primary)',
            color: 'var(--color-primary-foreground)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: createCategory.isPending ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Add
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

      {/* Custom categories */}
      {customCats.length > 0 && (
        <div style={{ marginBottom: 'var(--space-5)' }}>
          <p
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              marginBottom: 'var(--space-2)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Custom
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {customCats.map((cat) => (
              <div
                key={cat.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'var(--color-bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                {cat.icon && (
                  <span style={{ fontSize: 'var(--font-size-lg)' }}>{cat.icon}</span>
                )}
                <div
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    background: cat.color || 'var(--color-border)',
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    flex: 1,
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--color-text-primary)',
                  }}
                >
                  {cat.name}
                </span>
                {cat.is_income && (
                  <span
                    style={{
                      fontSize: 'var(--font-size-xs)',
                      color: 'var(--color-success)',
                      background: 'var(--color-success-light)',
                      padding: '1px var(--space-2)',
                      borderRadius: 'var(--radius-full)',
                    }}
                  >
                    Income
                  </span>
                )}
                <button
                  onClick={() => deleteCategory.mutate(cat.id)}
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
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System categories (read-only) */}
      {isLoading ? (
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
          Loading...
        </p>
      ) : (
        <div>
          <p
            style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              marginBottom: 'var(--space-2)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            System (read-only)
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
            {systemCats.map((cat) => (
              <span
                key={cat.id}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 'var(--space-1)',
                  padding: 'var(--space-1) var(--space-2)',
                  background: 'var(--color-bg-elevated)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-full)',
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--color-text-secondary)',
                }}
              >
                {cat.icon && cat.icon} {cat.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
