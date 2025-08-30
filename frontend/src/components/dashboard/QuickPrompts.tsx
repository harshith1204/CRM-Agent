
import { Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const prompts = [
  "Deals created last week by owner (bar chart)",
  "Leads with no activity in 14 days (export)", 
  "MTD revenue vs target by region",
  "Top 10 stalled deals with next actions",
  "Pipeline forecast for next quarter"
];

export function QuickPrompts() {
  const navigate = useNavigate();

  const handlePromptClick = (prompt: string) => {
    // Navigate to agent console with the prompt
    navigate('/agent', { state: { initialPrompt: prompt } });
  };

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
              onClick={() => handlePromptClick(prompt)}
            >
              {prompt}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
