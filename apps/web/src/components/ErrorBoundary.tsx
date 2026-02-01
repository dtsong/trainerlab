"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  handleReport = () => {
    const errorMessage = this.state.error?.message || "Unknown error";
    const subject = encodeURIComponent("TrainerLab Error Report");
    const body = encodeURIComponent(
      `Error: ${errorMessage}\n\nPlease describe what you were doing when this error occurred:\n`,
    );
    window.open(`mailto:support@trainerlab.io?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center">
          <div className="mb-4 rounded-full bg-destructive/10 p-4">
            <AlertTriangle className="h-8 w-8 text-destructive" />
          </div>
          <h2 className="mb-2 text-xl font-semibold">Something went wrong</h2>
          <p className="mb-6 max-w-md text-muted-foreground">
            An unexpected error occurred. You can try refreshing the page or
            contact support if the problem persists.
          </p>
          {this.state.error?.message && (
            <p className="mb-6 max-w-md rounded bg-muted p-3 font-mono text-sm text-muted-foreground">
              {this.state.error.message}
            </p>
          )}
          <div className="flex gap-3">
            <Button onClick={this.handleRetry}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
            <Button variant="outline" onClick={this.handleReport}>
              Report Issue
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
