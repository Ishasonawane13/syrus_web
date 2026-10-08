import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { api, MarketPrice } from '../api';

const SYMBOLS = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ITC', 'TATAMOTORS'];

export const MarketTicker: React.FC = () => {
  const [prices, setPrices] = useState<Record<string, MarketPrice>>({});
  const [loading, setLoading] = useState(true);

  const fetchAllPrices = async () => {
    try {
      const results: Record<string, MarketPrice> = {};
      await Promise.all(
        SYMBOLS.map(async (sym) => {
          try {
            const p = await api.getMarketPrice(sym);
            results[sym] = p;
          } catch {}
        })
      );
      setPrices(results);
      setLoading(false);
    } catch {}
  };

  useEffect(() => {
    fetchAllPrices();
    const interval = setInterval(fetchAllPrices, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full bg-[#0b0f19] border-y border-white/5 py-2 px-4 overflow-x-auto flex items-center gap-6 no-scrollbar text-xs">
      <div className="flex items-center gap-2 text-indigo-400 font-semibold uppercase tracking-wider pl-2 border-r border-white/10 pr-4 shrink-0">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        NSE Live
      </div>

      <div className="flex items-center gap-6 shrink-0">
        {SYMBOLS.map((sym) => {
          const item = prices[sym];
          if (!item) {
            return (
              <div key={sym} className="flex items-center gap-2 text-slate-500 font-mono">
                <span>{sym}</span>
                <span>---</span>
              </div>
            );
          }
          const isPos = item.change >= 0;
          return (
            <div
              key={sym}
              className="flex items-center gap-2 font-mono hover:bg-white/5 px-2 py-1 rounded transition-colors"
            >
              <span className="font-semibold text-slate-200">{sym}</span>
              <span className="text-slate-100">₹{item.price.toFixed(2)}</span>
              <span
                className={`flex items-center text-[11px] font-medium ${
                  isPos ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isPos ? <TrendingUp size={12} className="mr-0.5" /> : <TrendingDown size={12} className="mr-0.5" />}
                {isPos ? '+' : ''}
                {item.change_pct.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
