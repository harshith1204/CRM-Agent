import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, Clock, Mail, Loader2 } from "lucide-react";
import { crmAPI, type SavedReport } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function ReportBuilder() {
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningReports, setRunningReports] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await crmAPI.listReports();
      setReports(response.reports);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      toast({
        title: "Error",
        description: "Failed to fetch reports. Using sample data.",
        variant: "destructive",
      });
      // Use fallback data
      setReports([
        {
          id: "1",
          name: "Weekly Pipeline Summary",
          description: "Deals by stage with weekly trends",
          spec: {} as any,
          schedule: "Weekly (Monday 9:00 IST)",
          status: "active",
          created_by: "system",
          last_run: "2025-08-25"
        },
        {
          id: "2",
          name: "MTD Revenue Analysis",
          description: "Revenue breakdown by source and owner",
          spec: {} as any,
          schedule: "Monthly (1st, 9:00 IST)",
          status: "active",
          created_by: "system",
          last_run: "2025-08-20"
        },
        {
          id: "3",
          name: "Lead Activity Report",
          description: "Leads with no activity in 14+ days",
          spec: {} as any,
          schedule: "None",
          status: "draft",
          created_by: "system",
          last_run: "Never"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRunReport = async (reportId: string) => {
    setRunningReports(prev => new Set(prev).add(reportId));
    try {
      const response = await crmAPI.runReport(reportId);
      window.open(crmAPI.getArtifactDownloadURL(response.artifact_id), '_blank');
      toast({
        title: "Report Generated",
        description: "Your report has been generated and is ready for download.",
      });
      // Refresh reports to update last_run time
      fetchReports();
    } catch (error) {
      console.error('Failed to run report:', error);
      toast({
        title: "Report Failed",
        description: "Failed to generate report. Please try again.",
        variant: "destructive",
      });
    } finally {
      setRunningReports(prev => {
        const newSet = new Set(prev);
        newSet.delete(reportId);
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-8">
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Report Builder</h1>
          <p className="text-muted-foreground">Create and schedule automated reports</p>
        </div>
        <Button>Create New Report</Button>
      </div>

      <div className="grid gap-4">
        {reports.map((report) => (
          <Card key={report.id}>
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {report.name}
                    <Badge variant={report.status === 'active' ? 'default' : 'secondary'}>
                      {report.status}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{report.description}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => report.id && handleRunReport(report.id)}
                    disabled={!report.id || runningReports.has(report.id)}
                  >
                    {report.id && runningReports.has(report.id) ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    Run Now
                  </Button>
                  <Button variant="ghost" size="sm">
                    Edit
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="flex items-center gap-6 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Last run: {report.last_run || "Never"}
                </div>
                {report.schedule && report.schedule !== 'None' && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    {report.schedule}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}