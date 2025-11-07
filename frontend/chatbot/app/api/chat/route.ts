export const runtime = "edge";
export const maxDuration = 30;

export async function POST(req: Request) {
  try {
    // Extract namespaces and role from URL parameters
    const url = new URL(req.url);
    const namespacesParam = url.searchParams.get('namespaces');
    const roleParam = url.searchParams.get('role');
    
    // Parse and normalize namespaces - support both kb-* and edipedia-* formats
    let namespaces = null;
    if (namespacesParam) {
      const rawNamespaces = namespacesParam.split(',').map(ns => ns.trim().toLowerCase()).filter(Boolean);
      const validKbNamespaces = ['kb-psp', 'kb-msp', 'kb-ssp', 'kb-esp'];
      const validEdipediaNamespaces = ['edipedia-k12', 'edipedia-preschools', 'edipedia-edifyho'];
      const allValidNamespaces = [...validKbNamespaces, ...validEdipediaNamespaces];
      let processedNamespaces = [];
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
      processedNamespaces = [...new Set(processedNamespaces)];
      // Enforce only one group/namespace at a time
      let selectedNamespace = null;
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
      namespaces = selectedNamespace ? [selectedNamespace] : null;
    }
    const role = roleParam ? roleParam.trim().toLowerCase() : null;
    
    console.log('🏷️ Extracted namespaces from URL:', namespaces);
    console.log('👤 Extracted role from URL:', role);
    
    const requestBody = await req.json();
    console.log('🔍 Full request body:', JSON.stringify(requestBody, null, 2));
    
    // Handle messages array format (Assistant-UI/OpenAI standard)
    let messages;
    let messageContent = '';
    
    if (requestBody.messages && Array.isArray(requestBody.messages)) {
      // Standard format: { messages: [...] }
      messages = requestBody.messages;
      console.log('📝 Messages array format detected, length:', messages.length);
      
      // Extract the latest user message
      const userMessage = messages[messages.length - 1];
      console.log('👤 User message:', JSON.stringify(userMessage, null, 2));
      
      if (!userMessage || userMessage.role !== 'user') {
        console.log('❌ Invalid message format - userMessage:', userMessage);
        return new Response(JSON.stringify({error: 'Invalid message format'}), { 
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        });
      }

      // Extract text content from the message (handle both string and array formats)
      if (typeof userMessage.content === 'string') {
        messageContent = userMessage.content;
        console.log('📝 String content detected:', messageContent);
      } else if (Array.isArray(userMessage.content)) {
        console.log('📝 Array content detected, searching for text...');
        // Handle assistant-ui format with content array
        const textPart = userMessage.content.find((part: any) => part.type === 'text');
        console.log('📝 Found text part:', JSON.stringify(textPart, null, 2));
        
        if (textPart) {
          // Try different possible text fields
          messageContent = textPart.text || textPart.content || '';
          console.log('📝 Extracted text from part:', messageContent);
        } else {
          console.log('❌ No text part found in content array');
          messageContent = '';
        }
      } else {
        messageContent = String(userMessage.content);
        console.log('📝 Other content format, converted to string:', messageContent);
      }
    } else {
      console.log('❌ Invalid request format - expected messages array');
      return new Response(JSON.stringify({error: 'Expected messages array format'}), { 
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    console.log('💬 Final extracted message content:', JSON.stringify(messageContent));

    if (!messageContent || !messageContent.trim()) {
      console.log('❌ Empty message content after extraction');
      return new Response(JSON.stringify({error: 'Message content is required'}), { 
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Limit message history to prevent token overflow (keep last 20 messages)
    const limitMessages = (msgs: any[], maxMessages = 20) => {
      if (msgs.length <= maxMessages) return msgs;
      
      // Keep system message + recent messages
      const systemMessage = msgs.find((m: any) => m.role === 'system');
      const recentMessages = msgs.slice(-maxMessages + 1);
      
      return systemMessage ? [systemMessage, ...recentMessages] : recentMessages;
    };

    const limitedMessages = limitMessages(messages);
    console.log(`📝 Message history: ${messages.length} total, ${limitedMessages.length} after limiting`);

    // Convert full conversation history to backend format
    const conversationHistory = limitedMessages
      .slice(0, -1) // Exclude current message
      .map((msg: any) => {
        // Convert to format expected by backend
        let content = '';
        if (typeof msg.content === 'string') {
          content = msg.content;
        } else if (Array.isArray(msg.content)) {
          const textPart = msg.content.find((part: any) => part.type === 'text');
          content = textPart?.text || '';
        }
        
        return {
          role: msg.role,
          content: content
        };
      });
    
    console.log(`💬 Sending full conversation context: ${conversationHistory.length} previous messages`);

    // Generate consistent thread_id for conversation continuity
    // Use a hash of the first user message to ensure same conversation gets same thread_id
    const firstUserMessage = messages.find((m: any) => m.role === 'user');
    const threadSeed = firstUserMessage ? JSON.stringify(firstUserMessage.content).slice(0, 50) : 'default';
    const threadId = 'ui_thread_' + Buffer.from(threadSeed).toString('base64').slice(0, 8).replace(/[^a-zA-Z0-9]/g, '');
    
    // Get backend URL properly for Edge runtime
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:5000';
    console.log('Using backend URL:', backendUrl);
    console.log('🧵 Generated thread_id:', threadId);
    
    // Send message to backend endpoint with full conversation history and role
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: messageContent,
        messages: conversationHistory, // Send full conversation history as messages array
        thread_id: threadId, // Add thread_id for conversation continuity
        role: role,
        namespaces: namespaces
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    const aiResponse = data.response;
    
    // Extract metadata from response
    const metadata = data.metadata || {};
    
    // Try getting reasoning from both places (direct field or metadata)
    const reasoning = data.reasoning || metadata.reasoning || '';
    const sources = metadata.sources || [];
    
    // Log sources count for debugging
    console.log(`📁 Sources received from backend:`, sources.length);
    if (sources.length > 0) {
      console.log(`📁 Source titles:`, sources.map((s: any, i: number) => `${i+1}. ${s.title || s.filename}`));
    }
    
    const confidence = metadata.confidence || 0;
    const isFollowUp = metadata.is_follow_up || false;
    const followUpContext = metadata.follow_up_context || null;
    
    // Log reasoning data for debugging
    console.log(`🧠 Backend reasoning data:`, {
      direct_reasoning: data.reasoning ? data.reasoning.substring(0, 100) + '...' : 'NONE',
      metadata_reasoning: metadata.reasoning ? metadata.reasoning.substring(0, 100) + '...' : 'NONE',
      final_reasoning: reasoning ? reasoning.substring(0, 100) + '...' : 'NONE',
      has_reasoning: data.has_reasoning,
      reasoning_length: reasoning?.length || 0
    });
    
    if (reasoning) {
      console.log(`🧠 Full reasoning content: ${reasoning}`);
    } else {
      console.log(`❌ No reasoning content found in backend response`);
    }

    // Create AI SDK compatible streaming response with structured content
    const encoder = new TextEncoder();
    
    // Capture role for use in streaming function
    const requestRole = role;
    
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Helper function to safely encode and send chunks
          const sendChunk = async (text: string, delay: number = 30) => {
            if (controller.desiredSize === null) return; // Controller is closed
            
            // Properly escape the text for JSON - handle all cases safely
            const escapedText = JSON.stringify(text).slice(1, -1); // Use JSON.stringify and remove outer quotes
            
            const chunk = `0:"${escapedText}"\n`;
            controller.enqueue(encoder.encode(chunk));
            
            if (delay > 0) {
              await new Promise(resolve => setTimeout(resolve, delay));
            }
          };
          
          // 1. Add follow-up context if this is a follow-up query
          if (isFollowUp && followUpContext) {
            if (followUpContext.previous_topic) {
              await sendChunk(`*Building on our previous discussion about ${followUpContext.previous_topic.substring(0, 50)}...*\n\n`, 50);
            }
          }
          
          // 2. Add reasoning section first with ChatGPT-style collapsible dropdown
          if (reasoning?.trim()) {
            console.log('🧠 Adding reasoning to response, length:', reasoning.length, 'characters');
            console.log('🧠 Raw reasoning content (first 800 chars):', reasoning.substring(0, 800));
            
            // Process reasoning content for better structure
            let processedReasoning = reasoning.trim();
            
            // First, protect existing HTML/structured content by converting line breaks to placeholders
            const lines = processedReasoning.split('\n');
            let formattedLines: string[] = [];
            
            console.log('🧠 Total lines in reasoning:', lines.length);
            
            // Track which steps we've found
            const stepsFound: number[] = [];
            
            for (let i = 0; i < lines.length; i++) {
              const line = lines[i];
              const trimmedLine = line.trim();
              
              if (!trimmedLine) {
                // Empty line - add spacing
                formattedLines.push('<div style="height: 8px;"></div>');
                continue;
              }
              
              // Check for numbered steps with multiple patterns
              const numberMatch = trimmedLine.match(/^(\d+)[\.\)\:]\s+/);
              if (numberMatch) {
                const stepNum = parseInt(numberMatch[1]);
                stepsFound.push(stepNum);
                console.log(`🧠 Found step ${stepNum} at line ${i}:`, trimmedLine.substring(0, 100));
              }
              
              // Convert markdown-style headers to HTML
              if (trimmedLine.startsWith('### ')) {
                formattedLines.push(`<div style="font-weight: 600; font-size: 15px; color: #10a37f; margin: 16px 0 8px 0;">${trimmedLine.substring(4)}</div>`);
              } else if (trimmedLine.startsWith('## ')) {
                formattedLines.push(`<div style="font-weight: 600; font-size: 16px; color: #0d8f6b; margin: 18px 0 10px 0;">${trimmedLine.substring(3)}</div>`);
              } else if (trimmedLine.startsWith('# ')) {
                formattedLines.push(`<div style="font-weight: 700; font-size: 17px; color: #0a7a5c; margin: 20px 0 12px 0;">${trimmedLine.substring(2)}</div>`);
              }
              // Convert numbered lists (1., 2., 3., etc.) - More flexible pattern
              else if (/^\d+[\.\)\:]\s+/.test(trimmedLine)) {
                const match = trimmedLine.match(/^(\d+)[\.\)\:]\s+(.*)$/);
                if (match) {
                  const [, number, content] = match;
                  
                  // Skip if content is empty
                  if (!content || !content.trim()) {
                    formattedLines.push(`<div style="margin-left: 20px; padding: 8px 12px; border-left: 3px solid #10a37f; margin-top: 8px; margin-bottom: 8px; background: rgba(16, 163, 127, 0.03);"><span style="font-weight: 700; color: #10a37f; font-size: 15px;">${number}.</span></div>`);
                    continue;
                  }
                  
                  // Process inline formatting in content
                  let formattedContent = content
                    .replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight: 600; color: #1f2937;">$1</strong>')
                    .replace(/\*(.+?)\*/g, '<em style="font-style: italic; color: #4b5563;">$1</em>')
                    .replace(/`(.+?)`/g, '<code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #e11d48;">$1</code>');
                  
                  formattedLines.push(`<div style="margin-left: 20px; padding: 8px 12px; border-left: 3px solid #10a37f; margin-top: 8px; margin-bottom: 8px; background: rgba(16, 163, 127, 0.03);"><span style="font-weight: 700; color: #10a37f; font-size: 15px;">${number}.</span> <span style="color: #1f2937;">${formattedContent}</span></div>`);
                  console.log(`✅ Formatted step ${number}`);
                }
              }
              // Convert bullet points
              else if (/^[\-\*]\s+/.test(trimmedLine)) {
                const content = trimmedLine.substring(2);
                let formattedContent = content
                  .replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight: 600; color: #1f2937;">$1</strong>')
                  .replace(/\*(.+?)\*/g, '<em style="font-style: italic; color: #4b5563;">$1</em>')
                  .replace(/`(.+?)`/g, '<code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #e11d48;">$1</code>');
                
                formattedLines.push(`<div style="margin-left: 20px; padding-left: 12px; border-left: 2px solid #e5e7eb; margin-top: 6px; margin-bottom: 6px; color: #374151;">• ${formattedContent}</div>`);
              }
              // Regular text with inline formatting
              else {
                let formattedContent = trimmedLine
                  .replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight: 600; color: #1f2937;">$1</strong>')
                  .replace(/\*(.+?)\*/g, '<em style="font-style: italic; color: #4b5563;">$1</em>')
                  .replace(/`(.+?)`/g, '<code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #e11d48;">$1</code>');
                
                formattedLines.push(`<div style="margin: 6px 0; color: #374151; line-height: 1.6;">${formattedContent}</div>`);
              }
            }
            
            processedReasoning = formattedLines.join('');
            console.log('🧠 Processed reasoning HTML length:', processedReasoning.length);
            console.log('🧠 Steps found:', stepsFound.sort((a, b) => a - b));
            
            // Warn if step 1 or 2 is missing
            if (stepsFound.length > 0) {
              if (!stepsFound.includes(1)) {
                console.warn('⚠️ Step 1 is missing from reasoning!');
              }
              if (!stepsFound.includes(2) && stepsFound.length > 1) {
                console.warn('⚠️ Step 2 is missing from reasoning!');
              }
            }
            
            // Create a simple collapsible reasoning section (similar to thinking dots)
            const reasoningHtml = `
<style>
  .simple-reasoning-summary {
    padding: 8px 0;
    cursor: pointer;
    font-size: 14px;
    color: #6b7280;
    display: flex;
    align-items: center;
    gap: 8px;
    user-select: none;
    border: none;
    outline: none;
    transition: all 0.2s ease;
  }
  .simple-reasoning-summary:hover {
    color: #374151;
  }
  .simple-reasoning-chevron {
    color: #9ca3af;
    transition: transform 0.2s ease;
    transform: rotate(0deg);
    width: 12px;
    height: 12px;
  }
  .simple-reasoning-details[open] .simple-reasoning-chevron {
    transform: rotate(90deg);
  }
  .simple-reasoning-content {
    padding: 12px 0 12px 20px;
    border-left: 2px solid #e5e7eb;
    margin-left: 6px;
  }
</style>
<details class="simple-reasoning-details" style="
  margin: 16px 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
">
  <summary class="simple-reasoning-summary">
    <svg class="simple-reasoning-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <polyline points="9,18 15,12 9,6"/>
    </svg>
    <span>Thinking</span>
  </summary>
  <div class="simple-reasoning-content" style="
    font-size: 14px;
    line-height: 1.7;
    color: #374151;
  ">${processedReasoning}</div>
</details>

<style>
details[open] summary svg:first-of-type {
  transform: rotate(90deg) !important;
}
details summary::-webkit-details-marker {
  display: none;
}
details summary::marker {
  content: "";
}
</style>`;
            
            await sendChunk(reasoningHtml, 30);
          }
          
          // 3. Stream the main AI response (the actual answer)
          const words = aiResponse.split(' ');
          for (let i = 0; i < words.length; i++) {
            if (controller.desiredSize === null) break; // Controller is closed
            
            const word = words[i] + (i < words.length - 1 ? ' ' : '');
            await sendChunk(word, 20);
          }
          
          // 4. Add videos section if there are any video sources
          const videoSources = sources.filter((source: any) => 
            source.video_url || 
            (source.filename && source.filename.toLowerCase().endsWith('.mp4')) ||
            source.media_type === 'video'
          );
          
          if (videoSources.length > 0) {
            console.log('🎥 Adding video section, count:', videoSources.length);
            
            await sendChunk('\n\n---\n\n', 50);
            await sendChunk('### 🎥 Related Videos\n\n', 50);
            
            for (let i = 0; i < videoSources.length; i++) {
              const video = videoSources[i];
              
              // Extract video title
              let videoTitle = 'Educational Video';
              if (video.title && video.title !== video.filename) {
                videoTitle = video.title;
              } else if (video.filename) {
                // Clean up filename for display
                videoTitle = video.filename
                  .replace(/\.[^/.]+$/, '') // Remove extension
                  .replace(/[_-]/g, ' ') // Replace underscores/hyphens with spaces
                  .replace(/([a-f0-9\-]{8,})/gi, '') // Remove UUID-like strings
                  .trim();
                
                if (!videoTitle || videoTitle.length < 3) {
                  videoTitle = `Educational Video ${i + 1}`;
                }
              }
              
              // Get video URL - try multiple sources
              let videoUrl = video.video_url;
              if (!videoUrl && video.filename) {
                // Construct Azure Blob Storage URL
                const storageAccount = 'edifystorageaccount';
                const containerName = 'edifydocumentcontainer';
                videoUrl = `https://${storageAccount}.blob.core.windows.net/${containerName}/${video.filename}`;
              }
              
              if (videoUrl) {
                // Create video player HTML
                const videoHtml = `
<div style="
  margin: 20px 0;
  padding: 20px;
  border: 1px solid #e1e5e9;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
">
  <div style="
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e9ecef;
  ">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2" style="flex-shrink: 0;">
      <polygon points="5,3 19,12 5,21 5,3"/>
    </svg>
    <h4 style="
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #2c3e50;
      line-height: 1.3;
    ">${videoTitle}</h4>
  </div>
  
  <div style="
    position: relative;
    width: 100%;
    max-width: 640px;
    margin: 0 auto;
  ">
    <video 
      controls 
      preload="metadata"
      style="
        width: 100%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      "
      onloadstart="console.log('Video loading started')"
      onerror="console.error('Video failed to load:', this.src)"
    >
      <source src="${videoUrl}" type="video/mp4">
      <p style="
        padding: 20px;
        text-align: center;
        color: #6c757d;
        background: #f8f9fa;
        border-radius: 6px;
        margin: 10px 0;
      ">
        Your browser doesn't support video playback. 
        <a href="${videoUrl}" style="color: #007bff; text-decoration: none;">Download the video</a>
      </p>
    </video>
  </div>
  
  <div style="
    margin-top: 12px;
    padding: 12px;
    background: rgba(13, 110, 253, 0.05);
    border: 1px solid rgba(13, 110, 253, 0.2);
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
  ">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d6efd" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <path d="m15,9-6,3.5 6,3.5z"/>
    </svg>
    <span style="
      font-size: 14px;
      color: #0d6efd;
      font-weight: 500;
    ">Click play to watch this educational content</span>
  </div>
</div>`;
                
                await sendChunk(videoHtml, 100);
                
                // Add video description if available
                if (video.excerpt || video.description) {
                  const description = video.excerpt || video.description;
                  await sendChunk(`\n*${description.substring(0, 200)}${description.length > 200 ? '...' : ''}*\n\n`, 30);
                }
              }
            }
          }
          
          // 5. Add sources section last (supporting documents) - ONLY for admin role
          const showSources = requestRole === 'admin';
          console.log('👤 Role check for sources:', { 
            role: requestRole, 
            showSources: showSources, 
            sourcesLength: sources.length 
          });
          
          if (sources.length > 0 && showSources) {
            console.log('📁 Adding sources to response (admin role only), count:', sources.length);
            
            await sendChunk('\n\n---\n\n', 50);
            await sendChunk('### 📁 Source Documents\n\n', 50);
            
            for (let i = 0; i < sources.length; i++) {
              const source = sources[i];
              
              // Better title extraction with fallbacks
              let title = 'Unknown Document';
              
              // Try to get title from various fields
              if (source.title && source.title !== source.filename) {
                title = source.title;
              } else if (source.document_title) {
                title = source.document_title;
              } else if (source.name) {
                title = source.name;
              } else if (source.filename) {
                // Clean up filename if it looks like a UUID
                if (source.filename.match(/^[a-f0-9\-\s]+$/i)) {
                  title = `Document ${i + 1}`;
                } else {
                  // Remove file extension and clean filename
                  title = source.filename.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
                }
              } else {
                title = `Document ${i + 1}`;
              }
              
              const actualBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:5000';
              
              // Generate download URL if not provided
              let downloadUrl = source.download_url;
              if (!downloadUrl || !downloadUrl.startsWith('http')) {
                downloadUrl = `${actualBackendUrl}/api/files/download/${encodeURIComponent(source.filename || '')}`;
              }
              
              // Add source as markdown with proper formatting
              await sendChunk(`**${i + 1}. ${title}**\n`, 20);
              
              if (source.excerpt) {
                const excerpt = source.excerpt.substring(0, 150) + (source.excerpt.length > 150 ? '...' : '');
                await sendChunk(`*${excerpt}*\n`, 10);
              } else if (source.department || source.sub_department) {
                const deptInfo = [source.department, source.sub_department].filter(Boolean).join(' › ');
                await sendChunk(`*Department: ${deptInfo}*\n`, 10);
              }
              
              await sendChunk(`[📄 Download PDF](${downloadUrl})\n\n`, 30);
            }
          }
          
          // Send finish signal only if controller is still open
          if (controller.desiredSize !== null) {
            const finishChunk = `d:{"finishReason":"stop","usage":{"promptTokens":0,"completionTokens":0}}\n`;
            controller.enqueue(encoder.encode(finishChunk));
            controller.close();
          }
          
        } catch (error) {
          console.error('Error in stream controller:', error);
          if (controller.desiredSize !== null) {
            controller.error(error);
          }
        }
      },
      
      cancel() {
        console.log('Stream cancelled by client');
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    console.error('Error in chat API:', error);
    
    // Return error using AI SDK format
    const encoder = new TextEncoder();
    const errorMessage = 'I apologize, but I encountered an error while processing your request. Please try again.';
    
    const errorStream = new ReadableStream({
      async start(controller) {
        try {
          // Safely escape error message
          const escapedError = errorMessage
            .replace(/\\/g, '\\\\')
            .replace(/"/g, '\\"')
            .replace(/\n/g, '\\n');
          
          const errorChunk = `0:"${escapedError}"\n`;
          controller.enqueue(encoder.encode(errorChunk));
          
          // Send completion
          const finishChunk = `d:{"finishReason":"error","usage":{"promptTokens":0,"completionTokens":0}}\n`;
          controller.enqueue(encoder.encode(finishChunk));
          
          controller.close();
        } catch (error) {
          console.error('Error in error stream controller:', error);
          if (controller.desiredSize !== null) {
            controller.error(error);
          }
        }
      }
    });

    return new Response(errorStream, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }
}
