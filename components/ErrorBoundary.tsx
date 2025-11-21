import React from 'react';

interface State { hasError: boolean; error?: any }

export default class ErrorBoundary extends React.Component<{children: React.ReactNode}, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(error: any) { return { hasError: true, error }; }
  componentDidCatch(error: any, info: any) { console.error('[ErrorBoundary]', error, info); }
  render() {
    if (this.state.hasError) {
      return <div className="flex items-center justify-center h-full text-red-400 font-mono text-sm">UI FAILURE // {String(this.state.error)} <button onClick={()=>this.setState({hasError:false,error:null})} className="ml-3 px-2 py-1 border border-red-500/40 rounded">Retry</button></div>;
    }
    return this.props.children;
  }
}
