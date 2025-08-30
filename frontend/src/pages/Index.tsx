import { useState, useEffect } from "react";
import { KPICard } from "@/components/dashboard/KPICard";
import { RecentArtifacts } from "@/components/dashboard/RecentArtifacts";
import { QuickPrompts } from "@/components/dashboard/QuickPrompts";
import { TrendingUp, Users, DollarSign, Calendar } from "lucide-react";
import { crmAPI, type KPIData } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const [kpiData, setKpiData] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetchKPIs = async () => {
      try {
        const data = await crmAPI.getKPIs();
        setKpiData(data);
      } catch (error) {
        console.error('Failed to fetch KPIs:', error);
        toast({
          title: "Error",
          description: "Failed to fetch dashboard metrics. Using fallback data.",
          variant: "destructive",
        });
        // Use fallback data
        setKpiData({
          mtd_revenue: { value: "₹2,45,000", change: { value: 12.5, type: "positive" } },
          new_leads: { value: "127", change: { value: 8.2, type: "positive" } },
          win_rate: { value: "23.5%", change: { value: 3.1, type: "negative" } },
          avg_cycle: { value: "18 days", change: { value: 5.2, type: "positive" } }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchKPIs();
  }, [toast]);

  if (loading) {
    return (
      <div className="flex-1 space-y-6 p-8">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-6 p-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's what's happening with your CRM today.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="MTD Revenue"
          value={kpiData?.mtd_revenue.value || "₹0"}
          change={kpiData?.mtd_revenue.change}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <KPICard
          title="New Leads"
          value={kpiData?.new_leads.value || "0"}
          change={kpiData?.new_leads.change}
          icon={<Users className="h-5 w-5" />}
        />
        <KPICard
          title="Win Rate"
          value={kpiData?.win_rate.value || "0%"}
          change={kpiData?.win_rate.change}
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <KPICard
          title="Avg Cycle"
          value={kpiData?.avg_cycle.value || "0 days"}
          change={kpiData?.avg_cycle.change}
          icon={<Calendar className="h-5 w-5" />}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid gap-6 md:grid-cols-2">
        <QuickPrompts />
        <RecentArtifacts />
      </div>
    </div>
  );
};

export default Index;
