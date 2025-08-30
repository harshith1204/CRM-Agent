import { ChevronDown, ChevronRight, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useState } from "react";

interface PlanStep {
  id: number;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  tool?: string;
  params?: Record<string, any>;
  output?: {
    rows?: number;
    bytes?: number;
    duration?: number;
  };
}

interface Plan {
  steps: PlanStep[];
}

interface PlanPanelProps {
  plan: Plan | null;
}

export function PlanPanel({ plan }: PlanPanelProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (stepId: number) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stepId)) {
        newSet.delete(stepId);
      } else {
        newSet.add(stepId);
      }
      return newSet;
    });
  };

  const getStatusIcon = (status: PlanStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-success" />;
      case 'running':
        return <Clock className="h-4 w-4 text-warning animate-spin" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: PlanStep['status']) => {
    const variants = {
      pending: 'secondary',
      running: 'default',
      completed: 'default',
      error: 'destructive'
    } as const;

    return (
      <Badge variant={variants[status]} className="text-xs">
        {status}
      </Badge>
    );
  };

  if (!plan) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Plan & Tools</h2>
          <p className="text-sm text-muted-foreground">Execution steps will appear here</p>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center text-muted-foreground">
            <Clock className="h-8 w-8 mx-auto mb-2" />
            <p className="text-sm">No active plan</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Plan & Tools</h2>
            <p className="text-sm text-muted-foreground">{plan.steps.length} steps</p>
          </div>
          <Button variant="outline" size="sm">
            Re-run
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="p-4 space-y-3">
          {plan.steps.map((step, index) => (
            <Collapsible key={step.id}>
              <div className="rounded-lg border border-border bg-card animate-slide-up transition-smooth hover:shadow-md" style={{ animationDelay: `${index * 0.1}s` }}>
                <CollapsibleTrigger 
                  className="w-full p-3 transition-smooth hover:bg-muted/50"
                  onClick={() => toggleStep(step.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-1 rounded animate-scale-in">
                        {index + 1}
                      </span>
                      {getStatusIcon(step.status)}
                      <span className="text-sm font-medium text-left">{step.name}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(step.status)}
                      {expandedSteps.has(step.id) ? (
                        <ChevronDown className="h-4 w-4 transition-transform duration-200" />
                      ) : (
                        <ChevronRight className="h-4 w-4 transition-transform duration-200" />
                      )}
                    </div>
                  </div>
                </CollapsibleTrigger>
                
                <CollapsibleContent>
                  <div className="px-3 pb-3 border-t border-border">
                    <div className="pt-3 space-y-2">
                      {step.tool && (
                        <div>
                          <span className="text-xs font-medium text-muted-foreground">Tool:</span>
                          <code className="ml-2 text-xs bg-muted px-2 py-1 rounded">{step.tool}</code>
                        </div>
                      )}
                      
                      {step.params && (
                        <div>
                          <span className="text-xs font-medium text-muted-foreground">Parameters:</span>
                          <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-auto">
                            {JSON.stringify(step.params, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {step.output && (
                        <div>
                          <span className="text-xs font-medium text-muted-foreground">Output:</span>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {step.output.rows && (
                              <Badge variant="outline" className="text-xs">
                                {step.output.rows} rows
                              </Badge>
                            )}
                            {step.output.bytes && (
                              <Badge variant="outline" className="text-xs">
                                {(step.output.bytes / 1024).toFixed(1)}KB
                              </Badge>
                            )}
                            {step.output.duration && (
                              <Badge variant="outline" className="text-xs">
                                {step.output.duration}ms
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </CollapsibleContent>
              </div>
            </Collapsible>
          ))}
        </div>
      </div>
    </div>
  );
}