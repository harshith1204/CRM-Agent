
import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const prompts = [
  "Deals created last week by owner (bar chart)",
  "Leads with no activity in 14 days (export)", 
  "MTD revenue vs target by region",
  "Top 10 stalled deals with next actions",
  "Pipeline forecast for next quarter"
];

export function QuickPrompts() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Try These
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {prompts.map((prompt, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              className="text-left h-auto py-2 px-3 whitespace-normal justify-start"
              onClick={() => {
                // Navigate to console with pre-filled prompt
                console.log("Navigate to console with:", prompt);
              }}
            >
              {prompt}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
