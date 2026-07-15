"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, streamChat } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Send, Plus, Loader2, Bot, User, Sparkles, Brain, GitBranch, AlertTriangle, RefreshCw, Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import type { Conversation, Message, StreamEvent, AgentInfo, Memory, Decision } from "@/types";
import ReactMarkdown from "react-markdown";

function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [supported, setSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSupported(true);
      const recognition = new SpeechRecognition();
      recognition.lang = "zh-CN";
      recognition.interimResults = true;
      recognition.continuous = true;

      recognition.onresult = (event: any) => {
        let final = "";
        let interim = "";
        for (let i = 0; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        setTranscript(final + interim);
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        if (event.error !== "no-speech") {
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        if (recognitionRef.current?._shouldRestart) {
          try { recognition.start(); } catch {}
        } else {
          setIsListening(false);
        }
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = useCallback(() => {
    if (!recognitionRef.current) return;
    setTranscript("");
    recognitionRef.current._shouldRestart = true;
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch {}
  }, []);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    recognitionRef.current._shouldRestart = false;
    recognitionRef.current.stop();
    setIsListening(false);
  }, []);

  return { isListening, transcript, supported, startListening, stopListening };
}

function speakText(text: string, onEnd?: () => void) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const cleaned = text
    .replace(/[#*`>_~\[\]()]/g, "")
    .replace(/\n+/g, "。")
    .trim();
  if (!cleaned) return;

  const chunks = cleaned.match(/.{1,200}/g) || [cleaned];
  let index = 0;

  const speakNext = () => {
    if (index >= chunks.length) {
      onEnd?.();
      return;
    }
    const utterance = new SpeechSynthesisUtterance(chunks[index]);
    utterance.lang = "zh-CN";
    utterance.rate = 1.1;
    utterance.onend = () => {
      index++;
      speakNext();
    };
    utterance.onerror = () => {
      onEnd?.();
    };
    window.speechSynthesis.speak(utterance);
  };
  speakNext();
}

export default function ChatPage() {
  const queryClient = useQueryClient();
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [proposedTasks, setProposedTasks] = useState<string[]>([]);
  const [proposedMemories, setProposedMemories] = useState<string[]>([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const lastCompletedRef = useRef<string>("");

  const { isListening, transcript, supported: speechSupported, startListening, stopListening } = useSpeechRecognition();

  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  const { data: agents = [] } = useQuery({
    queryKey: ["agents"],
    queryFn: () => api.get<AgentInfo[]>("/api/agents"),
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.get<Conversation[]>("/api/conversations"),
  });

  const { data: messages = [] } = useQuery({
    queryKey: ["messages", activeConversation],
    queryFn: () =>
      activeConversation
        ? api.get<Message[]>(`/api/conversations/${activeConversation}/messages`)
        : Promise.resolve([]),
    enabled: !!activeConversation,
  });

  const { data: memories = [] } = useQuery({
    queryKey: ["memories-count"],
    queryFn: () => api.get<Memory[]>("/api/memories?status_filter=confirmed"),
  });

  const { data: decisions = [] } = useQuery({
    queryKey: ["decisions-count"],
    queryFn: () => api.get<Decision[]>("/api/decisions"),
  });

  useEffect(() => {
    if (autoSpeak && messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.sender_type === "agent" && lastMsg.content_text && lastMsg.id !== lastCompletedRef.current) {
        lastCompletedRef.current = lastMsg.id;
        setSpeakingId(lastMsg.id);
        speakText(lastMsg.content_text, () => setSpeakingId(null));
      }
    }
  }, [messages, autoSpeak]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, scrollToBottom]);

  const createConversation = useMutation({
    mutationFn: (agentId?: string | null) =>
      api.post<Conversation>("/api/conversations", {
        title: "新对话",
        conversation_type: "general",
        agent_id: agentId || selectedAgentId || undefined,
      }),
    onSuccess: (conv) => {
      setActiveConversation(conv.id);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const sendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    if (isListening) stopListening();

    let convId = activeConversation;
    if (!convId) {
      const conv = await createConversation.mutateAsync(selectedAgentId);
      convId = conv.id;
    }

    const userMessage = input.trim();
    setInput("");
    setIsStreaming(true);
    setStreamingText("");
    setProposedTasks([]);
    setProposedMemories([]);

    queryClient.setQueryData<Message[]>(["messages", convId], (old = []) => [
      ...old,
      {
        id: `temp-${Date.now()}`,
        conversation_id: convId!,
        sender_type: "user" as const,
        sender_id: null,
        content_text: userMessage,
        content_json: null,
        message_type: "text",
        model_provider: null,
        model_name: null,
        prompt_tokens: null,
        completion_tokens: null,
        latency_ms: null,
        created_at: new Date().toISOString(),
      },
    ]);

    try {
      for await (const event of streamChat(convId!, userMessage)) {
        const e = event as StreamEvent;
        switch (e.type) {
          case "text_delta":
            setStreamingText((prev) => prev + (e.content || ""));
            break;
          case "task_proposed":
            setProposedTasks(e.tasks || []);
            break;
          case "memory_proposed":
            setProposedMemories(e.memories || []);
            break;
          case "message_completed":
            queryClient.invalidateQueries({ queryKey: ["messages", convId] });
            queryClient.invalidateQueries({ queryKey: ["conversations"] });
            break;
          case "error":
            setStreamingText((prev) => prev + `\n\n⚠️ Error: ${e.error}`);
            break;
        }
      }
    } catch (err: any) {
      setStreamingText((prev) => prev + `\n\n⚠️ ${err.message}`);
    } finally {
      setIsStreaming(false);
      setStreamingText("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleSpeak = (msgId: string, text: string) => {
    if (speakingId === msgId) {
      window.speechSynthesis?.cancel();
      setSpeakingId(null);
    } else {
      setSpeakingId(msgId);
      speakText(text, () => setSpeakingId(null));
    }
  };

  const currentAgent = agents.find(a => a.id === selectedAgentId) || agents.find(a => a.agent_type === "ceo");

  return (
    <div className="flex h-screen">
      {/* Conversation list - desktop */}
      <div className={cn(
        "w-64 border-r bg-[hsl(var(--card))] flex-col",
        showSidebar ? "flex absolute inset-y-0 left-0 z-40 lg:relative" : "hidden lg:flex"
      )}>
        <div className="p-3 border-b flex items-center justify-between">
          <span className="text-sm font-medium">对话列表</span>
          <button
            onClick={() => {
              setActiveConversation(null);
              setShowSidebar(false);
            }}
            className="p-1.5 rounded-lg hover:bg-[hsl(var(--muted))] transition-colors"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-thin">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => {
                setActiveConversation(conv.id);
                setShowSidebar(false);
              }}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg text-sm transition-colors truncate",
                activeConversation === conv.id
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30"
                  : "hover:bg-[hsl(var(--muted))]"
              )}
            >
              {conv.title || "新对话"}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-14 border-b flex items-center px-4 gap-3 shrink-0">
          <button onClick={() => setShowSidebar(!showSidebar)} className="lg:hidden p-1">
            <Bot className="h-5 w-5 text-brand-600" />
          </button>
          <div>
            <p className="text-xs font-semibold tracking-wider uppercase text-brand-600">CEO Copilot</p>
            <h2 className="text-sm font-medium">AI 对话助手</h2>
          </div>
          <div className="ml-auto flex items-center gap-2">
            {/* Auto-speak toggle */}
            <button
              onClick={() => {
                if (autoSpeak) window.speechSynthesis?.cancel();
                setAutoSpeak(!autoSpeak);
              }}
              className={cn(
                "p-1.5 rounded-lg transition-colors",
                autoSpeak
                  ? "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
                  : "text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]"
              )}
              title={autoSpeak ? "关闭自动朗读" : "开启自动朗读回复"}
            >
              {autoSpeak ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            </button>
            <div className="w-px h-6 bg-[hsl(var(--border))]" />
            {agents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => setSelectedAgentId(agent.id)}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                  selectedAgentId === agent.id || (!selectedAgentId && agent.agent_type === "ceo")
                    ? "bg-brand-700 text-white"
                    : "bg-[hsl(var(--muted))] hover:bg-[hsl(var(--muted))]/80"
                )}
                title={`${agent.model_provider} / ${agent.model_name}`}
              >
                {agent.model_provider === "anthropic" ? "Claude" : "GPT-4o"}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
            {!activeConversation && messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-16 h-16 rounded-2xl bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center mb-4">
                  <Sparkles className="h-8 w-8 text-brand-600" />
                </div>
                <h3 className="text-lg font-semibold mb-2">AI 对话助手</h3>
                <p className="text-sm text-[hsl(var(--muted-foreground))] max-w-sm">
                  基于经营上下文，与 CEO Agent 讨论问题并形成下一步行动。
                </p>
                {speechSupported && (
                  <p className="text-xs text-brand-600 mt-3">
                    支持语音输入 — 点击麦克风按钮开始说话
                  </p>
                )}
                {currentAgent && (
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-2">
                    当前模型: {currentAgent.model_provider} / {currentAgent.model_name}
                  </p>
                )}
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className={cn("flex gap-3 group", msg.sender_type === "user" ? "justify-end" : "")}>
                {msg.sender_type !== "user" && (
                  <div className="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center shrink-0">
                    <Sparkles className="h-4 w-4 text-brand-600" />
                  </div>
                )}
                <div className="flex flex-col gap-1">
                  <div
                    className={cn(
                      "max-w-[75%] rounded-2xl px-4 py-2.5 text-sm",
                      msg.sender_type === "user"
                        ? "bg-brand-700 text-white"
                        : "bg-[hsl(var(--muted))]"
                    )}
                  >
                    {msg.sender_type === "user" ? (
                      <p className="whitespace-pre-wrap">{msg.content_text}</p>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown>{msg.content_text || ""}</ReactMarkdown>
                      </div>
                    )}
                  </div>
                  {msg.sender_type === "agent" && msg.content_text && (
                    <button
                      onClick={() => toggleSpeak(msg.id, msg.content_text!)}
                      className={cn(
                        "self-start flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full transition-colors",
                        speakingId === msg.id
                          ? "bg-brand-100 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
                          : "opacity-0 group-hover:opacity-100 text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]"
                      )}
                    >
                      <Volume2 className="h-3 w-3" />
                      {speakingId === msg.id ? "停止朗读" : "朗读"}
                    </button>
                  )}
                </div>
                {msg.sender_type === "user" && (
                  <div className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-gray-700 flex items-center justify-center shrink-0">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}

            {streamingText && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center shrink-0">
                  <Sparkles className="h-4 w-4 text-brand-600" />
                </div>
                <div className="max-w-[75%] rounded-2xl px-4 py-2.5 text-sm bg-[hsl(var(--muted))]">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{streamingText}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )}

            {isStreaming && !streamingText && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center shrink-0">
                  <Sparkles className="h-4 w-4 text-brand-600" />
                </div>
                <div className="rounded-2xl px-4 py-2.5 bg-[hsl(var(--muted))]">
                  <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
                </div>
              </div>
            )}

            {proposedTasks.length > 0 && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-3 text-sm">
                <p className="font-medium text-blue-700 dark:text-blue-400 mb-1">提取的任务:</p>
                {proposedTasks.map((t, i) => (
                  <p key={i} className="text-blue-600 dark:text-blue-300">• {t}</p>
                ))}
              </div>
            )}

            {proposedMemories.length > 0 && (
              <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-3 text-sm">
                <p className="font-medium text-purple-700 dark:text-purple-400 mb-1">建议保存的记忆:</p>
                {proposedMemories.map((m, i) => (
                  <p key={i} className="text-purple-600 dark:text-purple-300">• {m}</p>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Context Sidebar */}
          <div className="hidden xl:block w-72 border-l p-4 space-y-4 overflow-y-auto scrollbar-thin">
            <div className="p-4 rounded-xl bg-[hsl(var(--card))] border">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Bot className="h-4 w-4 text-brand-600" />
                本次对话上下文
              </h3>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[hsl(var(--muted-foreground))]">经营简报</span>
                  <span className="text-xs font-medium">
                    {new Date().getMonth()+1}月{new Date().getDate()}日
                  </span>
                </div>
                <div className="h-px bg-[hsl(var(--border))]" />
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[hsl(var(--muted-foreground))]">决策事项</span>
                  <span className="text-xs font-medium">{decisions.length} 条</span>
                </div>
                <div className="h-px bg-[hsl(var(--border))]" />
                <div className="flex items-center justify-between text-sm">
                  <span className="text-[hsl(var(--muted-foreground))]">长期记忆</span>
                  <span className="text-xs font-medium">{memories.length} 条相关</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-brand-900 dark:bg-brand-950 text-white">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-brand-300" />
                <span className="text-xs font-semibold text-brand-200">Agent 工作原则</span>
              </div>
              <p className="text-[11px] text-brand-300 leading-relaxed">
                结论前置，明确假设、风险与可选项。重要建议会引用经营数据和长期记忆依据。
              </p>
            </div>
          </div>
        </div>

        {/* Input */}
        <div className="border-t p-3 safe-area-bottom">
          {/* Voice recording indicator */}
          {isListening && (
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="flex items-center gap-1.5">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
                </span>
                <span className="text-xs text-red-600 font-medium">正在听...</span>
              </div>
              {transcript && (
                <span className="text-xs text-[hsl(var(--muted-foreground))] max-w-[200px] truncate">
                  {transcript}
                </span>
              )}
            </div>
          )}
          <div className="flex items-end gap-2 max-w-3xl mx-auto">
            {speechSupported && (
              <button
                onClick={isListening ? stopListening : startListening}
                className={cn(
                  "p-2.5 rounded-xl transition-colors shrink-0",
                  isListening
                    ? "bg-red-500 text-white hover:bg-red-600 animate-pulse"
                    : "bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))] hover:bg-brand-100 hover:text-brand-700"
                )}
                title={isListening ? "停止录音" : "语音输入"}
              >
                {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
              </button>
            )}
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isListening ? "正在听你说话..." : "向 CEO Agent 询问经营问题..."}
                rows={1}
                className="w-full resize-none rounded-xl border bg-transparent px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 max-h-32"
                style={{ minHeight: "42px" }}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isStreaming}
              className="p-2.5 rounded-xl bg-brand-700 text-white hover:bg-brand-800 disabled:opacity-50 transition-colors shrink-0"
            >
              {isStreaming ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
