import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Home, RefreshCw, LifeBuoy, Bot } from 'lucide-react';

export const ServerErrorPage: React.FC<{ error?: Error; resetErrorBoundary?: () => void }> = ({
  error,
  resetErrorBoundary,
}) => {
  const handleOpenAssistant = () => {
    const launcher = document.querySelector('button[aria-label="Open AI Assistant"]') as HTMLButtonElement | null;
    if (launcher) {
      launcher.click();
    }
  };

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="h-20 w-20 rounded-3xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-6 shadow-xl shadow-rose-500/10">
        <AlertTriangle className="h-10 w-10 animate-pulse" />
      </div>

      <div className="text-xs uppercase font-bold tracking-widest text-rose-400 mb-2">
        Error 500 — Internal Service Exception
      </div>
      <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-3">
        Unexpected System Interruption
      </h1>
      <p className="text-slate-400 text-sm max-w-md mx-auto mb-8">
        An unexpected condition was reported. Our automated monitoring has recorded this event with a correlation ID.
      </p>

      {/* Recovery Actions */}
      <div className="flex flex-wrap items-center justify-center gap-3">
        {resetErrorBoundary ? (
          <button
            onClick={resetErrorBoundary}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Retry Operation</span>
          </button>
        ) : (
          <Link
            to="/dashboard"
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Home className="h-4 w-4" />
            <span>Return to Dashboard</span>
          </Link>
        )}

        <Link
          to="/support"
          className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
        >
          <LifeBuoy className="h-4 w-4" />
          <span>Submit Support Ticket</span>
        </Link>

        <button
          onClick={handleOpenAssistant}
          className="px-4 py-2.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
        >
          <Bot className="h-4 w-4" />
          <span>Ask the Assistant</span>
        </button>
      </div>
    </div>
  );
};
