import { useState } from 'react'
import { getCases, type CaseItem } from './services/api'

function App() {
  const [token, setToken] = useState('')
  const [cases, setCases] = useState<CaseItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)

  async function handleLoadCases() {
    setLoading(true)
    setError('')

    try {
      const data = await getCases(token)
      setCases(data)
      setLoaded(true)
    } catch (err) {
      console.error(err)
      setError('Não foi possível carregar os casos. Verifique o token e o backend.')
      setLoaded(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#0b1020',
        color: '#f5f7fb',
        fontFamily: 'Arial, sans-serif',
        padding: '32px',
      }}
    >
      <section
        style={{
          maxWidth: '1100px',
          margin: '0 auto',
        }}
      >
        <header
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '32px',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <p style={{ margin: 0, color: '#9aa4bf', fontSize: '14px' }}>
              IA Trabalhista Robusta
            </p>
            <h1 style={{ margin: '8px 0 0', fontSize: '32px' }}>
              Painel do Advogado
            </h1>
          </div>

          <button
            style={{
              background: '#d4af37',
              color: '#111',
              border: 'none',
              borderRadius: '10px',
              padding: '14px 20px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
            type="button"
          >
            + Novo Caso
          </button>
        </header>

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
            marginBottom: '24px',
          }}
        >
          <h2 style={{ marginTop: 0 }}>Conectar com a API</h2>
          <p style={{ color: '#9aa4bf' }}>
            Cole abaixo o token Bearer obtido no backend para carregar os casos reais.
          </p>

          <textarea
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Cole aqui o token JWT"
            style={{
              width: '100%',
              minHeight: '110px',
              resize: 'vertical',
              borderRadius: '12px',
              border: '1px solid #24304f',
              background: '#0f172a',
              color: '#f5f7fb',
              padding: '14px',
              fontSize: '14px',
              boxSizing: 'border-box',
              marginBottom: '16px',
            }}
          />

          <button
            type="button"
            onClick={handleLoadCases}
            disabled={loading || !token.trim()}
            style={{
              background: loading || !token.trim() ? '#5b6478' : '#d4af37',
              color: '#111',
              border: 'none',
              borderRadius: '10px',
              padding: '14px 20px',
              fontWeight: 700,
              cursor: loading || !token.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Carregando casos...' : 'Carregar casos reais'}
          </button>

          {error ? (
            <p style={{ color: '#ff7b7b', marginTop: '14px' }}>{error}</p>
          ) : null}
        </section>

        <section
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            marginBottom: '32px',
          }}
        >
          {[
            ['Casos carregados', String(cases.length)],
            ['Backend', 'Online'],
            ['Modo', loaded ? 'Real' : 'Demo'],
            ['Token', token.trim() ? 'Informado' : 'Pendente'],
          ].map(([label, value]) => (
            <article
              key={label}
              style={{
                background: '#121a2f',
                border: '1px solid #1e2945',
                borderRadius: '16px',
                padding: '20px',
              }}
            >
              <p style={{ margin: 0, color: '#9aa4bf', fontSize: '14px' }}>{label}</p>
              <h2 style={{ margin: '10px 0 0', fontSize: '28px' }}>{value}</h2>
            </article>
          ))}
        </section>

        <section
          style={{
            background: '#121a2f',
            border: '1px solid #1e2945',
            borderRadius: '16px',
            padding: '24px',
          }}
        >
          <div style={{ marginBottom: '20px' }}>
            <h2 style={{ margin: 0, fontSize: '22px' }}>Casos do escritório</h2>
            <p style={{ margin: '8px 0 0', color: '#9aa4bf' }}>
              Lista vinda da API da IA Trabalhista Robusta.
            </p>
          </div>

          {!loaded ? (
            <p style={{ color: '#9aa4bf' }}>
              Informe o token e clique em “Carregar casos reais”.
            </p>
          ) : null}

          {loaded && !loading && cases.length === 0 && !error ? (
            <p style={{ color: '#9aa4bf' }}>Nenhum caso encontrado para este token.</p>
          ) : null}

          <div
            style={{
              display: 'grid',
              gap: '12px',
            }}
          >
            {cases.map((caso) => (
              <article
                key={caso.id}
                style={{
                  background: '#0f172a',
                  border: '1px solid #24304f',
                  borderRadius: '14px',
                  padding: '16px',
                }}
              >
                <strong style={{ display: 'block', marginBottom: '6px', fontSize: '18px' }}>
                  {caso.title}
                </strong>

                <p style={{ margin: '0 0 8px', color: '#9aa4bf' }}>
                  {caso.case_number}
                </p>

                <p style={{ margin: '0 0 12px', color: '#c7d0e0' }}>
                  {caso.description}
                </p>

                <div
                  style={{
                    display: 'flex',
                    gap: '10px',
                    flexWrap: 'wrap',
                    alignItems: 'center',
                  }}
                >
                  <span
                    style={{
                      display: 'inline-block',
                      background: '#1d2842',
                      color: '#d4af37',
                      borderRadius: '999px',
                      padding: '6px 10px',
                      fontSize: '12px',
                      fontWeight: 700,
                    }}
                  >
                    {caso.status}
                  </span>

                  <span style={{ color: '#9aa4bf', fontSize: '13px' }}>
                    ID do caso: {caso.id}
                  </span>

                  <span style={{ color: '#9aa4bf', fontSize: '13px' }}>
                    Tenant: {caso.tenant_id}
                  </span>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
