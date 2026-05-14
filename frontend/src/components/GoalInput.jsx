import { useState } from 'react'

export default function GoalInput({ goal, setGoal, mode, setMode, onRun, running, presets }) {
  const [focused, setFocused] = useState(false)

  return (
    <div style={{
      border: `1px solid ${focused ? '#3b82f6' : 'var(--border)'}`,
      borderRadius: 10,
      background: 'var(--bg-subtle)',
      transition: 'border-color 0.15s',
      overflow: 'hidden',
    }}>
      {/* Textarea */}
      <textarea
        value={goal}
        onChange={e => setGoal(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') onRun() }}
        disabled={running}
        rows={3}
        placeholder='e.g. "Create a weekly newsletter on the latest AI agent news for ML engineers"'
        style={{
          width: '100%', display: 'block',
          background: 'transparent',
          border: 'none', outline: 'none', resize: 'none',
          padding: '14px 16px',
          color: 'var(--text-primary)',
          fontSize: 14,
          fontFamily: 'inherit',
          lineHeight: 1.6,
        }}
      />

      {/* Bottom bar */}
      <div style={{
        borderTop: '1px solid var(--border-soft)',
        padding: '10px 12px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
      }}>

        {/* Left: presets + mode */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {presets.map(p => (
            <button key={p.label} onClick={() => setGoal(p.goal)} disabled={running}
              style={{
                padding: '4px 10px', borderRadius: 5, fontSize: 12, cursor: 'pointer',
                border: '1px solid var(--border)',
                background: 'transparent',
                color: 'var(--text-secondary)',
                fontFamily: 'inherit',
                transition: 'all 0.12s',
              }}
              onMouseEnter={e => { e.target.style.borderColor = '#3b82f6'; e.target.style.color = 'var(--text-primary)' }}
              onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-secondary)' }}
            >
              {p.label}
            </button>
          ))}

          <div style={{ width: 1, height: 16, background: 'var(--border)', margin: '0 2px' }} />

          {/* Mode toggle */}
          <ModeToggle mode={mode} setMode={setMode} disabled={running} />
        </div>

        {/* Right: run button */}
        <button
          onClick={onRun}
          disabled={!goal.trim() || running}
          style={{
            padding: '7px 18px',
            borderRadius: 7,
            fontSize: 13,
            fontWeight: 500,
            fontFamily: 'inherit',
            cursor: !goal.trim() || running ? 'not-allowed' : 'pointer',
            background: !goal.trim() || running ? 'var(--bg-raised)' : '#3b82f6',
            color: !goal.trim() || running ? 'var(--text-muted)' : '#fff',
            border: 'none',
            display: 'flex', alignItems: 'center', gap: 7,
            transition: 'background 0.15s',
          }}
        >
          {running ? (
            <>
              <span className="animate-spin" style={{ width: 13, height: 13, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'var(--text-muted)', display: 'inline-block' }} />
              Running…
            </>
          ) : (
            <>
              <span>▶</span> Run Agent
            </>
          )}
        </button>
      </div>
    </div>
  )
}

function ModeToggle({ mode, setMode, disabled }) {
  const isAuto = mode === 'autonomous'
  return (
    <button
      onClick={() => !disabled && setMode(m => m === 'autonomous' ? 'hitl' : 'autonomous')}
      disabled={disabled}
      title={isAuto ? 'Fully autonomous — click to switch to Human-in-the-Loop' : 'Human-in-the-Loop — click to switch to Autonomous'}
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '4px 10px', borderRadius: 5,
        border: `1px solid ${isAuto ? 'rgba(16,185,129,0.4)' : 'rgba(59,130,246,0.4)'}`,
        background: isAuto ? 'rgba(16,185,129,0.07)' : 'rgba(59,130,246,0.07)',
        color: isAuto ? '#10b981' : '#60a5fa',
        fontSize: 12, fontFamily: 'var(--font-mono)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.15s', whiteSpace: 'nowrap',
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
      {isAuto ? 'Autonomous' : 'Human-in-Loop'}
    </button>
  )
}
