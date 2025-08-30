
import { NavLink, useLocation } from "react-router-dom";
import { 
  Home, 
  MessageSquare, 
  Database, 
  BarChart3, 
  Zap, 
  Shield,
  Clock
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/agent", label: "Agent Console", icon: MessageSquare },
  { href: "/data", label: "Data Explorer", icon: Database },
  { href: "/reports", label: "Report Builder", icon: BarChart3 },
  { href: "/automations", label: "Automations", icon: Zap },
  { href: "/audit", label: "Audit Logs", icon: Clock },
  { href: "/admin", label: "Admin", icon: Shield },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-card border-r min-h-[calc(100vh-4rem)]">
      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          
          return (
            <NavLink
              key={item.href}
              to={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
