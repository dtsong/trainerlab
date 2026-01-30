import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>TrainerLab</CardTitle>
          <CardDescription>
            Competitive intelligence platform for Pokemon TCG
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-muted-foreground">
            Your competitive research lab for Pokemon TCG. Meta analysis,
            Japanese format preview, and smart deck building.
          </p>
          <Button>Get Started</Button>
        </CardContent>
      </Card>
    </main>
  );
}
