/**
 * API client for AI Trading Copilot backend
 */

export interface AccountSummary {
  id: string;
  user_email: string;
  cash_balance: number;
  portfolio_value: number;
  total_value: number;
  available_cash: number;
  realized_pnl: number;
  unrealized_pnl: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  total_pnl: number;
}

export interface Position {
  symbol: string;
  name: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  allocation_pct: number;
}

export interface Instrument {
  symbol: string;
  name: string;
  exchange: string;
  lot_size: number;
  is_active: boolean;
}

export interface MarketPrice {
  symbol: string;
  name: string;
  price: number;
  bid: number;
  ask: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

export interface OrderProposalCard {
  id: string;
  symbol: string;
  name?: string;
  side: string;
  order_type: string;
  quantity: number;
  limit_price?: number;
  estimated_value: number;
  current_price: number;
  risk_status: string;
  risk_details?: {
    status: string;
    rules?: Array<{ rule_id: string; rule_name: string; status: string; message: string }>;
    reason?: string;
    rejected_by?: string;
  };
  warnings: string[];
  status: string;
  message: string;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  order_proposal?: OrderProposalCard | null;
  tool_calls: Array<{ tool: string; args: any; result: any }>;
}

export interface OrderItem {
  id: string;
  symbol: string;
  name?: string;
  side: string;
  order_type: string;
  quantity: number;
  limit_price?: number;
  estimated_value: number;
  status: string;
  risk_status?: string;
  risk_details?: any;
  created_at: string;
  updated_at?: string;
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  user_request: string;
  interpreted_intent?: any;
  tool_used?: string;
  tool_args?: any;
  tool_result?: any;
  order_id?: string;
  risk_result?: string;
  risk_details?: any;
  user_approved?: boolean | null;
  execution_result?: string;
}

const API_BASE = '';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) errorMsg = body.detail;
      else if (body.message) errorMsg = body.message;
    } catch {}
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  getHealth: () => fetchJson<{ status: string; version: string; database: string }>('/health'),
  getAccount: () => fetchJson<AccountSummary>('/account'),
  getPositions: () => fetchJson<{ positions: Position[] }>('/account/positions'),
  getInstruments: () => fetchJson<{ instruments: Instrument[] }>('/market/instruments'),
  getMarketPrice: (symbol: string) => fetchJson<MarketPrice>(`/market/${symbol}/price`),
  getOrders: () => fetchJson<{ orders: OrderItem[]; total: number }>('/orders'),
  executeOrder: (orderId: string) => fetchJson<any>(`/orders/${orderId}/execute`, { method: 'POST' }),
  cancelOrder: (orderId: string) => fetchJson<any>(`/orders/${orderId}/cancel`, { method: 'POST' }),
  sendChat: (message: string, conversationId?: string) =>
    fetchJson<ChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }),
  getAuditLogs: () => fetchJson<{ logs: AuditLogItem[]; total: number }>('/audit/logs'),
};
