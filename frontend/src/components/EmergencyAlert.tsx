"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAlerts } from "@/lib/api";

export function EmergencyAlert() {
  const { data } = useQuery({
    queryKey: ["alerts"],
    queryFn: fetchAlerts,
  });

  if (!data?.triggered) return null;

  return (
    <div className="bg-red-600 text-white p-4 rounded-lg mb-6 animate-pulse">
      <div className="flex items-center gap-2">
        <span className="text-2xl">🚨</span>
        <div>
          <h3 className="font-bold text-lg">EMERGENCY ALERT</h3>
          <p>{data.reason}</p>
        </div>
      </div>
    </div>
  );
}
