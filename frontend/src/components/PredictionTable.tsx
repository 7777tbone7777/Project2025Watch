"use client";

import { Fragment, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPredictions, scorePredictions, Prediction } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const statusColors: Record<string, string> = {
  Achieved: "bg-green-600",
  InProgress: "bg-yellow-500",
  Obstructed: "bg-blue-500",
  "Not Started": "bg-gray-500",
};

export function PredictionTable() {
  const queryClient = useQueryClient();
  const [scoredData, setScoredData] = useState<Prediction[] | null>(null);
  // Statuses are model judgements from news excerpts, so the evidence behind one
  // has to be reachable. Collapsed by default to keep the table scannable.
  const [expanded, setExpanded] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["predictions"],
    queryFn: fetchPredictions,
  });

  const scoreMutation = useMutation({
    mutationFn: scorePredictions,
    onSuccess: (response) => {
      setScoredData(response.predictions);
      queryClient.invalidateQueries({ queryKey: ["predictions"] });
    },
  });

  const predictions = scoredData || data?.predictions || [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Project 2025 Predictions</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">
            {predictions.length} proposals · click a row for the evidence behind its status
          </p>
        </div>
        <Button
          onClick={() => scoreMutation.mutate()}
          disabled={scoreMutation.isPending}
        >
          {scoreMutation.isPending ? "Scoring..." : "Re-score"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-muted-foreground">Loading predictions...</div>
        ) : error ? (
          <div className="text-red-500">Error: {error.message}</div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[110px]">Timeframe</TableHead>
                  <TableHead>Proposal</TableHead>
                  <TableHead className="w-[180px]">Agency</TableHead>
                  <TableHead className="w-[110px]">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {predictions.map((pred) => (
                  // Fragment carries the key: React needs it on the outermost
                  // element of a list item, not on the rows inside.
                  <Fragment key={pred.id}>
                    <TableRow
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() =>
                        setExpanded(expanded === pred.id ? null : pred.id)
                      }
                    >
                      <TableCell className="whitespace-nowrap text-xs">
                        {pred.timeframe}
                      </TableCell>
                      <TableCell>{pred.prediction}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {pred.agency || "—"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={statusColors[pred.result] || "bg-gray-500"}
                        >
                          {pred.result}
                        </Badge>
                      </TableCell>
                    </TableRow>

                    {expanded === pred.id && (
                      <TableRow>
                        <TableCell colSpan={4} className="bg-muted/30 text-sm">
                          <div className="space-y-3 py-2">
                            {pred.reasoning && (
                              <div>
                                <span className="font-semibold">
                                  Why this status:{" "}
                                </span>
                                <span className="text-muted-foreground">
                                  {pred.reasoning}
                                </span>
                              </div>
                            )}

                            {pred.source && (
                              <div>
                                <span className="font-semibold">
                                  Proposal source:{" "}
                                </span>
                                <span className="text-muted-foreground">
                                  {pred.source}
                                </span>
                              </div>
                            )}

                            {pred.articles && pred.articles.length > 0 && (
                              <div>
                                <span className="font-semibold">
                                  Articles this was scored against:
                                </span>
                                <ul className="list-disc list-inside mt-1 space-y-1">
                                  {pred.articles.map((a, i) => (
                                    <li key={i}>
                                      <a
                                        href={a.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-blue-500 hover:underline"
                                      >
                                        {a.title}
                                      </a>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {!pred.reasoning && !pred.articles?.length && (
                              <div className="text-muted-foreground">
                                Not scored yet — press Re-score.
                              </div>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </Fragment>
                ))}
              </TableBody>
            </Table>

            <p className="text-xs text-muted-foreground mt-4">
              Statuses are assigned by an AI model reading recent news excerpts,
              not verified fact. Check the linked articles before relying on one.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
