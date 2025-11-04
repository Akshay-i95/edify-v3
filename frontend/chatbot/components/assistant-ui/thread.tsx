import {
  ActionBarPrimitive,
  BranchPickerPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useMessage,
} from "@assistant-ui/react";
import type { FC } from "react";
import {
  ArrowDownIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  CopyIcon,
  PencilIcon,
  RefreshCwIcon,
  SendHorizontalIcon,
  BookIcon,
  ExternalLinkIcon,
  ArrowUpIcon,
  PlusIcon,
  Square,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useState, useEffect, useRef } from "react";

import { Button } from "@/components/ui/button";
import { MarkdownText } from "@/components/assistant-ui/markdown-text";
import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { ToolFallback } from "./tool-fallback";

// Modern AI-inspired thinking and reasoning styles (ChatGPT/Gemini/Claude style)
const thinkingStyles = `
  /* Premium AI Thinking Component - ChatGPT 4o/Gemini 2.0/Claude 3.5 Style */
  .ai-thinking-container {
    margin-bottom: 20px;
    padding: 16px 20px;
    border-radius: 16px;
    background: linear-gradient(135deg, 
      rgba(247, 248, 249, 0.95) 0%, 
      rgba(250, 251, 252, 0.98) 100%
    );
    position: relative;
    transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
    overflow: hidden;
    border: 1px solid rgba(0, 0, 0, 0.06);
    box-shadow: 
      0 1px 3px rgba(0, 0, 0, 0.1),
      0 1px 2px rgba(0, 0, 0, 0.06),
      inset 0 1px 0 rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(8px);
    transform: translateY(0);
    animation: thinkingSlideIn 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
  }
  
  .dark .ai-thinking-container {
    background: linear-gradient(135deg, 
      rgba(31, 32, 35, 0.95) 0%, 
      rgba(40, 42, 46, 0.98) 100%
    );
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.3),
      0 1px 3px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  
  @keyframes thinkingSlideIn {
    0% { 
      opacity: 0; 
      transform: translateY(-8px) scale(0.98); 
    }
    100% { 
      opacity: 1; 
      transform: translateY(0) scale(1); 
    }
  }
  
  /* AI Thinking Header */
  .ai-thinking-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }
  
  .ai-thinking-icon {
    width: 20px;
    height: 20px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: iconPulse 2s ease-in-out infinite;
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
  }
  
  .dark .ai-thinking-icon {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    box-shadow: 0 2px 4px rgba(79, 70, 229, 0.4);
  }
  
  @keyframes iconPulse {
    0%, 100% { transform: scale(1); opacity: 0.9; }
    50% { transform: scale(1.05); opacity: 1; }
  }
  
  .ai-thinking-title {
    font-size: 14px;
    font-weight: 600;
    color: #1f2937;
    letter-spacing: -0.025em;
  }
  
  .dark .ai-thinking-title {
    color: #f9fafb;
  }
  
  /* Premium Animated Dots */
  .ai-thinking-dots {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    margin-left: 8px;
  }
  
  .ai-thinking-dot {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    animation: premiumDotPulse 1.8s infinite cubic-bezier(0.4, 0.0, 0.6, 1);
    opacity: 0.6;
  }
  
  .dark .ai-thinking-dot {
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    opacity: 0.8;
  }
  
  .ai-thinking-dot:nth-child(1) { animation-delay: 0s; }
  .ai-thinking-dot:nth-child(2) { animation-delay: 0.2s; }
  .ai-thinking-dot:nth-child(3) { animation-delay: 0.4s; }
  
  @keyframes premiumDotPulse {
    0%, 80%, 100% { 
      transform: translateY(0) scale(1); 
      opacity: 0.6; 
    }
    40% { 
      transform: translateY(-3px) scale(1.2); 
      opacity: 1; 
    }
  }
  
  /* Progress Indicator */
  .ai-thinking-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    width: 100%;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 0 0 16px 16px;
    overflow: hidden;
  }
  
  .ai-thinking-progress-bar {
    height: 100%;
    width: 100%;
    background: linear-gradient(
      90deg,
      rgba(99, 102, 241, 0) 0%,
      rgba(99, 102, 241, 0.8) 30%,
      rgba(139, 92, 246, 1) 50%,
      rgba(99, 102, 241, 0.8) 70%,
      rgba(99, 102, 241, 0) 100%
    );
    background-size: 200% 100%;
    animation: progressFlow 2.5s ease-in-out infinite;
  }
  
  .dark .ai-thinking-progress {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .dark .ai-thinking-progress-bar {
    background: linear-gradient(
      90deg,
      rgba(124, 58, 237, 0) 0%,
      rgba(124, 58, 237, 0.9) 30%,
      rgba(168, 85, 247, 1) 50%,
      rgba(124, 58, 237, 0.9) 70%,
      rgba(124, 58, 237, 0) 100%
    );
  }
  
  @keyframes progressFlow {
    0% { background-position: -200% 50%; }
    100% { background-position: 200% 50%; }
  }
  
  /* Subtle Background Animation */
  .ai-thinking-bg-animation {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(
      circle at 30% 20%,
      rgba(99, 102, 241, 0.03) 0%,
      transparent 50%
    );
    animation: bgShift 4s ease-in-out infinite;
    border-radius: 16px;
    pointer-events: none;
  }
  
  .dark .ai-thinking-bg-animation {
    background: radial-gradient(
      circle at 30% 20%,
      rgba(124, 58, 237, 0.05) 0%,
      transparent 50%
    );
  }
  
  @keyframes bgShift {
    0%, 100% { transform: translate(0, 0) scale(1); }
    50% { transform: translate(5px, -3px) scale(1.02); }
  }
  
  /* Modern Reasoning Display Styles */
  .modern-reasoning-container {
    margin-bottom: 20px;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    backdrop-filter: blur(8px);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }
  
  .dark .modern-reasoning-container {
    background: rgba(30, 32, 36, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.2), 0 1px 2px 0 rgba(0, 0, 0, 0.15);
  }
  
  .reasoning-toggle-button {
    width: 100%;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    background: transparent;
    border: none;
    cursor: pointer;
    text-align: left;
    transition: all 0.2s ease;
    font-size: 13px;
    font-weight: 500;
    color: #4b5563;
    border-radius: 12px 12px 0 0;
  }
  
  .dark .reasoning-toggle-button {
    color: #9ca3af;
  }
  
  .reasoning-toggle-button:hover {
    background: rgba(255, 255, 255, 0.5);
  }
  
  .dark .reasoning-toggle-button:hover {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .reasoning-icon {
    width: 16px;
    height: 16px;
    color: #6366f1;
    transition: transform 0.2s ease;
    flex-shrink: 0;
  }
  
  .reasoning-icon.expanded {
    transform: rotate(90deg);
  }
  
  .reasoning-content {
    padding: 0 18px 18px 18px;
    background: rgba(255, 255, 255, 0.7);
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    animation: reasoningExpand 0.3s ease-out;
    backdrop-filter: blur(4px);
  }
  
  .dark .reasoning-content {
    background: rgba(17, 24, 39, 0.7);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  @keyframes reasoningExpand {
    0% { opacity: 0; transform: translateY(-10px); }
    100% { opacity: 1; transform: translateY(0); }
  }
  
  .reasoning-step {
    margin-bottom: 14px;
    padding: 14px 16px;
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 10px;
    font-size: 13px;
    line-height: 1.5;
    color: #374151;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
  }
  
  .reasoning-step:hover {
    background: rgba(255, 255, 255, 0.95);
    border-color: rgba(0, 0, 0, 0.1);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
  
  .dark .reasoning-step {
    background: rgba(31, 41, 55, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #d1d5db;
  }
  
  .dark .reasoning-step:hover {
    background: rgba(31, 41, 55, 0.95);
    border-color: rgba(255, 255, 255, 0.12);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
  
  .reasoning-step-title {
    font-weight: 600;
    color: #374151;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }
  
  .dark .reasoning-step-title {
    color: #e5e7eb;
  }
  
  /* Animated entrance effects */
  @keyframes slideInFromLeft {
    0% {
      opacity: 0;
      transform: translateX(-20px);
    }
    100% {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  @keyframes slideInFromBottom {
    0% {
      opacity: 0;
      transform: translateY(20px);
    }
    100% {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  @keyframes fadeIn {
    0% {
      opacity: 0;
    }
    100% {
      opacity: 1;
    }
  }
  
  .animate-in {
    animation-fill-mode: both;
  }
  
  .slide-in-from-left-2 {
    animation: slideInFromLeft 0.3s ease-out;
  }
  
  .slide-in-from-bottom-2 {
    animation: slideInFromBottom 0.3s ease-out;
  }
  
  .fade-in {
    animation: fadeIn 0.3s ease-out;
  }
  
  /* Scrollbar styling for reasoning content */
  .reasoning-content::-webkit-scrollbar {
    width: 6px;
  }
  
  .reasoning-content::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 3px;
  }
  
  .reasoning-content::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 3px;
  }
  
  .dark .reasoning-content::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .dark .reasoning-content::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
  }
`;

// Enhanced thinking messages for different query types
const getThinkingMessage = (isFirst: boolean = false) => {
  const messages = [
    "Analyzing your educational query with advanced AI reasoning...",
    "Processing context from educational documents and frameworks...",
    "Applying chain-of-thought analysis for comprehensive response...",
    "Synthesizing information from multiple educational sources...",
    "Evaluating pedagogical best practices and research findings...",
    "Generating evidence-based educational guidance...",
  ];
  
  return isFirst ? messages[0] : messages[Math.floor(Math.random() * messages.length)];
};

export const Thread: FC = () => {
  // Inject thinking styles
  useEffect(() => {
    const styleId = 'thinking-styles';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = thinkingStyles;
      document.head.appendChild(style);
    }
  }, []);

  return (
    <ThreadPrimitive.Root
      className="bg-background flex h-full flex-col overflow-hidden"
      style={{
        ["--thread-max-width" as string]: "52rem",
        ["--thread-padding-x" as string]: "1rem",
      }}
    >
      <ThreadPrimitive.Viewport className="relative flex min-w-0 flex-1 flex-col items-center gap-6 overflow-y-auto scroll-smooth px-[var(--thread-padding-x)]">
        <ThreadWelcome />

        <ThreadPrimitive.Messages
          components={{
            UserMessage: UserMessage,
            EditComposer: EditComposer,
            AssistantMessage: AssistantMessage,
          }}
        />

        <ThreadPrimitive.If empty={false}>
          <div className="min-h-6 min-w-6 shrink-0" />
        </ThreadPrimitive.If>
      </ThreadPrimitive.Viewport>

      <div className="bg-background sticky bottom-0 mx-auto flex w-full max-w-[var(--thread-max-width)] flex-col gap-4 px-[var(--thread-padding-x)] pb-4 pt-2 md:pb-6">
        <ThreadScrollToBottom />
        <Composer />
      </div>
    </ThreadPrimitive.Root>
  );
};

const ThreadScrollToBottom: FC = () => {
  return (
    <ThreadPrimitive.ScrollToBottom asChild>
      <TooltipIconButton
        tooltip="Scroll to bottom"
        variant="outline"
        className="dark:bg-background dark:hover:bg-accent absolute -top-12 z-10 self-center rounded-full p-4 disabled:invisible"
      >
        <ArrowDownIcon />
      </TooltipIconButton>
    </ThreadPrimitive.ScrollToBottom>
  );
};

const ThreadWelcome: FC = () => {
  return (
    <ThreadPrimitive.Empty>
      <div className="flex w-full max-w-4xl flex-grow flex-col items-center justify-center">
        {/* Welcome message centered with search bar at bottom */}
        <div className="flex w-full flex-grow flex-col items-center justify-center px-8">
          <div className="text-center">
            <div className="text-2xl font-semibold">
              Welcome to Edify AI Assistant!
            </div>
            <div className="text-muted-foreground/65 text-2xl mt-2">
              How can I help you with educational curriculum today?
            </div>
          </div>
        </div>
        <ThreadWelcomeSuggestions />
      </div>
    </ThreadPrimitive.Empty>
  );
};

const ThreadWelcomeSuggestions: FC = () => {
  return (
    <div className="mt-3 flex w-full items-stretch justify-center gap-4">
      <ThreadPrimitive.Suggestion
        className="hover:bg-muted/80 flex max-w-sm grow basis-0 flex-col items-center justify-center rounded-lg border p-3 transition-colors ease-in"
        prompt="What are the key assessment strategies in modern education?"
        method="replace"
        autoSend
      >
        <span className="line-clamp-2 text-ellipsis text-sm font-semibold">
          What are the key assessment strategies in modern education?
        </span>
      </ThreadPrimitive.Suggestion>
      <ThreadPrimitive.Suggestion
        className="hover:bg-muted/80 flex max-w-sm grow basis-0 flex-col items-center justify-center rounded-lg border p-3 transition-colors ease-in"
        prompt="How can teachers implement formative assessment effectively?"
        method="replace"
        autoSend
      >
        <span className="line-clamp-2 text-ellipsis text-sm font-semibold">
          How can teachers implement formative assessment effectively?
        </span>
      </ThreadPrimitive.Suggestion>
    </div>
  );
};

const Composer: FC = () => {
  return (
    <ComposerPrimitive.Root className="focus-within:ring-offset-2 relative flex w-full flex-col rounded-2xl focus-within:ring-2 focus-within:ring-black dark:focus-within:ring-white">
      <ComposerPrimitive.Input
        rows={1}
        autoFocus
        placeholder="Send a message..."
        className="bg-muted border-border dark:border-muted-foreground/15 focus:outline-primary placeholder:text-muted-foreground max-h-[calc(50dvh)] min-h-16 w-full resize-none rounded-t-2xl border-x border-t px-4 pt-2 pb-3 text-base outline-none"
        aria-label="Message input"
      />
      <ComposerAction />
    </ComposerPrimitive.Root>
  );
};

const ComposerAction: FC = () => {
  return (
    <div className="bg-muted border-border dark:border-muted-foreground/15 relative flex items-center justify-between rounded-b-2xl border-x border-b p-2">
      <TooltipIconButton
        tooltip="Attach file"
        variant="ghost"
        className="hover:bg-foreground/15 dark:hover:bg-background/50 scale-115 p-3.5"
        onClick={() => {
          console.log("Attachment clicked - not implemented");
        }}
      >
        <PlusIcon />
      </TooltipIconButton>

      <ThreadPrimitive.If running={false}>
        <ComposerPrimitive.Send asChild>
          <Button
            type="submit"
            variant="default"
            className="dark:border-muted-foreground/90 border-muted-foreground/60 hover:bg-primary/75 size-8 rounded-full border"
            aria-label="Send message"
          >
            <ArrowUpIcon className="size-5" />
          </Button>
        </ComposerPrimitive.Send>
      </ThreadPrimitive.If>

      <ThreadPrimitive.If running>
        <ComposerPrimitive.Cancel asChild>
          <Button
            type="button"
            variant="default"
            className="dark:border-muted-foreground/90 border-muted-foreground/60 hover:bg-primary/75 size-8 rounded-full border"
            aria-label="Stop generating"
          >
            <Square className="size-3.5 fill-white dark:size-4 dark:fill-black" />
          </Button>
        </ComposerPrimitive.Cancel>
      </ThreadPrimitive.If>
    </div>
  );
};

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="flex flex-col w-full max-w-4xl py-4 items-end">
      <div className="flex gap-2 items-start max-w-[70%]">
        <UserActionBar />
        <div className="bg-muted text-foreground break-words rounded-3xl px-5 py-2.5">
          <MessagePrimitive.Content />
        </div>
      </div>
      <BranchPicker className="mt-2 mr-2" />
    </MessagePrimitive.Root>
  );
};

const UserActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="never"
      className="flex flex-col items-end mt-2.5"
    >
      <ActionBarPrimitive.Edit asChild>
        <TooltipIconButton tooltip="Edit">
          <PencilIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Edit>
    </ActionBarPrimitive.Root>
  );
};

const EditComposer: FC = () => {
  return (
    <ComposerPrimitive.Root className="bg-muted my-4 flex w-full max-w-4xl flex-col gap-2 rounded-xl">
      <ComposerPrimitive.Input className="text-foreground flex h-8 w-full resize-none bg-transparent p-4 pb-0 outline-none" />

      <div className="mx-3 mb-3 flex items-center justify-center gap-2 self-end">
        <ComposerPrimitive.Cancel asChild>
          <Button variant="ghost">Cancel</Button>
        </ComposerPrimitive.Cancel>
        <ComposerPrimitive.Send asChild>
          <Button>Send</Button>
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
};

// Premium AI Thinking Component with Live Reasoning Stream
const PremiumThinking: FC<{ 
  content?: string; 
  isTyping?: boolean;
  liveReasoning?: string;
  onReasoningChange?: (isVisible: boolean, content: string) => void;
}> = ({ 
  content,
  isTyping = true,
  liveReasoning = "",
  onReasoningChange
}) => {
  // State for dropdown and animations
  const [isExpanded, setIsExpanded] = useState(false);
  const [showLiveContent, setShowLiveContent] = useState(false);
  
  // Use live reasoning if available, otherwise use placeholder
  const reasoningText = liveReasoning || content || "Analyzing query and retrieving relevant educational information...";
  
  // Dynamic thinking message with rotation
  const [thinkingMessage, setThinkingMessage] = useState(() => getThinkingMessage(true));
  const [messageIndex, setMessageIndex] = useState(0);
  const [animateText, setAnimateText] = useState(true);
  
  // Show live content when we start receiving reasoning
  useEffect(() => {
    if (liveReasoning && liveReasoning.length > 10) {
      setShowLiveContent(true);
      // Keep collapsed by default - user can expand if they want to see details
      // setIsExpanded(true); // Removed auto-expand
    }
  }, [liveReasoning]);
  
  // Rotate thinking messages for better UX
  useEffect(() => {
    if (!isTyping) return;
    
    const messages = [
      "Analyzing your educational query with advanced AI reasoning...",
      "Processing context from educational documents and frameworks...",
      "Applying chain-of-thought analysis for comprehensive response...",
      "Synthesizing information from multiple educational sources...",
      "Evaluating pedagogical best practices and research findings...",
      "Generating evidence-based educational guidance..."
    ];
    
    const interval = setInterval(() => {
      setAnimateText(false);
      setTimeout(() => {
        setMessageIndex(prev => (prev + 1) % messages.length);
        setThinkingMessage(messages[(messageIndex + 1) % messages.length]);
        setAnimateText(true);
      }, 150);
    }, 2500);
    
    return () => clearInterval(interval);
  }, [isTyping, messageIndex]);
  
  // Notify parent component so reasoning is available after response
  useEffect(() => {
    if (onReasoningChange) {
      onReasoningChange(true, reasoningText);
    }
  }, [onReasoningChange, reasoningText]);
  
  return (
    <div className="ai-thinking-container animate-in fade-in slide-in-from-bottom-2 duration-500" role="status" aria-live="polite">
      <div className="ai-thinking-bg-animation"></div>
      
      {/* Main thinking header - always visible */}
      <div className="ai-thinking-header">
        <div className="ai-thinking-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" className="text-white animate-pulse">
            <path 
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <span className="ai-thinking-title">
          {showLiveContent ? "AI Reasoning Process" : "Thinking"}
        </span>
        <div className="ai-thinking-dots">
          <div className="ai-thinking-dot"></div>
          <div className="ai-thinking-dot"></div>
          <div className="ai-thinking-dot"></div>
        </div>
        
        {/* Expand/Collapse button for reasoning - always show during thinking */}
        {isTyping && (
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="ml-auto p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            aria-label={isExpanded ? "Hide reasoning details" : "Show reasoning details"}
          >
            <ChevronDownIcon 
              className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            />
          </button>
        )}
      </div>
      
      {/* Status message */}
      <div className={`text-xs text-gray-600 dark:text-gray-400 opacity-80 transition-all duration-300 ${animateText ? 'opacity-80 translate-y-0' : 'opacity-40 translate-y-1'}`}>
        {showLiveContent ? 
          `Streaming reasoning in real-time (${liveReasoning?.length || 0} chars)...` : 
          thinkingMessage
        }
      </div>
      
      {/* Reasoning content dropdown - always available during thinking */}
      {isTyping && (
        <div className={`mt-3 overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
            <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full animate-pulse ${
                showLiveContent ? 'bg-blue-500' : 'bg-orange-500'
              }`}></div>
              {showLiveContent ? 'Live Reasoning Stream' : 'Preparing Reasoning...'}
            </div>
            <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap max-h-64 overflow-y-auto font-mono leading-relaxed">
              {liveReasoning || (showLiveContent ? "Waiting for reasoning data..." : "AI is analyzing your query and preparing detailed reasoning...")}
              {isTyping && <span className="animate-pulse">▋</span>}
            </div>
          </div>
        </div>
      )}
      
      {/* Animated progress bar */}
      <div className="ai-thinking-progress">
        <div className="ai-thinking-progress-bar"></div>
      </div>
      
      {/* Small indicator for real-time processing */}
      <div className="flex items-center gap-1 mt-2 text-xs opacity-60">
        <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${
          showLiveContent ? 'bg-blue-500' : 'bg-green-500'
        }`}></div>
        <span>
          {showLiveContent ? 'Streaming reasoning live' : 'Processing in real-time'}
        </span>
      </div>
    </div>
  );
};

// Simple Thinking Component with just animated dots
const SimpleThinking: FC = () => {
  return (
    <div className="flex items-center gap-2 py-2" role="status" aria-live="polite">
      <span className="text-sm text-gray-600 dark:text-gray-400">Thinking</span>
      <div className="flex items-center gap-1">
        <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
        <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
        <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
      </div>
    </div>
  );
};

const AssistantMessage: FC = () => {
  // Track if the message is still being generated
  const [isGenerating, setIsGenerating] = useState(true);
  // Track if we should show citations (after message is done generating)
  const [showCitations, setShowCitations] = useState(false);
  // For animation timing
  const [isResponseVisible, setIsResponseVisible] = useState(false);
  // Track thinking visibility for smooth animations
  const [showThinking, setShowThinking] = useState(true);
  // Store the reasoning content to display after generation
  const [savedReasoning, setSavedReasoning] = useState("");
  // NEW: Track live reasoning as it streams in
  const [liveReasoning, setLiveReasoning] = useState("");
  
  // Sources state for document links and metadata
  const [sources, setSources] = useState<any[]>([]);

  // Get message to check for completion
  const message = useMessage();
  
  // NEW: Extract live reasoning from streaming message content
  useEffect(() => {
    const messageData = message as any;
    let content = "";
    
    // Handle different content formats
    if (messageData?.content) {
      if (typeof messageData.content === 'string') {
        content = messageData.content;
      } else if (Array.isArray(messageData.content)) {
        // Handle array format - extract text parts
        const textParts = messageData.content
          .filter((part: any) => part.type === 'text')
          .map((part: any) => part.text || '')
          .join('');
        content = textParts;
      } else if (messageData.content.text) {
        content = messageData.content.text;
      }
    }
    
    // Only proceed if we have valid string content
    if (typeof content === 'string' && content.length > 0) {
      // Look for reasoning section in the streaming content
      const reasoningMatch = content.match(/### 🧠 AI Reasoning\n\n> ([\s\S]*?)(?=\n\n---|\n\n### |$)/);
      if (reasoningMatch && reasoningMatch[1]) {
        const extractedReasoning = reasoningMatch[1].trim();
        if (extractedReasoning && extractedReasoning !== liveReasoning) {
          setLiveReasoning(extractedReasoning);
        }
      }
    } else {
      // Content not ready for reasoning extraction
    }
  }, [message, liveReasoning]);
  
  // Check if message is completed and extract sources if available
  useEffect(() => {
    // Check if message is completed OR if we have annotations (reasoning might arrive before completion)
    const messageData = message as any;
    
    if (message.status?.type === 'complete' || (messageData && messageData.annotations)) {
      // Only trigger completion animations if actually complete
      if (message.status?.type === 'complete') {
        // Start fade-out animation for thinking
        setShowThinking(false);
        
        // After thinking fades out, show response
        setTimeout(() => {
          setIsGenerating(false);
          setIsResponseVisible(true);
          setTimeout(() => setShowCitations(true), 600);
        }, 300);
      }
      
      // Extract reasoning from annotations first (most reliable method)
      if (messageData && messageData.annotations) {
        // Find sources annotation
        const sourcesAnnotation = messageData.annotations.find(
          (annotation: any) => annotation.type === 'sources'
        );
        
        if (sourcesAnnotation?.data) {
          let sourcesData = sourcesAnnotation.data;
          
          // Handle base64 encoded sources
          if (typeof sourcesData === 'string') {
            try {
              const decodedData = Buffer.from(sourcesData, 'base64').toString('utf-8');
              sourcesData = JSON.parse(decodedData);
            } catch (error) {
              console.error('Failed to decode sources data:', error);
              sourcesData = [];
            }
          }
          
          // Ensure sourcesData is an array
          const sourcesArray = Array.isArray(sourcesData) ? sourcesData : 
                              sourcesData.sources ? sourcesData.sources : [];
          
          setSources(sourcesArray);
          
          // Also dispatch an event for other components that might need sources
          window.dispatchEvent(
            new CustomEvent('sourcesUpdate', { 
              detail: { sources: sourcesArray } 
            })
          );
        }
        
        // Find reasoning annotation
        const reasoningAnnotation = messageData.annotations.find(
          (annotation: any) => annotation.type === 'reasoning'
        );
        
        if (reasoningAnnotation?.data) {
          // FIXED: Handle both string data and object with content property
          let reasoningContent = reasoningAnnotation.data;
          
          // Handle case when data is a string (directly or base64 encoded)
          if (typeof reasoningContent === 'string') {
            // Check if it's base64 encoded
            try {
              const decodedData = Buffer.from(reasoningContent, 'base64').toString('utf-8');
              // Try to parse as JSON if it's an object
              try {
                const parsedData = JSON.parse(decodedData);
                reasoningContent = parsedData.content || decodedData;
              } catch {
                // If not JSON, use decoded string directly
                reasoningContent = decodedData;
              }
            } catch {
              // If not base64, use string directly
              reasoningContent = reasoningContent;
            }
          } else if (reasoningContent.content) {
            // Handle case when data is an object with content property
            reasoningContent = reasoningContent.content;
          }
          
          setSavedReasoning(reasoningContent);
        } else {
          // Try getting reasoning from metadata
          if (messageData.metadata?.reasoning) {
            setSavedReasoning(messageData.metadata.reasoning);
          }
        }
      } else if (messageData.metadata?.reasoning) {
        // Alternative path - check metadata directly if no annotations
        setSavedReasoning(messageData.metadata.reasoning);
      }
    }
  }, [message.status, message]);

  // For demo purposes, also use the old timer approach as fallback
  useEffect(() => {
    if (isGenerating && message.status?.type !== 'complete') {
      const timer = setTimeout(() => {
        setShowThinking(false);
        setTimeout(() => {
          setIsGenerating(false);
          setIsResponseVisible(true);
          setTimeout(() => setShowCitations(true), 600);
        }, 300);
      }, 4000);
      
      return () => clearTimeout(timer);
    }
  }, [isGenerating, message.status]);

  // Handle saving reasoning content for display after generation completes
  const handleReasoningChange = (isVisible: boolean, content: string) => {
    // Only save reasoning content during thinking phase if we don't have real backend reasoning yet
    // Real reasoning from backend annotations will override this
    if (!savedReasoning) {
      setSavedReasoning(content);
    }
  };

  return (
    <MessagePrimitive.Root className="flex flex-col w-full max-w-4xl py-4 items-start">
      
      <div className="text-foreground max-w-[85%] break-words leading-7 my-1.5">
        {/* Simple Thinking Component with just animated dots */}
        {isGenerating && (
          <div className={`transition-all duration-300 ease-out ${showThinking ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'}`}>
            <SimpleThinking />
          </div>
        )}
        
        {/* Response Content with smooth fade-in animation when thinking completes */}
        <div 
          className={`bg-inherit rounded-2xl px-0 py-0 transition-all duration-500 ease-in-out ${
            isResponseVisible ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform translate-y-2'
          }`}
          aria-live="polite"
          role="region"
        >
          {/* Always display saved reasoning in modern collapsed state when response is complete */}
          {/* Note: Reasoning and sources are now streamed directly as HTML content from route.ts */}
        
          <MessagePrimitive.Content 
            components={{ 
              Text: MarkdownText, 
              tools: { Fallback: ToolFallback },
              Reasoning: () => null, // Override default Reasoning component
            }}
          />
          
          {/* Simple source display without complex context */}
          {showCitations && !isGenerating && sources.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 animate-in fade-in duration-300">
              <div className="flex flex-col gap-2">
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium flex items-center gap-1.5">
                  <BookIcon className="size-3" />
                  Sources ({sources.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {sources.map((source, index) => {
                    // Ensure download URL is properly formatted
                    let downloadUrl = source.download_url;
                    
                    // If URL doesn't start with http, use the backend API endpoint
                    if (!downloadUrl || !downloadUrl.startsWith('http')) {
                      const backendUrl = typeof window !== 'undefined' && window.BACKEND_URL || 'http://localhost:5000';
                      downloadUrl = `${backendUrl}/api/files/download/${encodeURIComponent(source.filename || '')}`;
                    }
                    
                    return (
                      <a 
                        key={index}
                        href={downloadUrl}
                        className={`inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded ${
                          source.download_available !== false
                            ? 'bg-gray-50 hover:bg-gray-100 dark:bg-gray-800/50 dark:hover:bg-gray-800/80 cursor-pointer' 
                            : 'bg-gray-50/50 dark:bg-gray-800/30 cursor-not-allowed'
                        } text-gray-600 dark:text-gray-300 transition-colors border border-gray-200 dark:border-gray-700`}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={`${source.title || source.filename}${source.department ? ` - ${source.department}` : ''}${source.sub_department ? ` / ${source.sub_department}` : ''}`}
                        onClick={(e) => {
                          if (source.download_available === false) {
                            e.preventDefault();
                            alert('This document is not available for download.');
                          }
                        }}
                      >
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-red-500 flex-shrink-0">
                          <path d="M8 16H16V18H8V16ZM8 12H16V14H8V12ZM14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20Z" fill="currentColor"/>
                        </svg>
                        <span className="truncate max-w-[120px]">
                          {source.title || source.filename || `Doc ${index + 1}`}
                        </span>
                        {source.download_available !== false && (
                          <ExternalLinkIcon className="size-2.5 text-gray-400 flex-shrink-0" />
                        )}
                      </a>
                    );
                  })}
                </div>
                
                {/* Show metadata if available */}
                {sources.some(s => s.has_edify_metadata) && (
                  <div className="text-[10px] text-gray-400 mt-1">
                    Documents from Edify School System
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Only show action bar when the message is fully generated */}
      <div className="flex gap-2 items-center mt-2">
        {!isGenerating && (
          <AssistantActionBar />
        )}
        <BranchPicker className="justify-start" />
      </div>
    </MessagePrimitive.Root>
  );
};

const AssistantActionBar: FC = () => {
  return (
    <ActionBarPrimitive.Root
      hideWhenRunning
      autohide="not-last"
      autohideFloat="single-branch"
      className="text-muted-foreground flex gap-1 data-[floating]:bg-background data-[floating]:absolute data-[floating]:rounded-md data-[floating]:border data-[floating]:p-1 data-[floating]:shadow-sm"
    >
      <ActionBarPrimitive.Copy asChild>
        <TooltipIconButton tooltip="Copy">
          <MessagePrimitive.If copied>
            <CheckIcon />
          </MessagePrimitive.If>
          <MessagePrimitive.If copied={false}>
            <CopyIcon />
          </MessagePrimitive.If>
        </TooltipIconButton>
      </ActionBarPrimitive.Copy>
      <ActionBarPrimitive.Reload asChild>
        <TooltipIconButton tooltip="Refresh">
          <RefreshCwIcon />
        </TooltipIconButton>
      </ActionBarPrimitive.Reload>
    </ActionBarPrimitive.Root>
  );
};

const BranchPicker: FC<BranchPickerPrimitive.Root.Props> = ({
  className,
  ...rest
}) => {
  return (
    <BranchPickerPrimitive.Root
      hideWhenSingleBranch
      className={cn(
        "text-muted-foreground inline-flex items-center text-xs",
        className
      )}
      {...rest}
    >
      <BranchPickerPrimitive.Previous asChild>
        <TooltipIconButton tooltip="Previous">
          <ChevronLeftIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Previous>
      <span className="font-medium">
        <BranchPickerPrimitive.Number /> / <BranchPickerPrimitive.Count />
      </span>
      <BranchPickerPrimitive.Next asChild>
        <TooltipIconButton tooltip="Next">
          <ChevronRightIcon />
        </TooltipIconButton>
      </BranchPickerPrimitive.Next>
    </BranchPickerPrimitive.Root>
  );
};

// Note: ModernReasoning component has been replaced by direct HTML streaming in route.ts
// This provides a much more reliable approach where reasoning and sources are 
// embedded directly in the message content as styled HTML.

const CircleStopIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 16"
      fill="currentColor"
      width="16"
      height="16"
    >
      <rect width="10" height="10" x="3" y="3" rx="2" />
    </svg>
  );
};
