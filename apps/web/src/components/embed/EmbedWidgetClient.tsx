"use client";

import { useEffect, useRef } from "react";

import { useWidgetData } from "@/hooks/useWidgets";

interface EmbedWidgetClientProps {
  widgetId: string;
}

export function EmbedWidgetClient({ widgetId }: EmbedWidgetClientProps) {
  const { data, isLoading, error } = useWidgetData(widgetId);
  const containerRef = useRef<HTMLDivElement>(null);

  // Apply theme class to body
  useEffect(() => {
    if (data?.theme) {
      document.body.classList.remove("light", "dark");
      document.body.classList.add(data.theme);
    }
  }, [data?.theme]);

  // Post height to parent for iframe auto-resize
  useEffect(() => {
    const sendHeight = () => {
      if (containerRef.current) {
        const height = containerRef.current.scrollHeight;
        window.parent.postMessage(
          { type: "trainerlab-widget-resize", widgetId, height },
          "*"
        );
      }
    };

    sendHeight();
    const observer = new ResizeObserver(sendHeight);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [widgetId, data]);

  if (isLoading) {
    return (
      <div className="flex min-h-[100px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-teal-500" />
      </div>
    );
  }

  if (error || data?.error) {
    return (
      <div className="flex min-h-[100px] items-center justify-center p-4 text-center text-sm text-red-500">
        Failed to load widget
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const accentStyle = data.accent_color
    ? ({ "--widget-accent": data.accent_color } as React.CSSProperties)
    : undefined;

  return (
    <div ref={containerRef} style={accentStyle}>
      <div className="p-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.type} widget
          </p>
        </div>
      </div>

      {data.show_attribution && (
        <div className="px-4 pb-2 text-center">
          <a
            href="https://trainerlab.io"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            Powered by TrainerLab
          </a>
        </div>
      )}
    </div>
  );
}
