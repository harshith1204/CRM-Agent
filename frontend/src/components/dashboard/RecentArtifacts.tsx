import { useState, useEffect } from "react";
import { FileText, BarChart, Download, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { crmAPI } from "@/lib/api";

interface Artifact {
  id: string;
  filename: string;
  mime: string;
  size: number;
  download_url: string;
}

export function RecentArtifacts() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchArtifacts = async () => {
      try {
        const response = await crmAPI.listArtifacts();
        setArtifacts(response.artifacts.slice(0, 3)); // Show only recent 3
      } catch (error) {
        console.error('Failed to fetch artifacts:', error);
        // Use fallback data
        setArtifacts([
          {
            id: "1",
            filename: "Q2 Pipeline Analysis.xlsx",
            mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            size: 2400000,
            download_url: "/artifacts/1"
          },
          {
            id: "2",
            filename: "MTD Revenue Chart.png", 
            mime: "image/png",
            size: 128000,
            download_url: "/artifacts/2"
          },
          {
            id: "3",
            filename: "Lead Follow-up List.xlsx",
            mime: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            size: 1800000,
            download_url: "/artifacts/3"
          }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchArtifacts();
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileType = (mime: string): "excel" | "chart" => {
    if (mime.includes('spreadsheet') || mime.includes('excel')) return "excel";
    return "chart";
  };

  const handleDownload = (artifact: Artifact) => {
    window.open(crmAPI.getArtifactDownloadURL(artifact.id), '_blank');
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Recent Artifacts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Recent Artifacts
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {artifacts.map((artifact) => (
            <div 
              key={artifact.id}
              className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  {getFileType(artifact.mime) === "excel" ? (
                    <FileText className="h-5 w-5 text-emerald-600" />
                  ) : (
                    <BarChart className="h-5 w-5 text-blue-600" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm truncate">{artifact.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    System • Recent • {formatFileSize(artifact.size)}
                  </p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => handleDownload(artifact)}
              >
                <Download className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
