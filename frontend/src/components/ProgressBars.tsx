"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchProgress, analyzeProgress } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

export function ProgressBars() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["progress"],
    queryFn: fetchProgress,
  });

  const analyzeMutation = useMutation({
    mutationFn: analyzeProgress,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
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
          onClick={() => analyzeMutation.mutate()}
          disabled={analyzeMutation.isPending}
          size="sm"
        >
          {analyzeMutation.isPending ? "Analyzing..." : "Analyze Progress"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {analyzeMutation.isPending && (
          <p className="text-sm text-muted-foreground">
            Fetching news and analyzing with AI... This may take a moment.
          </p>
        )}
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
            {item.articles && item.articles.length > 0 && (
              <div className="text-xs space-y-0.5 mt-1">
                {item.articles.map((article, idx) => (
                  <a
                    key={idx}
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-blue-600 hover:underline truncate"
                    title={article.title}
                  >
                    → {article.title}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
