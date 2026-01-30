"use client";

import { Button } from "@/components/ui/button";
import { getReportUrl } from "@/lib/api";

export function ReportDownload() {
  return (
    <a href={getReportUrl()} download>
      <Button variant="outline">Download PDF Report</Button>
    </a>
  );
}
