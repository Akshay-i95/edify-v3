"use client";

import { useThread } from "@assistant-ui/react";
import { Button } from "@/components/ui/button";
import { MessageCircle, Trash2 } from "lucide-react";

export const ConversationStatus = () => {
  const { messages } = useThread();

  // Count only user and assistant messages (exclude system messages)
  const conversationMessages = messages.filter(
    (msg: any) => msg.role === 'user' || msg.role === 'assistant'
  );

  const contextLength = conversationMessages.length;

  if (contextLength === 0) {
    return null;
  }

  const handleClearContext = () => {
    // For now, just reload the page to clear context
    // This can be enhanced later with proper thread management
    window.location.reload();
  };

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 border-b border-gray-200">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <MessageCircle size={16} />
        <span className="font-medium">
          {contextLength} message{contextLength !== 1 ? 's' : ''} in context
        </span>
        {contextLength > 10 && (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
            High context
          </span>
        )}
      </div>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClearContext}
        className="ml-auto text-gray-500 hover:text-red-600 hover:bg-red-50 h-7 px-2"
        title="Clear conversation history"
      >
        <Trash2 size={14} />
        <span className="ml-1 text-xs">Clear</span>
      </Button>
    </div>
  );
};