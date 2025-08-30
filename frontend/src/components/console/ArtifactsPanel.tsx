import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Download, ExternalLink, FileSpreadsheet, BarChart3, Table as TableIcon } from "lucide-react";

interface Artifact {
  id: string;
  type: 'table' | 'chart' | 'excel';
  name: string;
  timestamp: Date;
  size?: string;
  rows?: number;
}

interface ArtifactsPanelProps {
  artifacts: Artifact[];
}

export function ArtifactsPanel({ artifacts }: ArtifactsPanelProps) {
  const [activeTab, setActiveTab] = useState("table");

  // Mock data for demonstration
  const mockTableData = [
    { id: 1, dealName: "Acme Renewal", owner: "Priya", stage: "Proposal", amount: 24000 },
    { id: 2, dealName: "Globex Expansion", owner: "Aryan", stage: "Qualified", amount: 85000 },
    { id: 3, dealName: "TechCorp Deal", owner: "Rahul", stage: "Negotiation", amount: 45000 },
  ];

  const getArtifactIcon = (type: Artifact['type']) => {
    switch (type) {
      case 'table':
        return <TableIcon className="h-4 w-4" />;
      case 'chart':
        return <BarChart3 className="h-4 w-4" />;
      case 'excel':
        return <FileSpreadsheet className="h-4 w-4" />;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Artifacts</h2>
        <p className="text-sm text-muted-foreground">Generated outputs and exports</p>
      </div>

      <div className="flex-1">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="px-4 pt-4">
            <TabsList className="grid w-full grid-cols-3 transition-smooth">
              <TabsTrigger value="table" className="flex items-center space-x-2 transition-smooth hover-scale">
                <TableIcon className="h-4 w-4" />
                <span>Table</span>
              </TabsTrigger>
              <TabsTrigger value="chart" className="flex items-center space-x-2 transition-smooth hover-scale">
                <BarChart3 className="h-4 w-4" />
                <span>Chart</span>
              </TabsTrigger>
              <TabsTrigger value="excel" className="flex items-center space-x-2 transition-smooth hover-scale">
                <FileSpreadsheet className="h-4 w-4" />
                <span>Excel</span>
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 px-4 pb-4">
            <TabsContent value="table" className="h-full mt-4">
              <div className="space-y-4 h-full flex flex-col">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">{mockTableData.length} rows</Badge>
                    <Badge variant="outline">3 columns</Badge>
                  </div>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open in Explorer
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Excel
                    </Button>
                  </div>
                </div>

                <div className="flex-1 border border-border rounded-lg overflow-hidden">
                  <div className="bg-muted px-3 py-2 border-b border-border">
                    <div className="grid grid-cols-4 gap-4 text-xs font-medium text-muted-foreground">
                      <span>Deal Name</span>
                      <span>Owner</span>
                      <span>Stage</span>
                      <span>Amount</span>
                    </div>
                  </div>
                  <ScrollArea className="h-full">
                    <div className="divide-y divide-border">
                      {mockTableData.map((row, index) => (
                        <div key={row.id} className="grid grid-cols-4 gap-4 px-3 py-2 text-sm animate-slide-up transition-smooth hover:bg-muted/50" style={{ animationDelay: `${index * 0.05}s` }}>
                          <span className="font-medium">{row.dealName}</span>
                          <span>{row.owner}</span>
                          <span>
                            <Badge variant="outline" className="text-xs">{row.stage}</Badge>
                          </span>
                          <span className="font-mono">₹{row.amount.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="chart" className="h-full mt-4">
              <div className="space-y-4 h-full flex flex-col">
                <div className="flex items-center justify-between">
                  <Badge variant="secondary">Bar Chart</Badge>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    PNG
                  </Button>
                </div>

                <div className="flex-1 border border-border rounded-lg bg-muted/50 flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                    <p className="text-sm">Chart will be generated here</p>
                    <p className="text-xs">Revenue by Stage - Q2 2025</p>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="excel" className="h-full mt-4">
              <div className="space-y-4 h-full flex flex-col">
                <div className="text-center text-muted-foreground py-8">
                  <FileSpreadsheet className="h-12 w-12 mx-auto mb-2" />
                  <p className="text-sm mb-4">Ready to export</p>
                  <Button>
                    <Download className="h-4 w-4 mr-2" />
                    Download Excel
                  </Button>
                </div>

                {artifacts.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Recent Exports</h3>
                    {artifacts.map((artifact) => (
                      <div key={artifact.id} className="flex items-center justify-between p-2 border border-border rounded">
                        <div className="flex items-center space-x-2">
                          {getArtifactIcon(artifact.type)}
                          <span className="text-sm">{artifact.name}</span>
                          {artifact.rows && (
                            <Badge variant="outline" className="text-xs">{artifact.rows} rows</Badge>
                          )}
                        </div>
                        <Button variant="ghost" size="sm">
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}