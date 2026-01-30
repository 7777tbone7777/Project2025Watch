import { EmergencyAlert } from "@/components/EmergencyAlert";
import { ProgressBars } from "@/components/ProgressBars";
import { PredictionTable } from "@/components/PredictionTable";
import { GeopoliticalFeed } from "@/components/GeopoliticalFeed";
import { ReportDownload } from "@/components/ReportDownload";

// Dashboard for tracking Project 2025 predictions
export default function Home() {
  return (
    <main className="min-h-screen bg-background p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Project 2025 Tracker</h1>
          <ReportDownload />
        </header>

        <EmergencyAlert />

        <div className="grid gap-6 md:grid-cols-2">
          <ProgressBars />
          <GeopoliticalFeed />
        </div>

        <PredictionTable />
      </div>
    </main>
  );
}
