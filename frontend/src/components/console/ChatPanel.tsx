import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Send, Sparkles, Loader2 } from "lucide-react";
import { crmAPI, type ChatResponse } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ChatPanelProps {
  onPlanUpdate: (plan: any) => void;
  onArtifactCreate: (artifact: any) => void;
}

interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  artifacts?: any;
  embed_urls?: string[];
}

export function ChatPanel({ onPlanUpdate, onArtifactCreate }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const location = useLocation();
  const { toast } = useToast();

  const quickPrompts = [
    "Deals created last week by owner (bar chart)",
    "Leads with no activity in 14 days (export)",
    "Q2 pipeline by stage",
    "MTD revenue by source"
  ];

  // Handle initial prompt from navigation state
  useEffect(() => {
    if (location.state?.initialPrompt) {
      setInput(location.state.initialPrompt);
    }
  }, [location.state]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    
    try {
      const response: ChatResponse = await crmAPI.sendMessage({
        session_id: sessionId,
        user_id: "admin", // In a real app, this would come from auth
        message: input
      });
      
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        content: response.message,
        timestamp: new Date(),
        artifacts: response.artifacts,
        embed_urls: response.embed_urls
      };
      
      setMessages(prev => [...prev, agentMessage]);
      
      // Update plan panel
      onPlanUpdate(response.plan);
      
      // Create artifacts
      if (response.artifacts) {
        Object.entries(response.artifacts).forEach(([type, artifact]: [string, any]) => {
          onArtifactCreate({
            id: artifact.artifact_id,
            type: type.includes('excel') ? 'excel' : type.includes('plot') ? 'chart' : 'table',
            name: `Generated ${type}`,
            timestamp: new Date(),
            download_url: artifact.download_url
          });
        });
      }
      
      if (response.embed_urls?.length > 0) {
        toast({
          title: "Metabase Dashboard",
          description: "Embedded dashboard URLs generated successfully.",
        });
      }
      
    } catch (error) {
      console.error('Chat error:', error);
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        content: "Sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }

    setInput("");
  };

  const handlePromptClick = (prompt: string) => {
    setInput(prompt);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Chat</h2>
        <p className="text-sm text-muted-foreground">Ask questions about your CRM data</p>
      </div>

      {messages.length === 0 && (
        <div className="p-4 space-y-4 animate-fade-in">
          <div className="text-center text-muted-foreground">
            <Sparkles className="h-8 w-8 mx-auto mb-2 text-primary animate-pulse" />
            <p className="text-sm">Ask me about deals, leads, activities.</p>
          </div>
          
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Try these:</p>
            {quickPrompts.map((prompt, index) => (
              <Button
                key={index}
                variant="ghost"
                size="sm"
                className="w-full justify-start text-left h-auto p-3 hover-scale transition-smooth"
                onClick={() => handlePromptClick(prompt)}
              >
                <span className="text-sm">{prompt}</span>
              </Button>
            ))}
          </div>
        </div>
      )}

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex animate-slide-up ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 transition-smooth hover-scale ${
                  message.type === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      <div className="p-4 border-t border-border">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your CRM data..."
            onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
            className="flex-1"
            disabled={loading}
          />
          <Button onClick={handleSend} size="sm" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
        
        <div className="mt-2 flex flex-wrap gap-1">
          <Badge variant="secondary" className="text-xs">/listDeals</Badge>
          <Badge variant="secondary" className="text-xs">/createTask</Badge>
          <Badge variant="secondary" className="text-xs">/export</Badge>
        </div>
      </div>
    </div>
  );
}