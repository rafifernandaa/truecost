import type React from 'react';
import { History, ShieldCheck, ShieldAlert, CreditCard, CheckCircle2 } from 'lucide-react';

interface AuditTrailViewProps {
  transactions: any[];
  executedOrders?: any[];
  disposableCards: any[];
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({
  transactions,
  executedOrders: _executedOrders,
  disposableCards,
}) => {
  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-4 sm:p-6 space-y-5">
      <div className="flex items-center justify-between pb-3.5 border-b border-zinc-800/80">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-semibold text-sm sm:text-base text-zinc-100">Immutable Bank Audit Trail</h3>
            <p className="text-xs text-zinc-500 font-mono">Verifiable Non-Repudiable Ledger Logs</p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
          {transactions.length} Events Logged
        </span>
      </div>

      {/* Disposable Cards Strip */}
      {disposableCards.length > 0 && (
        <div className="space-y-2">
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
            <CreditCard className="w-3.5 h-3.5 text-zinc-400" />
            <span>Single-Use Disposable Virtual Cards</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {disposableCards.map((card, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-zinc-950/80 border border-zinc-800 flex items-center justify-between text-xs font-mono"
              >
                <div>
                  <div className="text-zinc-200 font-medium">{card.masked_pan}</div>
                  <div className="text-[10px] text-zinc-500 mt-0.5">
                    Limit: {card.currency} {card.spending_limit?.toLocaleString()}
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-zinc-900 text-zinc-400 border border-zinc-800">
                  {card.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transaction Stream */}
      <div className="space-y-2">
        <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
          Ledger Activity Stream
        </div>
        {transactions.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-zinc-600 bg-zinc-950/40 rounded-lg border border-zinc-850">
            No transactions executed yet. Create a signed mandate or simulate a buy to record ledger events.
          </div>
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {transactions.slice().reverse().map((tx, idx) => {
              const isSettlement = tx.type === 'PURCHASE_SETTLEMENT';
              const isReserve = tx.type === 'RESERVE_SINKING_POT';
              const isRejected = tx.status === 'REJECTED_BY_BANK_POLICY';

              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs transition ${
                    isRejected
                      ? 'bg-zinc-950/90 border-red-950 text-red-300'
                      : isSettlement
                      ? 'bg-zinc-950/90 border-zinc-700 text-zinc-200'
                      : 'bg-zinc-950/80 border-zinc-850 text-zinc-300'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    {isRejected ? (
                      <ShieldAlert className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    ) : isSettlement ? (
                      <CheckCircle2 className="w-4 h-4 text-zinc-200 flex-shrink-0 mt-0.5" />
                    ) : (
                      <ShieldCheck className="w-4 h-4 text-zinc-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="font-medium text-zinc-100">
                        {isSettlement
                          ? 'Settled Autonomous Purchase'
                          : isReserve
                          ? 'Sinking Pot Allocation'
                          : tx.type}
                      </div>
                      <div className="text-[11px] font-mono text-zinc-500 mt-0.5">
                        {tx.reason || (tx.amount ? `Amount: Rp ${tx.amount.toLocaleString()} ${tx.currency}` : '')}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-[10px] text-zinc-500 font-mono">
                    {new Date(tx.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
