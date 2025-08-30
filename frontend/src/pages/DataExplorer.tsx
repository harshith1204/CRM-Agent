import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Download, Filter, Search } from "lucide-react";

export default function DataExplorer() {
  const [searchTerm, setSearchTerm] = useState("");
  
  const mockDeals = [
    { id: 1, name: "Acme Renewal", owner: "Priya", stage: "Proposal", amount: 24000, created: "2025-06-14", lastActivity: "2025-08-22" },
    { id: 2, name: "Globex Expansion", owner: "Aryan", stage: "Qualified", amount: 85000, created: "2025-07-05", lastActivity: "2025-08-25" },
    { id: 3, name: "TechCorp Integration", owner: "Sneha", stage: "Discovery", amount: 45000, created: "2025-08-01", lastActivity: "2025-08-20" },
  ];

  return (
    <div className="flex-1 space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Explorer</h1>
          <p className="text-muted-foreground">Browse and export your CRM data</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
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
        <Select defaultValue="all-owners">
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
        <Select defaultValue="all-stages">
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Stage" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all-stages">All Stages</SelectItem>
            <SelectItem value="discovery">Discovery</SelectItem>
            <SelectItem value="qualified">Qualified</SelectItem>
            <SelectItem value="proposal">Proposal</SelectItem>
          </SelectContent>
        </Select>
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search deals..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>Rows: 10,240 (previewing 1,000)</span>
        <span>•</span>
        <span>Last updated 10:12 IST</span>
      </div>

      {/* Data Grid */}
      <div className="border rounded-lg">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="text-left p-3 font-medium">Deal Name</th>
                <th className="text-left p-3 font-medium">Owner</th>
                <th className="text-left p-3 font-medium">Stage</th>
                <th className="text-left p-3 font-medium">Amount</th>
                <th className="text-left p-3 font-medium">Created</th>
                <th className="text-left p-3 font-medium">Last Activity</th>
              </tr>
            </thead>
            <tbody>
              {mockDeals.map((deal) => (
                <tr key={deal.id} className="border-b hover:bg-muted/25">
                  <td className="p-3 font-medium">{deal.name}</td>
                  <td className="p-3">{deal.owner}</td>
                  <td className="p-3">
                    <Badge variant="secondary">{deal.stage}</Badge>
                  </td>
                  <td className="p-3">₹{deal.amount.toLocaleString()}</td>
                  <td className="p-3 text-sm text-muted-foreground">{deal.created}</td>
                  <td className="p-3 text-sm text-muted-foreground">{deal.lastActivity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}