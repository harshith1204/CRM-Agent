import { KPICard } from "@/components/dashboard/KPICard";
import { RecentArtifacts } from "@/components/dashboard/RecentArtifacts";
import { QuickPrompts } from "@/components/dashboard/QuickPrompts";
import { TrendingUp, Users, DollarSign, Calendar } from "lucide-react";

const Index = () => {
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
          value="₹2,45,000"
          change={{ value: 12.5, type: "positive" }}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <KPICard
          title="New Leads"
          value="127"
          change={{ value: 8.2, type: "positive" }}
          icon={<Users className="h-5 w-5" />}
        />
        <KPICard
          title="Win Rate"
          value="23.5%"
          change={{ value: 3.1, type: "negative" }}
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <KPICard
          title="Avg Cycle"
          value="18 days"
          change={{ value: 5.2, type: "positive" }}
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
