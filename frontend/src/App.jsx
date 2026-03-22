import { useState, useEffect, useCallback, useRef } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function SignalBadge({ signal }) {
  const color = signal === 'BUY' ? '#22c55e' : signal === 'SELL' ? '#ef4444' : '#f59e0b'
  return (
    <span style={{
      background: color,
      color: '#fff',
      borderRadius: '4px',
      padding: '2px 8px',
      fontWeight: 700,
      fontSize: '0.8rem',
    }}>{signal}</span>
  )
}

function StocksTable({ stocks, loading, onTrade }) {
  if (loading) return <p className="loading">Loading stocks…</p>
  if (!stocks.length) return <p>No stock data available.</p>
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Close</th>
            <th>Pivot</th>
            <th>S1</th>
            <th>R1</th>
            <th>Signal</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((s) => (
            <tr key={s.ticker}>
              <td><strong>{s.ticker}</strong></td>
              <td>${s.ohlc.close.toFixed(2)}</td>
              <td>{s.pivot_points.pivot.toFixed(2)}</td>
              <td>{s.pivot_points.s1.toFixed(2)}</td>
              <td>{s.pivot_points.r1.toFixed(2)}</td>
              <td><SignalBadge signal={s.signal} /></td>
              <td>
                <button className="trade-btn" onClick={() => onTrade(s.ticker)}>
                  Trade
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TransactionsTable({ transactions, loading }) {
  if (loading) return <p className="loading">Loading transactions…</p>
  if (!transactions.length) return <p>No transactions yet.</p>
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Ticker</th>
            <th>Action</th>
            <th>Price</th>
            <th>Qty</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td><strong>{t.ticker}</strong></td>
              <td><SignalBadge signal={t.action} /></td>
              <td>${Number(t.price).toFixed(2)}</td>
              <td>{t.quantity}</td>
              <td>{new Date(t.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function TradeModal({ ticker, onClose, onConfirm }) {
  const [quantity, setQuantity] = useState(1)
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Trade {ticker}</h3>
        <label>
          Quantity
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
          />
        </label>
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={() => onConfirm(quantity)}>Execute</button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState('stocks')
  const [stocks, setStocks] = useState([])
  const [stocksLoading, setStocksLoading] = useState(false)
  const [transactions, setTransactions] = useState([])
  const [txLoading, setTxLoading] = useState(false)
  const [tradeTicker, setTradeTicker] = useState(null)
  const [toast, setToast] = useState(null)
  const toastTimerRef = useRef(null)

  const showToast = (msg, type = 'success') => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
    setToast({ msg, type })
    toastTimerRef.current = setTimeout(() => setToast(null), 4000)
  }

  useEffect(() => () => { if (toastTimerRef.current) clearTimeout(toastTimerRef.current) }, [])

  const fetchStocks = useCallback(async () => {
    setStocksLoading(true)
    try {
      const res = await fetch(`${API_BASE}/stocks`)
      const data = await res.json()
      setStocks(data.stocks || [])
    } catch {
      showToast('Failed to load stocks', 'error')
    } finally {
      setStocksLoading(false)
    }
  }, [])

  const fetchTransactions = useCallback(async () => {
    setTxLoading(true)
    try {
      const res = await fetch(`${API_BASE}/transactions`)
      const data = await res.json()
      setTransactions(data.transactions || [])
    } catch {
      showToast('Failed to load transactions', 'error')
    } finally {
      setTxLoading(false)
    }
  }, [])

  useEffect(() => { fetchStocks() }, [fetchStocks])
  useEffect(() => {
    if (tab === 'transactions') fetchTransactions()
  }, [tab, fetchTransactions])

  const executeTrade = async (quantity) => {
    const ticker = tradeTicker
    setTradeTicker(null)
    try {
      const res = await fetch(`${API_BASE}/trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, quantity }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Trade failed')
      showToast(data.message)
      if (tab === 'transactions') fetchTransactions()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  return (
    <div className="app">
      <header>
        <h1>📈 Traders</h1>
        <p className="subtitle">Pivot-point driven demo trading dashboard</p>
      </header>

      <nav>
        <button
          className={tab === 'stocks' ? 'active' : ''}
          onClick={() => setTab('stocks')}
        >Stocks</button>
        <button
          className={tab === 'transactions' ? 'active' : ''}
          onClick={() => setTab('transactions')}
        >Transactions</button>
      </nav>

      <main>
        {tab === 'stocks' && (
          <>
            <div className="section-header">
              <h2>Top 20 Stocks</h2>
              <button className="btn-secondary" onClick={fetchStocks}>↻ Refresh</button>
            </div>
            <StocksTable stocks={stocks} loading={stocksLoading} onTrade={setTradeTicker} />
          </>
        )}
        {tab === 'transactions' && (
          <>
            <div className="section-header">
              <h2>Transaction History</h2>
              <button className="btn-secondary" onClick={fetchTransactions}>↻ Refresh</button>
            </div>
            <TransactionsTable transactions={transactions} loading={txLoading} />
          </>
        )}
      </main>

      {tradeTicker && (
        <TradeModal
          ticker={tradeTicker}
          onClose={() => setTradeTicker(null)}
          onConfirm={executeTrade}
        />
      )}

      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.msg}</div>
      )}
    </div>
  )
}
