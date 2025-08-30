import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, Clock, Mail } from "lucide-react";

export default function ReportBuilder() {
  const savedReports = [
    {
      id: 1,
      name: "Weekly Pipeline Summary",
      description: "Deals by stage with weekly trends",
      lastRun: "2025-08-25",
      schedule: "Weekly (Monday 9:00 IST)",
      status: "active"
    },
    {
      id: 2,
      name: "MTD Revenue Analysis",
      description: "Revenue breakdown by source and owner",
      lastRun: "2025-08-20",
      schedule: "Monthly (1st, 9:00 IST)",
      status: "active"
    },
    {
      id: 3,
      name: "Lead Activity Report",
      description: "Leads with no activity in 14+ days",
      lastRun: "Never",
      schedule: "None",
      status: "draft"
    }
  ];

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
        {savedReports.map((report) => (
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
                  <Button variant="outline" size="sm">
                    <Play className="h-4 w-4 mr-2" />
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
                  Last run: {report.lastRun}
                </div>
                {report.schedule !== 'None' && (
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