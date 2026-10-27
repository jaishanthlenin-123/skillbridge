import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, MessageSquare } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    console.error('ErrorBoundary caught an unhandled rendering error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  private handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  private handleOpenChat = () => {
    window.dispatchEvent(
      new CustomEvent('skillbridge:open-chat', {
        detail: { prompt: 'I encountered an interface rendering error. Please help.' },
      })
    );
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[500px] flex items-center justify-center p-6">
          <div className="glass-panel max-w-lg w-full p-8 rounded-2xl border border-rose-500/30 text-center space-y-5 shadow-2xl">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-rose-500/10 text-rose-400 flex items-center justify-center border border-rose-500/20">
              <AlertTriangle className="h-7 w-7" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-white tracking-tight">Something went wrong</h2>
              <p className="text-xs text-slate-300 leading-relaxed">
                An unexpected display error occurred while rendering this view. Your saved data, uploaded resumes, and matches remain secure.
              </p>
              {this.state.error?.message && (
                <div className="mt-3 p-3 rounded-lg bg-slate-900 border border-slate-800 text-left font-mono text-[11px] text-rose-300 overflow-x-auto max-h-24">
                  {this.state.error.message}
                </div>
              )}
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/20"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Reload Page</span>
              </button>
              <button
                onClick={this.handleGoHome}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Home className="h-3.5 w-3.5" />
                <span>Return to Dashboard</span>
              </button>
              <button
                onClick={this.handleOpenChat}
                className="px-4 py-2 bg-slate-850 hover:bg-slate-800 text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>Report Issue</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
