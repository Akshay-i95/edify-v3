"use client";

import "@assistant-ui/react-markdown/styles/dot.css";

import {
  CodeHeaderProps,
  MarkdownTextPrimitive,
  unstable_memoizeMarkdownComponents as memoizeMarkdownComponents,
  useIsMarkdownCodeBlock,
} from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { FC, memo, useState } from "react";
import { CheckIcon, CopyIcon } from "lucide-react";

import { TooltipIconButton } from "@/components/assistant-ui/tooltip-icon-button";
import { cn } from "@/lib/utils";

const MarkdownTextImpl = () => {
  return (
    <MarkdownTextPrimitive
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      className="aui-md"
      components={defaultComponents}
    />
  );
};

// Function to remove emojis and sources sections from text
const removeEmojis = (text: string): string => {
  if (!text || typeof text !== 'string') return text;
  
  // Remove Edify reasoning data markers 
  text = text.replace(/<!--EDIFY_REASONING_DATA_START:[\s\S]*?:EDIFY_REASONING_DATA_END-->/g, '');
  text = text.replace(/<!-- REASONING_START -->[\s\S]*?<!-- REASONING_END -->/g, '');
  
  // Comprehensive emoji regex pattern including all Unicode ranges
  const emojiRegex = /[\u{1F600}-\u{1F64F}]|[\u{1F300}-\u{1F5FF}]|[\u{1F680}-\u{1F6FF}]|[\u{1F1E0}-\u{1F1FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{1F900}-\u{1F9FF}]|[\u{1F018}-\u{1F270}]|[\u{238C}-\u{2454}]|[\u{20D0}-\u{20FF}]|[\u{FE00}-\u{FE0F}]|[\u{1F004}]|[\u{1F0CF}]|[\u{1F170}-\u{1F251}]|[\u{1F004}-\u{1F0CF}]|[\u{1F100}-\u{1F1FF}]|[\u{2194}-\u{2199}]|[\u{21A9}-\u{21AA}]|[\u{231A}-\u{231B}]|[\u{2328}]|[\u{23CF}]|[\u{23E9}-\u{23F3}]|[\u{23F8}-\u{23FA}]|[\u{24C2}]|[\u{25AA}-\u{25AB}]|[\u{25B6}]|[\u{25C0}]|[\u{25FB}-\u{25FE}]|[\u{2600}-\u{2604}]|[\u{260E}]|[\u{2611}]|[\u{2614}-\u{2615}]|[\u{2618}]|[\u{261D}]|[\u{2620}]|[\u{2622}-\u{2623}]|[\u{2626}]|[\u{262A}]|[\u{262E}-\u{262F}]|[\u{2638}-\u{263A}]|[\u{2640}]|[\u{2642}]|[\u{2648}-\u{2653}]|[\u{2660}]|[\u{2663}]|[\u{2665}-\u{2666}]|[\u{2668}]|[\u{267B}]|[\u{267E}-\u{267F}]|[\u{2692}-\u{2697}]|[\u{2699}]|[\u{269B}-\u{269C}]|[\u{26A0}-\u{26A1}]|[\u{26AA}-\u{26AB}]|[\u{26B0}-\u{26B1}]|[\u{26BD}-\u{26BE}]|[\u{26C4}-\u{26C5}]|[\u{26C8}]|[\u{26CE}-\u{26CF}]|[\u{26D1}]|[\u{26D3}-\u{26D4}]|[\u{26E9}-\u{26EA}]|[\u{26F0}-\u{26F5}]|[\u{26F7}-\u{26FA}]|[\u{26FD}]|[\u{2702}]|[\u{2705}]|[\u{2708}-\u{270D}]|[\u{270F}]|[\u{2712}]|[\u{2714}]|[\u{2716}]|[\u{271D}]|[\u{2721}]|[\u{2728}]|[\u{2733}-\u{2734}]|[\u{2744}]|[\u{2747}]|[\u{274C}]|[\u{274E}]|[\u{2753}-\u{2755}]|[\u{2757}]|[\u{2763}-\u{2764}]|[\u{2795}-\u{2797}]|[\u{27A1}]|[\u{27B0}]|[\u{27BF}]|[\u{2934}-\u{2935}]|[\u{2B05}-\u{2B07}]|[\u{2B1B}-\u{2B1C}]|[\u{2B50}]|[\u{2B55}]|[\u{3030}]|[\u{303D}]|[\u{3297}]|[\u{3299}]/gu;
  
  // Also remove common text-based emoticons
  const textEmoticons = /:\)|:\(|:D|:P|;-?\)|8-?\)|:-?\||:-?\/|:-?\\|<3|:-?\*|:-?o|:-?O|>:-?\(|:-?\$|:-?@|:-?#|:-?\[|:-?\]/g;
  
  // Remove markdown emojis like :smile:, :thumbs_up:, etc.
  const markdownEmojis = /:[\w\+\-_]+:/g;
  
  // AGGRESSIVE removal of sources and references sections
  const sourcesPatterns = [
    // Various source section patterns
    /\*\*📚[\s\S]*?Sources?[\s\S]*?&?[\s\S]*?References?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    /\*\*Sources?[\s\S]*?&?[\s\S]*?References?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    /\*\*References?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    /\*\*Sources?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    
    // Document and chunk info
    /\*\*[\s\S]*?Chunks?[\s\S]*?Retrieved[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    /\*\*[\s\S]*?Document[\s\S]*?Sources?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    /\*\*[\s\S]*?Retrieved[\s\S]*?Documents?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    
    // Similarity and scores
    /\*\*[\s\S]*?Similarity[\s\S]*?Scores?[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
    /\([\s]*Score[\s]*:?[\s]*[\d.]+[\s]*\)/gi,
    /Score[\s]*:?[\s]*[\d.]+/gi,
    
    // Any line starting with bullet points containing technical terms
    /^[\s]*[-•*][\s]*.*(?:score|chunk|document|retrieval|similarity).*$/gmi,
    
    // Catch-all for remaining technical sections
    /\*\*[\s\S]*?(?:Retrieval|Source|Document)[\s\S]*?Info[\s\S]*?:?\*\*[\s\S]*?(?=\n\n|\n(?=[A-Z])|$)/gi,
  ];
  
  let cleaned = text;
  
  // Apply emoji removal
  cleaned = cleaned
    .replace(emojiRegex, '')
    .replace(textEmoticons, '')
    .replace(markdownEmojis, '');
  
  // Apply source removal patterns
  sourcesPatterns.forEach(pattern => {
    cleaned = cleaned.replace(pattern, '');
  });
  
  // Final cleanup - remove excessive whitespace and normalize
  cleaned = cleaned
    .replace(/\n\s*\n\s*\n+/g, '\n\n') // Multiple newlines to double newlines
    .replace(/^\s+|\s+$/g, '') // Trim whitespace from start and end
    .replace(/\s+/g, ' ') // Multiple spaces to single space
    .trim();
  
  return cleaned;
};

export const MarkdownText = memo(MarkdownTextImpl);

const CodeHeader: FC<CodeHeaderProps> = ({ language, code }) => {
  const { isCopied, copyToClipboard } = useCopyToClipboard();
  const onCopy = () => {
    if (!code || isCopied) return;
    copyToClipboard(code);
  };

  return (
    <div className="flex items-center justify-between gap-4 rounded-t-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white">
      <span className="lowercase [&>span]:text-xs">{language}</span>
      <TooltipIconButton tooltip="Copy" onClick={onCopy}>
        {!isCopied && <CopyIcon />}
        {isCopied && <CheckIcon />}
      </TooltipIconButton>
    </div>
  );
};

const useCopyToClipboard = ({
  copiedDuration = 3000,
}: {
  copiedDuration?: number;
} = {}) => {
  const [isCopied, setIsCopied] = useState<boolean>(false);

  const copyToClipboard = (value: string) => {
    if (!value) return;

    navigator.clipboard.writeText(value).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), copiedDuration);
    });
  };

  return { isCopied, copyToClipboard };
};

const defaultComponents = memoizeMarkdownComponents({
  h1: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <h1 className={cn("mb-8 scroll-m-20 text-4xl font-extrabold tracking-tight last:mb-0", className)} {...props}>
        {cleanChildren}
      </h1>
    );
  },
  h2: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <h2 className={cn("mb-4 mt-8 scroll-m-20 text-3xl font-semibold tracking-tight first:mt-0 last:mb-0", className)} {...props}>
        {cleanChildren}
      </h2>
    );
  },
  h3: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <h3 className={cn("mb-4 mt-6 scroll-m-20 text-2xl font-semibold tracking-tight first:mt-0 last:mb-0", className)} {...props}>
        {cleanChildren}
      </h3>
    );
  },
  h4: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <h4 className={cn("mb-4 mt-6 scroll-m-20 text-xl font-semibold tracking-tight first:mt-0 last:mb-0", className)} {...props}>
        {cleanChildren}
      </h4>
    );
  },
  h5: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <h5 className={cn("my-4 text-lg font-semibold first:mt-0 last:mb-0", className)} {...props}>
        {cleanChildren}
      </h5>
    );
  },
  h6: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <h6 className={cn("my-4 font-semibold first:mt-0 last:mb-0", className)} {...props}>
        {cleanChildren}
      </h6>
    );
  },
  p: ({ className, children, ...props }) => {
    // Remove emojis from text content
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <p className={cn("mb-5 mt-5 leading-7 first:mt-0 last:mb-0", className)} {...props}>
        {cleanChildren}
      </p>
    );
  },
  a: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <a className={cn("text-primary font-medium underline underline-offset-4", className)} {...props}>
        {cleanChildren}
      </a>
    );
  },
  blockquote: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <blockquote className={cn("border-l-2 pl-6 italic", className)} {...props}>
        {cleanChildren}
      </blockquote>
    );
  },
  ul: ({ className, ...props }) => (
    <ul className={cn("my-5 ml-6 list-disc [&>li]:mt-2", className)} {...props} />
  ),
  ol: ({ className, ...props }) => (
    <ol className={cn("my-5 ml-6 list-decimal [&>li]:mt-2", className)} {...props} />
  ),
  li: ({ className, children, ...props }) => {
    const cleanChildren = typeof children === 'string' ? removeEmojis(children) : children;
    return (
      <li className={className} {...props}>
        {cleanChildren}
      </li>
    );
  },
  hr: ({ className, ...props }) => (
    <hr className={cn("my-5 border-b", className)} {...props} />
  ),
  table: ({ className, ...props }) => (
    <table className={cn("my-5 w-full border-separate border-spacing-0 overflow-y-auto", className)} {...props} />
  ),
  th: ({ className, ...props }) => (
    <th className={cn("bg-muted px-4 py-2 text-left font-bold first:rounded-tl-lg last:rounded-tr-lg [&[align=center]]:text-center [&[align=right]]:text-right", className)} {...props} />
  ),
  td: ({ className, ...props }) => (
    <td className={cn("border-b border-l px-4 py-2 text-left last:border-r [&[align=center]]:text-center [&[align=right]]:text-right", className)} {...props} />
  ),
  tr: ({ className, ...props }) => (
    <tr className={cn("m-0 border-b p-0 first:border-t [&:last-child>td:first-child]:rounded-bl-lg [&:last-child>td:last-child]:rounded-br-lg", className)} {...props} />
  ),
  sup: ({ className, ...props }) => (
    <sup className={cn("[&>a]:text-xs [&>a]:no-underline", className)} {...props} />
  ),
  details: ({ className, ...props }) => (
    <details className={cn("my-4 rounded-lg border border-gray-200 bg-gray-50 dark:bg-gray-800 dark:border-gray-700 p-4 [&[open]>summary]:mb-4 [&>summary]:cursor-pointer transition-colors", className)} {...props} />
  ),
  summary: ({ className, ...props }) => (
    <summary className={cn(
      "cursor-pointer font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 select-none list-none",
      "[&::-webkit-details-marker]:hidden [&::marker]:hidden",
      "relative pl-6 before:content-['▶'] before:absolute before:left-0 before:transition-transform",
      "[details[open]>&]:before:rotate-90"
    , className)} {...props} />
  ),
  pre: ({ className, ...props }) => (
    <pre className={cn("overflow-x-auto rounded-b-lg bg-black p-4 text-white", className)} {...props} />
  ),
  code: function Code({ className, ...props }) {
    const isCodeBlock = useIsMarkdownCodeBlock();
    return (
      <code
        className={cn(!isCodeBlock && "bg-muted rounded border font-semibold", className)}
        {...props}
      />
    );
  },
  CodeHeader,
});
