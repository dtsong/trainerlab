import { EmbedWidgetClient } from "@/components/embed/EmbedWidgetClient";

interface EmbedPageProps {
  params: Promise<{ id: string }>;
}

export default async function EmbedPage({ params }: EmbedPageProps) {
  const { id } = await params;
  return <EmbedWidgetClient widgetId={id} />;
}
