"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchProgress } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

export function ProgressBars() {
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["progress"],
    queryFn: fetchProgress,
  });

  if (isLoading) {
    return <div className="text-muted-foreground">Loading progress...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error.message}</div>;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Progress Toward Authoritarian Goals</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          {isFetching ? "Refreshing..." : "Refresh"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {data?.items.map((item) => (
          <div key={item.title} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="font-medium">{item.title}</span>
              <span className="text-muted-foreground">{item.progress}%</span>
            </div>
            <Progress
              value={item.progress}
              className={item.progress >= 75 ? "[&>div]:bg-red-500" : ""}
            />
            <p className="text-xs text-muted-foreground">
              Last updated: {item.last_updated}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
