import React from 'react';
import { ShieldAlert, RefreshCw, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleHardRefresh = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center h-full w-full p-8 bg-[#060709] text-[#e5e2e1] font-mono select-none">
          <div className="max-w-md w-full bg-[#0e0f16] border border-red-900/60 rounded-2xl p-6 shadow-2xl space-y-4 text-center">
            <div className="w-12 h-12 rounded-xl bg-red-950/70 border border-red-800/80 flex items-center justify-center mx-auto text-red-400">
              <ShieldAlert className="w-6 h-6" />
            </div>

            <div>
              <h2 className="text-sm font-bold text-[#f5dfc0] uppercase tracking-wider">
                {this.props.name || 'Component'} Runtime Recovered
              </h2>
              <p className="text-[11px] text-[#858585] mt-1">
                A localized runtime issue occurred. The system protected the surrounding workspace from crashing.
              </p>
            </div>

            {this.state.error && (
              <div className="p-3 bg-[#060709] border border-white/[0.06] rounded-lg text-left text-[10px] text-red-300 font-mono overflow-x-auto max-h-24">
                {this.state.error.message || String(this.state.error)}
              </div>
            )}

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-[#1c2e26] hover:bg-[#254236] text-[#9ed1c1] border border-[#2a4d3e] rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow"
              >
                <RotateCcw className="w-3.5 h-3.5" /> Re-initialize View
              </button>
              <button
                onClick={this.handleHardRefresh}
                className="px-4 py-2 bg-[#161822] hover:bg-[#202433] text-[#cfc5b9] border border-white/[0.08] rounded-xl text-xs font-bold transition flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
