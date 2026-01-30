"use client";

import { useState } from "react";
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
  Achieved: "bg-green-500",
  InProgress: "bg-yellow-500",
  Obstructed: "bg-blue-500",
  "Not Started": "bg-gray-500",
};

export function PredictionTable() {
  const queryClient = useQueryClient();
  const [scoredData, setScoredData] = useState<Prediction[] | null>(null);

  const { data, isLoading } = useQuery({
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
        <CardTitle>Project 2025 Predictions</CardTitle>
        <Button
          onClick={() => scoreMutation.mutate()}
          disabled={scoreMutation.isPending}
        >
          {scoreMutation.isPending ? "Scoring..." : "Score Predictions"}
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-muted-foreground">Loading predictions...</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timeframe</TableHead>
                <TableHead>Prediction</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {predictions.map((pred) => (
                <TableRow key={pred.id}>
                  <TableCell className="whitespace-nowrap">
                    {pred.timeframe}
                  </TableCell>
                  <TableCell>{pred.prediction}</TableCell>
                  <TableCell>
                    <Badge className={statusColors[pred.result] || "bg-gray-500"}>
                      {pred.result}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
