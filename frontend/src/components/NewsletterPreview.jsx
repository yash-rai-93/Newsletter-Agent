import { useState } from 'react'

export default function NewsletterPreview({ newsletter, running, stepCount }) {
  const [copied, setCopied] = useState(false)
  const [view, setView]     = useState('preview') // 'preview' | 'source'

  const copySubject = () => {
    if (!newsletter?.subject) return
    navigator.clipboard.writeText(newsletter.subject)
    setCopied(true)
    setTimeout(() => setCopied(false), 1800)
  }

  const downloadHTML = () => {
    if (!newsletter?.html) return
    const blob = new Blob([newsletter.html], { type: 'text/html' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'newsletter.html'
    a.click()
  }

  // ── Empty / loading state ────────────────────────────────────────────────
  if (!newsletter) {
    return (
      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>
          Newsletter Preview
        </div>
        <div style={{
          minHeight: 600, height: '75vh', borderRadius: 8, border: '1px solid var(--border)',
          background: 'var(--bg-subtle)', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 12,
        }}>
          {running ? (
            <>
              <div style={{ display: 'flex', gap: 5 }}>
                {[0,1,2].map(i => (
                  <span key={i} style={{
                    width: 6, height: 6, borderRadius: '50%', background: 'var(--border)',
                    animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                {stepCount < 4 ? 'Researching…' : stepCount < 5 ? 'Writing…' : 'Almost ready…'}
              </span>
            </>
          ) : (
            <>
              <span style={{ fontSize: 32 }}>📄</span>
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>Newsletter will appear here</span>
            </>
          )}
        </div>
      </div>
    )
  }

  // ── Newsletter ready ─────────────────────────────────────────────────────
  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Newsletter Preview
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* View toggle */}
          <div style={{ display: 'flex', border: '1px solid var(--border)', borderRadius: 6, overflow: 'hidden' }}>
            {['preview', 'source'].map(v => (
              <button key={v} onClick={() => setView(v)} style={{
                padding: '4px 10px', fontSize: 12, border: 'none', cursor: 'pointer', fontFamily: 'inherit',
                background: view === v ? 'var(--bg-raised)' : 'transparent',
                color: view === v ? 'var(--text-primary)' : 'var(--text-muted)',
              }}>{v === 'preview' ? 'Preview' : 'HTML'}</button>
            ))}
          </div>
          <ActionBtn onClick={downloadHTML} title="Download HTML">⬇ Download</ActionBtn>
        </div>
      </div>

      {/* Meta strip */}
      <div style={{
        padding: '10px 14px', borderRadius: '7px 7px 0 0',
        border: '1px solid var(--border)', borderBottom: 'none',
        background: 'var(--bg-raised)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Subject</div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.4 }}>{newsletter.subject}</div>
        </div>
        <div style={{ display: 'flex', gap: 10, flexShrink: 0 }}>
          {newsletter.quality != null && (
            <Stat label="Quality" value={`${newsletter.quality}/10`} color={newsletter.quality >= 8 ? '#10b981' : newsletter.quality >= 6 ? '#f59e0b' : '#ef4444'} />
          )}
          {newsletter.articleCount && <Stat label="Articles" value={newsletter.articleCount} />}
          <button onClick={copySubject} style={{
            padding: '4px 10px', borderRadius: 5, fontSize: 12,
            border: '1px solid var(--border)', background: 'transparent', cursor: 'pointer',
            color: copied ? '#10b981' : 'var(--text-secondary)', fontFamily: 'inherit',
            transition: 'color 0.15s',
          }}>
            {copied ? '✓ Copied' : 'Copy subject'}
          </button>
        </div>
      </div>

      {/* Content pane */}
      {view === 'preview' ? (
        <iframe
          srcDoc={newsletter.html}
          title="Newsletter preview"
          style={{
            width: '100%', height: '75vh', minHeight: 600, border: '1px solid var(--border)',
            borderRadius: '0 0 8px 8px', background: '#fff', display: 'block',
          }}
          sandbox="allow-same-origin"
        />
      ) : (
        <div style={{
          height: '75vh', minHeight: 600, border: '1px solid var(--border)', borderRadius: '0 0 8px 8px',
          background: 'var(--bg-subtle)', overflow: 'auto',
        }}>
          <pre style={{
            margin: 0, padding: '16px', fontSize: 11.5,
            fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)',
            whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.6,
          }}>
            {newsletter.html}
          </pre>
        </div>
      )}
    </div>
  )
}

function ActionBtn({ onClick, children, title }) {
  return (
    <button onClick={onClick} title={title} style={{
      padding: '4px 11px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
      border: '1px solid var(--border)', background: 'transparent',
      color: 'var(--text-secondary)', fontFamily: 'inherit',
      transition: 'all 0.12s',
    }}
    onMouseEnter={e => { e.target.style.color = 'var(--text-primary)'; e.target.style.borderColor = '#3b82f6' }}
    onMouseLeave={e => { e.target.style.color = 'var(--text-secondary)'; e.target.style.borderColor = 'var(--border)' }}
    >
      {children}
    </button>
  )
}

function Stat({ label, value, color }) {
  return (
    <div style={{ textAlign: 'right' }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600, color: color || 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{value}</div>
    </div>
  )
}
