
import { useState } from "react";
import { ChatPanel } from "./ChatPanel";
import { PlanPanel } from "./PlanPanel";
import { ArtifactsPanel } from "./ArtifactsPanel";

export function AgentConsole() {
  const [currentPlan, setCurrentPlan] = useState(null);
  const [artifacts, setArtifacts] = useState([]);

  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-5 gap-4 p-6">
      <div className="lg:col-span-2">
        <ChatPanel 
          onPlanUpdate={setCurrentPlan}
          onArtifactCreate={(artifact) => setArtifacts(prev => [...prev, artifact])}
        />
      </div>
      <div className="lg:col-span-3 grid grid-rows-1 lg:grid-rows-2 gap-4">
        <PlanPanel plan={currentPlan} />
        <ArtifactsPanel artifacts={artifacts} />
      </div>
    </div>
  );
}
