import { AgentConsole as AgentConsoleComponent } from "@/components/console/AgentConsole";

export default function AgentConsole() {
  return (
    <div className="flex-1 h-[calc(100vh-4rem)] overflow-hidden">
      <AgentConsoleComponent />
    </div>
  );
}