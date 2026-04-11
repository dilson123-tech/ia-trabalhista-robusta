import type { KeyboardEventHandler } from 'react'

type LoginPanelProps = {
  token: string
  loginFormKey: number
  username: string
  password: string
  showToken: boolean
  authLoading: boolean
  error: string
  loginFieldsUnlocked: boolean
  onGoToPanel: () => void
  onUsernameChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onUnlockFields: () => void
  onToggleShowToken: () => void
  onLogin: () => void
  onLoginKeyDown: KeyboardEventHandler<HTMLInputElement>
  onClear: () => void
}

export function LoginPanel({
  token,
  loginFormKey,
  username,
  password,
  showToken,
  authLoading,
  error,
  loginFieldsUnlocked,
  onGoToPanel,
  onUsernameChange,
  onPasswordChange,
  onUnlockFields,
  onToggleShowToken,
  onLogin,
  onLoginKeyDown,
  onClear,
}: LoginPanelProps) {
  return (
    <main className="app-shell">
      <section className="app-container">
        <section className="hero-panel">
          <div className="hero-card">
            <p className="hero-kicker">Plataforma Jurídica Multiárea</p>
            <h1 className="hero-heading">Acesso ao sistema</h1>
            <p className="hero-description">
              Entre com usuário e senha para acessar o painel do advogado, a carteira de casos
              e os fluxos executivos da plataforma.
            </p>

            <div className="hero-actions">
              <button
                className="btn btn-ghost"
                type="button"
                onClick={onGoToPanel}
              >
                Voltar ao painel
              </button>
            </div>
          </div>

          <aside className="technical-card" key={loginFormKey}>
            <div className="technical-topbar">
              <div>
                <h2 className="technical-title">Login oficial</h2>
                <p className="technical-description">
                  Entrada dedicada para autenticação do frontend, separada do hero principal
                  para deixar a experiência mais limpa e com cara de produto SaaS.
                </p>
              </div>

              <span className={`connection-badge ${token.trim() ? 'connection-badge--ok' : 'connection-badge--pending'}`}>
                {token.trim() ? 'Sessão pronta' : 'Sessão inativa'}
              </span>
            </div>

            <div className="form-grid token-field">
              <input
                className="login-decoy"
                type="text"
                tabIndex={-1}
                autoComplete="username"
                aria-hidden="true"
              />

              <input
                className="login-decoy"
                type="password"
                tabIndex={-1}
                autoComplete="current-password"
                aria-hidden="true"
              />

              <input
                className="form-control"
                value={username}
                onChange={(e) => onUsernameChange(e.target.value)}
                onFocus={onUnlockFields}
                readOnly={!loginFieldsUnlocked}
                placeholder="Usuário"
                autoComplete="off"
                autoCapitalize="none"
                spellCheck={false}
                name={`login-user-${loginFormKey}`}
                onKeyDown={onLoginKeyDown}
              />

              <div className="password-field">
                <input
                  className="form-control"
                  type={showToken ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => onPasswordChange(e.target.value)}
                  onFocus={onUnlockFields}
                  readOnly={!loginFieldsUnlocked}
                  placeholder="Senha"
                  autoComplete="new-password"
                  name={`login-password-${loginFormKey}`}
                  onKeyDown={onLoginKeyDown}
                />
                <button
                  className="password-toggle-icon"
                  type="button"
                  onClick={onToggleShowToken}
                  disabled={!password.trim()}
                  aria-label={showToken ? 'Ocultar senha' : 'Mostrar senha'}
                  title={showToken ? 'Ocultar senha' : 'Mostrar senha'}
                >
                  {showToken ? (
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M3 3l18 18" />
                      <path d="M10.58 10.58a2 2 0 1 0 2.84 2.84" />
                      <path d="M9.88 5.09A10.94 10.94 0 0 1 12 4c5 0 9.27 3.11 11 8-.9 2.54-2.66 4.61-4.94 5.94" />
                      <path d="M6.1 6.1C3.8 7.45 2.04 9.5 1 12c1.73 4.89 6 8 11 8 1.73 0 3.37-.37 4.84-1.03" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            <div className="actions-row">
              <button
                className={`btn ${authLoading || !username.trim() || !password.trim() ? 'btn-muted' : 'btn-primary'}`}
                type="button"
                onClick={onLogin}
                disabled={authLoading || !username.trim() || !password.trim()}
              >
                {authLoading ? 'Entrando...' : 'Entrar no sistema'}
              </button>

              <button
                className="btn btn-ghost"
                type="button"
                onClick={onClear}
              >
                Limpar
              </button>

              {token.trim() ? (
                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={onGoToPanel}
                >
                  Ir para o painel
                </button>
              ) : null}
            </div>

            {error ? (
              <p className="status-message status-message--error">{error}</p>
            ) : null}
          </aside>
        </section>
      </section>
    </main>
  )
}
