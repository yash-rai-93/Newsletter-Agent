import { useState } from 'react'

export default function HumanReview({ checkpoint, onSubmit }) {
  const [feedback, setFeedback] = useState('')
  const d = checkpoint.data || {}

  const approve = () => onSubmit(true, feedback || null)
  const reject  = () => onSubmit(false, feedback || null)

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20, backdropFilter: 'blur(2px)',
    }}>
      <div style={{
        background: 'var(--bg-subtle)', border: '1px solid var(--border)',
        borderRadius: 12, width: '100%', maxWidth: 560, maxHeight: '90vh',
        overflow: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
      }}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 16 }}>👥</span>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>Human Review Required</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: 1 }}>
              Checkpoint: <span style={{ color: '#60a5fa' }}>{checkpoint.step}</span>
            </div>
          </div>
        </div>

        <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Content preview */}
          {checkpoint.step === 'plan' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Field label="Topic"    value={d.topic} />
              <Field label="Audience" value={d.audience} />
              {d.search_queries?.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Search queries</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {d.search_queries.map((q, i) => (
                      <div key={i} style={{ fontSize: 12, fontFamily: 'var(--font-mono)', padding: '6px 10px', background: 'var(--bg-raised)', borderRadius: 5, color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
                        <span style={{ color: 'var(--text-muted)' }}>{i+1}.</span>{q}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {d.plan && (
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Plan</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-raised)', borderRadius: 5, padding: '10px 12px', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{d.plan}</div>
                </div>
              )}
            </div>
          )}

          {checkpoint.step === 'write' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Field label="Subject" value={d.subject_line} />
              {d.newsletter_draft && (
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>Draft preview</div>
                  <div style={{
                    fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-raised)',
                    borderRadius: 5, padding: '10px 12px', maxHeight: 200, overflow: 'auto',
                    lineHeight: 1.6, whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)',
                  }}>
                    {d.newsletter_draft.slice(0, 800)}{d.newsletter_draft.length > 800 ? '\n…' : ''}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Feedback input */}
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
              Optional feedback <span style={{ color: 'var(--text-muted)' }}>(leave blank to approve as-is)</span>
            </label>
            <textarea
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              rows={3}
              placeholder="e.g. Focus more on open-source tools, remove the enterprise section..."
              style={{
                width: '100%', padding: '9px 12px', borderRadius: 6,
                border: '1px solid var(--border)', background: 'var(--bg-raised)',
                color: 'var(--text-primary)', fontSize: 13, fontFamily: 'inherit',
                lineHeight: 1.5, resize: 'vertical', outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = '#3b82f6'}
              onBlur={e => e.target.style.borderColor = 'var(--border)'}
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button onClick={reject} style={{
              padding: '8px 18px', borderRadius: 6, fontSize: 13, cursor: 'pointer',
              border: '1px solid var(--border)', background: 'transparent',
              color: 'var(--text-secondary)', fontFamily: 'inherit',
            }}>
              ✕ Reject
            </button>
            <button onClick={approve} style={{
              padding: '8px 18px', borderRadius: 6, fontSize: 13, fontWeight: 500,
              cursor: 'pointer', border: 'none', background: '#3b82f6',
              color: '#fff', fontFamily: 'inherit',
            }}>
              ✓ Approve & Continue
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Field({ label, value }) {
  if (!value) return null
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>{value}</div>
    </div>
  )
}
