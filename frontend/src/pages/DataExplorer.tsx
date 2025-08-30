import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Download, Filter, Search, Loader2 } from "lucide-react";
import { crmAPI, type DataExplorerResponse } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function DataExplorer() {
  const [searchTerm, setSearchTerm] = useState("");
  const [collection, setCollection] = useState("leads");
  const [ownerFilter, setOwnerFilter] = useState("all-owners");
  const [stageFilter, setStageFilter] = useState("all-stages");
  const [data, setData] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, [collection, ownerFilter, stageFilter, searchTerm]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const filters: any = {};
      if (ownerFilter !== "all-owners") filters.owner = ownerFilter;
      if (stageFilter !== "all-stages") filters.status = stageFilter;

      const response = await crmAPI.exploreData({
        collection,
        filters,
        search: searchTerm || undefined,
        page: 1,
        limit: 50
      });

      setData(response.data);
      setTotalCount(response.total_count);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast({
        title: "Error",
        description: "Failed to fetch data. Using sample data.",
        variant: "destructive",
      });
      // Use fallback data
      setData([
        { _id: "1", name: "Acme Renewal", owner: "Priya", status: "Proposal", amount: 24000, created_date: "2025-06-14" },
        { _id: "2", name: "Globex Expansion", owner: "Aryan", status: "Qualified", amount: 85000, created_date: "2025-07-05" },
        { _id: "3", name: "TechCorp Integration", owner: "Sneha", status: "Discovery", amount: 45000, created_date: "2025-08-01" },
      ]);
      setTotalCount(3);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'excel') => {
    setExporting(true);
    try {
      const response = await crmAPI.exportData(collection, format);
      window.open(crmAPI.getArtifactDownloadURL(response.artifact_id), '_blank');
      toast({
        title: "Export Started",
        description: `Your ${format.toUpperCase()} export is ready for download.`,
      });
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: "Export Failed",
        description: "Failed to export data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex-1 space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Explorer</h1>
          <p className="text-muted-foreground">Browse and export your CRM data</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => handleExport('csv')}
            disabled={exporting}
          >
            {exporting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}
            Export CSV
          </Button>
          <Button 
            size="sm"
            onClick={() => handleExport('excel')}
            disabled={exporting}
          >
            {exporting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}
            Export Excel
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-card rounded-lg border">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters:</span>
        </div>
        <Select value={collection} onValueChange={setCollection}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Collection" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="leads">Leads</SelectItem>
            <SelectItem value="tasks">Tasks</SelectItem>
            <SelectItem value="notes">Notes</SelectItem>
            <SelectItem value="activity">Activity</SelectItem>
          </SelectContent>
        </Select>
        <Select value={ownerFilter} onValueChange={setOwnerFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Owner" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-owners">All Owners</SelectItem>
            <SelectItem value="priya">Priya</SelectItem>
            <SelectItem value="aryan">Aryan</SelectItem>
            <SelectItem value="sneha">Sneha</SelectItem>
          </SelectContent>
        </Select>
        <Select value={stageFilter} onValueChange={setStageFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Stage" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-stages">All Stages</SelectItem>
            <SelectItem value="Discovery">Discovery</SelectItem>
            <SelectItem value="Qualified">Qualified</SelectItem>
            <SelectItem value="Proposal">Proposal</SelectItem>
            <SelectItem value="Won">Won</SelectItem>
            <SelectItem value="Lost">Lost</SelectItem>
          </SelectContent>
        </Select>
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>Rows: {totalCount.toLocaleString()} (showing {data.length})</span>
        <span>•</span>
        <span>Last updated {new Date().toLocaleTimeString()} IST</span>
      </div>

      {/* Data Grid */}
      <div className="border rounded-lg">
        {loading ? (
          <div className="p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading data...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b bg-muted/50">
                <tr>
                  {data.length > 0 && Object.keys(data[0]).slice(0, 6).map((key) => (
                    <th key={key} className="text-left p-3 font-medium capitalize">
                      {key.replace('_', ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr key={item._id || index} className="border-b hover:bg-muted/25">
                    {Object.entries(item).slice(0, 6).map(([key, value]) => (
                      <td key={key} className="p-3">
                        {key === 'status' || key === 'stage' ? (
                          <Badge variant="secondary">{String(value)}</Badge>
                        ) : key === 'amount' && typeof value === 'number' ? (
                          `₹${value.toLocaleString()}`
                        ) : (
                          <span className={key.includes('date') ? 'text-sm text-muted-foreground' : 'font-medium'}>
                            {String(value)}
                          </span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}