import { WidgetBuilder } from "@/components/creator";

interface EditWidgetPageProps {
  params: Promise<{ id: string }>;
}

export default async function EditWidgetPage({ params }: EditWidgetPageProps) {
  const { id } = await params;
  return <WidgetBuilder mode="edit" widgetId={id} />;
}
