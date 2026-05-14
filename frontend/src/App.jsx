import { useState, useRef, useCallback } from 'react'
import GoalInput from './components/GoalInput.jsx'
import AgentSteps from './components/AgentSteps.jsx'
import NewsletterPreview from './components/NewsletterPreview.jsx'
import HumanReview from './components/HumanReview.jsx'

const PRESETS = [
  { label: 'AI Agents',   goal: 'Create a weekly newsletter on the latest AI agent developments, frameworks, and research for ML engineers' },
  { label: 'LLMs',        goal: 'Create a weekly newsletter on large language model releases, benchmarks, and research papers' },
  { label: 'AI Startups', goal: 'Create a weekly newsletter on AI startup funding rounds, new product launches, and industry moves' },
  { label: 'AI Research', goal: 'Create a weekly newsletter on cutting-edge AI research, new papers, and academic breakthroughs' },
]

const STEP_ICONS = {
  plan:     '◈',
  research: '⊕',
  summarize:'◉',
  write:    '◎',
  review:   '◑',
  improve:  '↻',
  output:   '◆',
}

export default function App() {
  const [goal,    setGoal]    = useState('')
  const [mode,    setMode]    = useState('autonomous')
  const [running, setRunning] = useState(false)
  const [steps,   setSteps]   = useState([])
  const [newsletter, setNewsletter] = useState(null)
  const runIdRef = useRef(null)
  const [hitl,    setHitl]    = useState(null)
  const [tab,     setTab]     = useState('steps')
  const [error,   setError]   = useState(null)

  const addOrUpdateStep = (incoming) => {
    setSteps(prev => {
      const idx = prev.findIndex(s => s.step === incoming.step)
      if (idx >= 0) { const n = [...prev]; n[idx] = incoming; return n }
      return [...prev, incoming]
    })
  }

  const handleEvent = useCallback((ev) => {
    if (ev.type === 'run_started') {
      runIdRef.current = ev.run_id
    } else if (ev.type === 'step_complete') {
      addOrUpdateStep({
        step:   ev.step,
        label:  ev.label,
        icon:   STEP_ICONS[ev.step] || '◦',
        status: 'complete',
        data:   ev.data,
      })
      if (ev.step === 'output' && ev.data?.newsletter_html) {
        setNewsletter({
          html:         ev.data.newsletter_html,
          subject:      ev.data.subject_line,
          quality:      ev.data.quality_score,
          articleCount: ev.data.article_count,
          outputPath:   ev.data.output_path,
          plainText:    ev.data.plain_text,
        })
        setTab('preview')
      }
    } else if (ev.type === 'hitl_checkpoint') {
      setHitl({ step: ev.step, data: ev.data, runId: runIdRef.current })
    } else if (ev.type === 'error') {
      setError(ev.message)
      setRunning(false)
    } else if (ev.type === 'complete') {
      setRunning(false)
    }
  }, [])

  const consumeStream = async (res) => {
    const reader = res.body.getReader()
    const dec    = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += dec.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try { handleEvent(JSON.parse(line.slice(6))) } catch {}
      }
    }
  }

  const runAgent = async () => {
    if (!goal.trim() || running) return
    setRunning(true)
    setSteps([])
    setNewsletter(null)
    setError(null)
    setHitl(null)
    setTab('steps')
    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, mode }),
      })
      if (!res.ok) throw new Error(`Server error ${res.status} — is the backend running?`)
      await consumeStream(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const submitFeedback = async (approved, feedback) => {
    if (!hitl) return
    const saved = hitl
    setHitl(null)
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: saved.runId, checkpoint: saved.step, approved, feedback }),
      })
      await consumeStream(res)
    } catch (e) { setError(e.message) }
  }

  const hasContent = steps.length > 0 || running

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>
      <Header />

      <main style={{ flex: 1, maxWidth: 1200, width: '100%', margin: '0 auto', padding: '24px 20px' }}>

        {/* Goal input */}
        <GoalInput
          goal={goal} setGoal={setGoal}
          mode={mode} setMode={setMode}
          onRun={runAgent} running={running}
          presets={PRESETS}
        />

        {/* Error */}
        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

        {/* HITL modal */}
        {hitl && <HumanReview checkpoint={hitl} onSubmit={submitFeedback} />}

        {/* Content area */}
        {hasContent ? (
          <div style={{ marginTop: 24 }}>
            {/* Mobile tab bar */}
            <div className="lg:hidden" style={{ display: 'flex', marginBottom: 16, border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
              {['steps', 'preview'].map(t => (
                <button key={t} onClick={() => setTab(t)}
                  style={{
                    flex: 1, padding: '8px 0', fontSize: 13, fontWeight: 500,
                    background: tab === t ? 'var(--bg-raised)' : 'transparent',
                    color: tab === t ? 'var(--text-primary)' : 'var(--text-muted)',
                    border: 'none', cursor: 'pointer',
                  }}>
                  {t === 'steps' ? 'Agent Steps' : 'Newsletter'}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[350px_1fr] gap-5">
              <div className={tab !== 'steps' ? 'hidden lg:block' : ''} style={{ display: tab !== 'steps' ? undefined : 'block' }}>
                <AgentSteps steps={steps} running={running} mode={mode} />
              </div>
              <div className={tab !== 'preview' ? 'hidden lg:block' : ''} style={{ display: tab !== 'preview' ? undefined : 'block' }}>
                <NewsletterPreview newsletter={newsletter} running={running} stepCount={steps.length} />
              </div>
            </div>
          </div>
        ) : (
          <EmptyState />
        )}
      </main>
    </div>
  )
}

function Header() {
  return (
    <header style={{
      borderBottom: '1px solid var(--border)',
      background: 'var(--bg)',
      position: 'sticky', top: 0, zIndex: 50,
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 20px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 18 }}>📰</span>
          <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>Newsletter Agent</span>
          <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginLeft: 4, padding: '2px 7px', border: '1px solid var(--border)', borderRadius: 4 }}>v1.0</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          Gemini + LangGraph
        </div>
      </div>
    </header>
  )
}

function ErrorBanner({ message, onDismiss }) {
  return (
    <div style={{
      marginTop: 16, padding: '12px 16px', borderRadius: 8,
      border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)',
      display: 'flex', alignItems: 'flex-start', gap: 12,
    }} className="animate-fade-up">
      <span style={{ color: '#ef4444', fontSize: 15, marginTop: 1 }}>⚠</span>
      <div style={{ flex: 1 }}>
        <div style={{ color: '#fca5a5', fontSize: 13, fontWeight: 500, marginBottom: 2 }}>Error</div>
        <div style={{ color: 'rgba(252,165,165,0.7)', fontSize: 13 }}>{message}</div>
      </div>
      <button onClick={onDismiss} style={{ color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 16, lineHeight: 1 }}>×</button>
    </div>
  )
}

function EmptyState() {
  return (
    <div style={{ textAlign: 'center', marginTop: 64, padding: '0 20px' }}>
      <div style={{ fontSize: 40, marginBottom: 16 }}>📰</div>
      <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Autonomous Newsletter Generation</h2>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 440, margin: '0 auto', lineHeight: 1.6 }}>
        Describe the newsletter you want. The agent will research, write, self-critique, and output production-ready HTML — fully autonomously.
      </p>
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 8, marginTop: 32 }}>
        {['Multi-step reasoning', 'Web research', 'Self-critique loop', 'HTML output', 'Human-in-the-loop', 'LangGraph pipeline'].map(f => (
          <span key={f} style={{
            padding: '4px 12px', borderRadius: 20, fontSize: 12, fontFamily: 'var(--font-mono)',
            border: '1px solid var(--border)', color: 'var(--text-muted)',
          }}>{f}</span>
        ))}
      </div>
    </div>
  )
}
