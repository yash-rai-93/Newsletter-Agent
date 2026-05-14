import { useState } from 'react'

const ORDERED = ['plan','research','summarize','write','review','improve','output']
const LABEL = {
  plan:     'Planning',
  research: 'Researching',
  summarize:'Summarizing',
  write:    'Writing',
  review:   'Self-Review',
  improve:  'Improving',
  output:   'Output',
}

export default function AgentSteps({ steps, running, mode }) {
  const [open, setOpen] = useState({})
  const completedSet = new Set(steps.map(s => s.step))
  const lastDone = steps.at(-1)?.step
  const pendingIdx = running ? (ORDERED.indexOf(lastDone) + 1) : -1
  const pendingStep = pendingIdx >= 0 ? ORDERED[pendingIdx] : null

  return (
    <div>
      <SectionHeader
        title="Agent Pipeline"
        right={running
          ? <Pill color="green">Running</Pill>
          : steps.length > 0
          ? <Pill color="muted">{steps.length} steps</Pill>
          : null}
      />

      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {steps.map((s, i) => (
          <StepRow
            key={s.step} step={s}
            open={!!open[s.step]}
            onToggle={() => setOpen(p => ({ ...p, [s.step]: !p[s.step] }))}
            isLast={i === steps.length - 1 && !running}
          />
        ))}

        {pendingStep && <PendingRow step={pendingStep} />}

        {running && ORDERED
          .slice(pendingIdx + 1)
          .filter(s => !completedSet.has(s) && s !== pendingStep)
          .slice(0, 3)
          .map(s => <QueuedRow key={s} step={s} />)}
      </div>

      {mode === 'hitl' && (
        <div style={{
          marginTop: 12, padding: '10px 14px', borderRadius: 7,
          border: '1px solid rgba(59,130,246,0.25)', background: 'rgba(59,130,246,0.05)',
          display: 'flex', gap: 10, alignItems: 'flex-start',
        }}>
          <span style={{ color: '#60a5fa', fontSize: 15, marginTop: 1 }}>ℹ</span>
          <div>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#93c5fd', marginBottom: 2 }}>Human-in-the-Loop active</div>
            <div style={{ fontSize: 12, color: 'rgba(147,197,253,0.5)' }}>Agent pauses after planning and drafting for your review.</div>
          </div>
        </div>
      )}
    </div>
  )
}

function StepRow({ step, open, onToggle, isLast }) {
  return (
    <div style={{
      borderRadius: 7, border: '1px solid var(--border)',
      background: 'var(--bg-subtle)', overflow: 'hidden',
    }} className="animate-fade-up">
      <button onClick={onToggle} style={{
        width: '100%', display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', background: 'none', border: 'none', cursor: 'pointer',
        textAlign: 'left',
      }}>
        <StatusDot status="done" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{step.label}</span>
            <StepBadge step={step} />
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1, fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            <StepSummary step={step} />
          </div>
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: 10, transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}>▼</span>
      </button>

      {open && step.data && (
        <div style={{ borderTop: '1px solid var(--border-soft)', padding: '12px 14px' }}>
          <StepDetails step={step} />
        </div>
      )}
    </div>
  )
}

function PendingRow({ step }) {
  return (
    <div style={{
      borderRadius: 7, border: '1px solid var(--border)',
      background: 'var(--bg-subtle)', padding: '10px 12px',
      display: 'flex', alignItems: 'center', gap: 10,
    }}>
      <StatusDot status="running" />
      <div>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{LABEL[step] || step}</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: 1 }}>running…</div>
      </div>
    </div>
  )
}

function QueuedRow({ step }) {
  return (
    <div style={{
      borderRadius: 7, border: '1px solid var(--border-soft)',
      padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10, opacity: 0.35,
    }}>
      <StatusDot status="queued" />
      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{LABEL[step] || step}</span>
    </div>
  )
}

function StatusDot({ status }) {
  const styles = {
    done:    { background: '#10b981', boxShadow: 'none' },
    running: { background: 'transparent', border: '2px solid #3b82f6', borderTopColor: 'transparent', animation: 'spin 0.75s linear infinite' },
    queued:  { background: 'var(--border)' },
  }
  return (
    <span style={{
      width: 8, height: 8, borderRadius: '50%', display: 'inline-block', flexShrink: 0,
      ...styles[status],
    }} className={status === 'running' ? 'animate-spin' : ''} />
  )
}

function StepBadge({ step }) {
  const d = step.data || {}
  if (step.step === 'review' && d.quality_score != null) {
    const color = d.quality_score >= 8 ? '#10b981' : d.quality_score >= 6 ? '#f59e0b' : '#ef4444'
    return <Tag color={color}>{d.quality_score}/10</Tag>
  }
  if ((step.step === 'research' || step.step === 'summarize') && d.article_count) {
    return <Tag color="#60a5fa">{d.article_count} articles</Tag>
  }
  return null
}

function Tag({ color, children }) {
  return (
    <span style={{
      fontSize: 11, fontFamily: 'var(--font-mono)', padding: '2px 7px',
      borderRadius: 4, color, background: color + '18', whiteSpace: 'nowrap',
    }}>{children}</span>
  )
}

function StepSummary({ step }) {
  const d = step.data || {}
  switch (step.step) {
    case 'plan':      return d.topic || 'Topic extracted'
    case 'research':  return `${d.article_count || 0} articles fetched`
    case 'summarize': return `${d.article_count || 0} articles summarized`
    case 'write':     return d.subject_line || 'Draft written'
    case 'review':    return d.improvement_needed ? 'Improvements queued' : 'Quality approved'
    case 'improve':   return `Iteration ${d.iteration || 1} complete`
    case 'output':    return d.output_path?.split('/').pop() || 'Newsletter saved'
    default:          return 'Completed'
  }
}

function StepDetails({ step }) {
  const d = step.data || {}
  switch (step.step) {
    case 'plan':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <KV k="Topic"    v={d.topic} />
          <KV k="Audience" v={d.audience} />
          {d.search_queries?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Search queries</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {d.search_queries.map((q, i) => (
                  <div key={i} style={{
                    fontSize: 12, fontFamily: 'var(--font-mono)', padding: '5px 10px',
                    background: 'var(--bg-raised)', borderRadius: 5, color: 'var(--text-secondary)',
                    display: 'flex', gap: 8, alignItems: 'flex-start',
                  }}>
                    <span style={{ color: 'var(--text-muted)' }}>{i+1}.</span>
                    <span>{q}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )
    case 'research':
      return (
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Articles found</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {(d.titles || []).map((t, i) => (
              <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '4px 0', display: 'flex', gap: 8 }}>
                <span style={{ color: 'var(--text-muted)', flexShrink: 0, fontFamily: 'var(--font-mono)' }}>{i+1}</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t}</span>
              </div>
            ))}
          </div>
        </div>
      )
    case 'summarize':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {(d.articles || []).map((a, i) => (
            <div key={i} style={{ padding: '10px 12px', background: 'var(--bg-raised)', borderRadius: 6, border: '1px solid var(--border-soft)' }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4, lineHeight: 1.4 }}>{a.title}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.55 }}>{a.summary}</div>
              {a.url && (
                <a href={a.url} target="_blank" rel="noopener noreferrer"
                   style={{ fontSize: 11, color: '#60a5fa', fontFamily: 'var(--font-mono)', marginTop: 6, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', opacity: 0.7 }}>
                  {a.url}
                </a>
              )}
            </div>
          ))}
        </div>
      )
    case 'write':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <KV k="Subject" v={d.subject_line} />
          <KV k="Preview" v={d.preview_text} />
          <KV k="Length"  v={d.draft_length ? `${d.draft_length.toLocaleString()} chars` : null} />
        </div>
      )
    case 'review':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              fontSize: 28, fontWeight: 700,
              color: d.quality_score >= 8 ? '#10b981' : d.quality_score >= 6 ? '#f59e0b' : '#ef4444',
            }}>{d.quality_score}/10</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {d.improvement_needed ? '↻ Will improve' : '✓ Approved'}
            </span>
          </div>
          {d.critique && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, padding: '10px 12px', background: 'var(--bg-raised)', borderRadius: 6, border: '1px solid var(--border-soft)' }}>
              {d.critique}
            </div>
          )}
        </div>
      )
    case 'output':
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <KV k="Subject"  v={d.subject_line} />
          <KV k="Quality"  v={d.quality_score ? `${d.quality_score}/10` : null} />
          <KV k="Articles" v={d.article_count} />
          <KV k="File"     v={d.output_path?.split('/').pop()} />
        </div>
      )
    default:
      return <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Step completed.</div>
  }
}

function KV({ k, v }) {
  if (!v) return null
  return (
    <div style={{ display: 'flex', gap: 10, fontSize: 12 }}>
      <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', minWidth: 60 }}>{k}</span>
      <span style={{ color: 'var(--text-secondary)', lineHeight: 1.5 }}>{v}</span>
    </div>
  )
}

function SectionHeader({ title, right }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{title}</span>
      {right}
    </div>
  )
}

function Pill({ color, children }) {
  const colors = {
    green: { color: '#10b981', background: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.25)' },
    muted: { color: 'var(--text-muted)', background: 'transparent', border: 'var(--border)' },
  }
  const c = colors[color] || colors.muted
  return (
    <span style={{
      fontSize: 11, fontFamily: 'var(--font-mono)', padding: '2px 8px',
      borderRadius: 20, color: c.color, background: c.background,
      border: `1px solid ${c.border}`,
      display: 'flex', alignItems: 'center', gap: 5,
    }}>
      {color === 'green' && <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} className="animate-pulse" />}
      {children}
    </span>
  )
}
