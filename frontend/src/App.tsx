import React, { useState, useEffect } from 'react';
import {
  Bot,
  LayoutDashboard,
  ShieldCheck,
  ShoppingBag,
  RefreshCw,
} from 'lucide-react';
import { api, AccountSummary, Position } from './api';
import { MarketTicker } from './components/MarketTicker';
import { PortfolioSummary } from './components/PortfolioSummary';
import { PositionsTable } from './components/PositionsTable';
import { CopilotChat } from './components/CopilotChat';
import { AuditLogView } from './components/AuditLogView';
import { OrdersView } from './components/OrdersView';

const DEFAULT_ACCOUNT: AccountSummary = {
  id: 'demo-account',
  user_email: 'demo@tradingcopilot.ai',
  cash_balance: 807500.0,
  portfolio_value: 438250.0,
  total_value: 1245750.0,
  available_cash: 807500.0,
  realized_pnl: 12500.0,
  unrealized_pnl: 18250.0,
  daily_pnl: 8250.0,
  daily_pnl_pct: 0.82,
  total_pnl: 30750.0,
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'copilot' | 'portfolio' | 'orders' | 'audit'>('copilot');
  const [account, setAccount] = useState<AccountSummary>(DEFAULT_ACCOUNT);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [acc, pos] = await Promise.all([api.getAccount(), api.getPositions()]);
      if (acc) setAccount(acc);
      if (pos?.positions) setPositions(pos.positions);
      setLoading(false);
      setRefreshing(false);
    } catch (e) {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleManualRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#07090e] text-slate-100 font-sans">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 bg-[#090d16]/90 backdrop-blur-md border-b border-white/10 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Bot className="text-white" size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white font-heading">
                  AI Trading Copilot
                </h1>
                <span className="glow-pill indigo text-[10px] uppercase font-bold tracking-widest px-2 py-0.5">
                  Paper Trading
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Natural Language &bull; Deterministic Risk Guardrails &bull; Simulated Exchange
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center bg-white/5 border border-white/10 p-1 rounded-xl gap-1 text-xs">
            <button
              onClick={() => setActiveTab('copilot')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeTab === 'copilot'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <Bot size={14} />
              Copilot &amp; Trade
            </button>
            <button
              onClick={() => setActiveTab('portfolio')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeTab === 'portfolio'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <LayoutDashboard size={14} />
              Portfolio
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeTab === 'orders'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <ShoppingBag size={14} />
              Orders
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
                activeTab === 'audit'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              <ShieldCheck size={14} />
              Audit Trail
            </button>
          </nav>

          {/* Account Badge & Refresh */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex flex-col text-right font-mono text-xs">
              <span className="text-slate-400 text-[11px]">Available Cash</span>
              <span className="font-semibold text-emerald-400">
                ₹{account.available_cash.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </span>
            </div>

            <button
              onClick={handleManualRefresh}
              className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 border border-white/5 transition-all"
              title="Refresh Portfolio"
            >
              <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </header>

      {/* Live Market Bar */}
      <MarketTicker />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Top Metric Cards */}
        <PortfolioSummary account={account} loading={loading} />

        {/* Tab 1: AI Copilot & Live Desk */}
        {activeTab === 'copilot' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-7">
              <CopilotChat onTradeExecuted={loadData} />
            </div>
            <div className="lg:col-span-5 space-y-6">
              <PositionsTable positions={positions} loading={loading} />
              <div className="glass-panel p-4 text-xs text-slate-400 space-y-2">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5 text-sm">
                  <ShieldCheck size={16} className="text-indigo-400" />
                  Deterministic Safety Guarantees
                </div>
                <p>
                  &bull; AI intent validation: LLMs cannot directly write to database or execute orders.
                </p>
                <p>
                  &bull; 8 hardcoded deterministic risk checks (Cash, holdings, order values, position limits).
                </p>
                <p>
                  &bull; Explicit user confirmation required for every paper trade proposal.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Full Portfolio Holdings */}
        {activeTab === 'portfolio' && (
          <div className="space-y-6">
            <PositionsTable positions={positions} loading={loading} />
          </div>
        )}

        {/* Tab 3: Order History */}
        {activeTab === 'orders' && (
          <div className="space-y-6">
            <OrdersView />
          </div>
        )}

        {/* Tab 4: Audit Trail */}
        {activeTab === 'audit' && (
          <div className="space-y-6">
            <AuditLogView />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-4 px-6 text-center text-xs text-slate-500">
        AI Trading Copilot &bull; Paper Trading Demo Platform &bull; Zero Real-Money Risk
      </footer>
    </div>
  );
};
export default App;
