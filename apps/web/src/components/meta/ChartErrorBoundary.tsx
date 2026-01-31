"use client";

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  chartName?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ChartErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const chartName = this.props.chartName || "Unknown";

    console.error(`[ChartErrorBoundary] Chart "${chartName}" crashed:`, {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });

    // TODO: When Sentry is added, capture this error:
    // Sentry.captureException(error, {
    //   tags: { component: "ChartErrorBoundary", chartName },
    //   extra: { componentStack: errorInfo.componentStack },
    // });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const chartName = this.props.chartName || "Chart";

      return (
        <div className="flex h-[350px] flex-col items-center justify-center rounded-lg border border-dashed">
          <div className="text-center">
            <p className="text-sm font-medium text-muted-foreground">
              {chartName} failed to load
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Please try refreshing the page
            </p>
            <button
              onClick={this.handleRetry}
              className="mt-3 text-xs text-primary hover:underline"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
