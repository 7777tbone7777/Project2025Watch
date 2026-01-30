const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://backend-production-d969.up.railway.app";

export interface Prediction {
  id: number;
  timeframe: string;
  prediction: string;
  result: string;
  news_match: string;
}

export interface PredictionList {
  predictions: Prediction[];
}

export interface ScoreResponse {
  predictions: Prediction[];
  message: string;
}

export interface ProgressItem {
  title: string;
  progress: number;
  last_updated: string;
}

export interface ProgressList {
  items: ProgressItem[];
}

export interface AlertStatus {
  triggered: boolean;
  reason: string;
}

export interface GeopoliticalArticle {
  title: string;
  date: string;
  summary: string;
  link: string;
  tags: string[];
}

export interface GeopoliticalFeed {
  articles: GeopoliticalArticle[];
}

export async function fetchPredictions(): Promise<PredictionList> {
  const res = await fetch(`${API_URL}/api/predictions`);
  if (!res.ok) throw new Error("Failed to fetch predictions");
  return res.json();
}

export async function scorePredictions(): Promise<ScoreResponse> {
  const res = await fetch(`${API_URL}/api/predictions/score`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to score predictions");
  return res.json();
}

export async function fetchProgress(): Promise<ProgressList> {
  const res = await fetch(`${API_URL}/api/progress`);
  if (!res.ok) throw new Error("Failed to fetch progress");
  return res.json();
}

export async function analyzeProgress(): Promise<ProgressList> {
  const res = await fetch(`${API_URL}/api/progress/analyze`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to analyze progress");
  return res.json();
}

export async function fetchAlerts(): Promise<AlertStatus> {
  const res = await fetch(`${API_URL}/api/alerts`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function fetchGeopolitical(): Promise<GeopoliticalFeed> {
  const res = await fetch(`${API_URL}/api/geopolitical`);
  if (!res.ok) throw new Error("Failed to fetch geopolitical feed");
  return res.json();
}

export function getReportUrl(): string {
  return `${API_URL}/api/report/pdf`;
}
