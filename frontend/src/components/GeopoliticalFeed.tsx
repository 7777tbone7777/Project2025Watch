"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchGeopolitical } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const tagColors: Record<string, string> = {
  "Federal Agency Capture": "bg-red-500",
  "Judicial Defiance": "bg-purple-500",
  "Suppression of Dissent": "bg-orange-500",
  "NATO Disengagement": "bg-blue-500",
  "Media Subversion": "bg-yellow-500",
};

export function GeopoliticalFeed() {
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["geopolitical"],
    queryFn: fetchGeopolitical,
  });

  if (isLoading) {
    return <div className="text-muted-foreground">Loading geopolitical feed...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error.message}</div>;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Geopolitical Updates</CardTitle>
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
        {data?.articles.map((article, idx) => (
          <div key={idx} className="border-b pb-4 last:border-0">
            <div className="flex items-start justify-between gap-2">
              <a
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium hover:underline"
              >
                {article.title}
              </a>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {article.date}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
              {article.summary}
            </p>
            {article.tags.length > 0 && (
              <div className="flex gap-1 mt-2">
                {article.tags.map((tag) => (
                  <Badge key={tag} className={tagColors[tag] || "bg-gray-500"}>
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
