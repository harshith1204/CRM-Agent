
import { FileText, BarChart, Download, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const artifacts = [
  {
    id: "1",
    name: "Q2 Pipeline Analysis",
    type: "excel",
    owner: "Priya Sharma",
    timestamp: "2 hours ago",
    size: "2.3 MB"
  },
  {
    id: "2", 
    name: "MTD Revenue by Source",
    type: "chart",
    owner: "Aryan Patel",
    timestamp: "4 hours ago",
    size: "128 KB"
  },
  {
    id: "3",
    name: "Lead Follow-up List",
    type: "excel", 
    owner: "You",
    timestamp: "Yesterday",
    size: "1.8 MB"
  }
];

export function RecentArtifacts() {
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
                  {artifact.type === "excel" ? (
                    <FileText className="h-5 w-5 text-emerald-600" />
                  ) : (
                    <BarChart className="h-5 w-5 text-blue-600" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm truncate">{artifact.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {artifact.owner} • {artifact.timestamp} • {artifact.size}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="icon">
                <Download className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
