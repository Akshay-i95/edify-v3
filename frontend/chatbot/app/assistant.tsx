"use client";

import { AssistantRuntimeProvider, AssistantCloud } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Separator } from "@/components/ui/separator";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { useEffect, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { ConversationStatus } from "@/components/conversation-status";

// Configure backend URL - ensure it's properly defined
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5000';

export const Assistant = () => {
  // Extract namespaces and role from URL parameters
  const searchParams = useSearchParams();
  const namespacesParam = searchParams.get('namespaces');
  const roleParam = searchParams.get('role');
  
  // Parse and normalize namespaces - support both kb-* and edipedia-* formats
  let finalNamespaces = null;
  if (namespacesParam) {
    const rawNamespaces = namespacesParam.split(',').map(ns => ns.trim().toLowerCase()).filter(Boolean);
    // Valid namespace patterns
    const validKbNamespaces = ['kb-psp', 'kb-msp', 'kb-ssp', 'kb-esp'];
    const validEdipediaNamespaces = ['edipedia-k12', 'edipedia-preschools', 'edipedia-edifyho'];
    const allValidNamespaces = [...validKbNamespaces, ...validEdipediaNamespaces];
    // Convert and include both kb-* and edipedia-* versions where applicable
    let processedNamespaces: string[] = [];
    for (const ns of rawNamespaces) {
      if (allValidNamespaces.includes(ns)) {
        processedNamespaces.push(ns);
      } else {
        switch (ns) {
          case 'psp':
          case 'primary':
            processedNamespaces.push('kb-psp');
            break;
          case 'msp':
          case 'middle':
            processedNamespaces.push('kb-msp');
            break;
          case 'ssp':
          case 'secondary':
            processedNamespaces.push('kb-ssp');
            break;
          case 'esp':
          case 'early':
            processedNamespaces.push('kb-esp');
            break;
          case 'k12':
            processedNamespaces.push('edipedia-k12');
            break;
          case 'preschool':
          case 'preschools':
            processedNamespaces.push('edipedia-preschools');
            break;
          case 'admin':
          case 'edifyho':
            processedNamespaces.push('edipedia-edifyho');
            break;
        }
      }
    }
    // Remove duplicates
    processedNamespaces = [...new Set(processedNamespaces)];
    // Enforce only one group/namespace at a time
    let selectedNamespace: string | null = null;
    // Priority: kb-* group if present, else edipedia-*
    for (const ns of processedNamespaces) {
      if (validKbNamespaces.includes(ns)) {
        selectedNamespace = ns;
        break;
      }
    }
    if (!selectedNamespace) {
      for (const ns of processedNamespaces) {
        if (validEdipediaNamespaces.includes(ns)) {
          selectedNamespace = ns;
          break;
        }
      }
    }
    finalNamespaces = selectedNamespace ? [selectedNamespace] : null;
  }

  // Validate role
  const validRoles = ['student', 'teacher', 'admin'];
  const userRole = roleParam && validRoles.includes(roleParam.toLowerCase()) ? roleParam.toLowerCase() : null;

  // Configure the cloud service
  const cloud = useMemo(() => {
    if (
      process.env.NEXT_PUBLIC_ASSISTANT_BASE_URL && 
      process.env.NEXT_PUBLIC_ASSISTANT_API_KEY && 
      process.env.NEXT_PUBLIC_ASSISTANT_WORKSPACE_ID
    ) {
      return new AssistantCloud({
        baseUrl: process.env.NEXT_PUBLIC_ASSISTANT_BASE_URL,
        apiKey: process.env.NEXT_PUBLIC_ASSISTANT_API_KEY,
        workspaceId: process.env.NEXT_PUBLIC_ASSISTANT_WORKSPACE_ID,
        userId: "default-user", // Use a default user ID
      });
    }
    return undefined;
  }, []);

  // Create dynamic API URL with namespaces and role
  const queryParams = [];
  if (finalNamespaces) {
    queryParams.push(`namespaces=${finalNamespaces.join(',')}`);
  }
  if (userRole) {
    queryParams.push(`role=${userRole}`);
  }
  const apiUrl = queryParams.length > 0 ? `/api/chat?${queryParams.join('&')}` : '/api/chat';
  
  const runtime = useChatRuntime({
    api: apiUrl,
    cloud: cloud,
  });

  // Debug cloud and backend connections
  useEffect(() => {
    console.log("Environment Setup:", {
      backendUrl: BACKEND_URL,
      namespaces: finalNamespaces || 'auto-detect',
      apiUrl: apiUrl,
      cloudConfig: {
        baseUrl: process.env.NEXT_PUBLIC_ASSISTANT_BASE_URL,
        hasApiKey: !!process.env.NEXT_PUBLIC_ASSISTANT_API_KEY,
        workspaceId: process.env.NEXT_PUBLIC_ASSISTANT_WORKSPACE_ID,
        cloudConfigured: !!cloud,
      }
    });
    
    // Add backend URL to window for components to access
    window.BACKEND_URL = BACKEND_URL;
  }, [cloud, finalNamespaces, apiUrl]);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="flex h-screen flex-col overflow-hidden">
          {/* Clean header with Breadcrumb navigation matching ref-ui */}
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbPage>Edify Assistant</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </header>
          {/* Main content with proper height and overflow handling */}
          <div className="flex flex-1 flex-col overflow-hidden p-4">
            <Thread />
          </div>
        </SidebarInset>
      </SidebarProvider>
    </AssistantRuntimeProvider>
  );
};

// Add type declaration for window object
declare global {
  interface Window {
    BACKEND_URL?: string;
  }
}
