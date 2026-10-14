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
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <History className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="font-bold text-base text-white">Immutable Bank Execution Trail</h3>
            <p className="text-xs text-slate-400">Verifiable Non-Repudiable Ledger Logs</p>
          </div>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          {transactions.length} Events Logged
        </span>
      </div>

      {/* Disposable Cards Strip */}
      {disposableCards.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <CreditCard className="w-3.5 h-3.5 text-indigo-400" />
            Active / Consumed Single-Use Tokens
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {disposableCards.map((card, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs font-mono"
              >
                <div>
                  <div className="text-slate-300 font-semibold">{card.masked_pan}</div>
                  <div className="text-[10px] text-slate-500">Cap: {card.currency} {card.spending_limit?.toLocaleString()}</div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-400 border border-slate-700">
                  {card.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transaction Stream */}
      <div className="space-y-2.5">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Ledger Activity
        </div>
        {transactions.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 bg-slate-950/30 rounded-xl border border-slate-800/50">
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
                  className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs transition ${
                    isRejected
                      ? 'bg-red-950/20 border-red-900/40 text-red-300'
                      : isSettlement
                      ? 'bg-emerald-950/20 border-emerald-900/40 text-emerald-300'
                      : 'bg-slate-950/40 border-slate-800 text-slate-300'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    {isRejected ? (
                      <ShieldAlert className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    ) : isSettlement ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                    ) : (
                      <ShieldCheck className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <div className="font-semibold text-white">
                        {isSettlement
                          ? 'Settled Autonomous Purchase'
                          : isReserve
                          ? 'Sinking Pot Allocation'
                          : tx.type}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {tx.reason || (tx.amount ? `Amount: Rp ${tx.amount.toLocaleString()} ${tx.currency}` : '')}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-[10px] text-slate-500 font-mono">
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
