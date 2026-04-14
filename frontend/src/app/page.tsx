"use client";

import { useState } from "react";
import { MessageSquare, BarChart3, Settings2, Sparkles, Send, Image as ImageIcon, Loader2 } from "lucide-react";
import MbtiChart from "@/components/MbtiChart";
import { post, uploadImage } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"analysis" | "chat">("analysis");
  
  // Analysis State
  const [formData, setFormData] = useState({
    my_mbti: "ENTJ",
    target_mbti_input: "자동 분석 (AI)",
    situation: "일상 대화",
    relationship: "친구",
    vibe: "호감/긍정적 😊",
    context_detail: "",
    target_text: "",
  });
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");
  const [ocrLoading, setOcrLoading] = useState(false);

  // Chat State
  const [chatSettings, setChatSettings] = useState({
    user_mbti: "ENTJ",
    target_mbti: "INFP",
    relationship: "직장 동료/상사",
    situation: "업무 지시를 받는 중이거나 피드백을 요구하는 상황",
    ai_first: true,
  });
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [coachingTip, setCoachingTip] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [reactionMsg, setReactionMsg] = useState("");

  const handleAnalysisSubmit = async () => {
    setLoading(true);
    setLoadingStatus("메시지 속 성향 분석 중...");
    try {
      setTimeout(() => setLoadingStatus("최적의 답변 레시피 생성 중..."), 2000);
      const result = await post("/analyze", formData);
      setLoadingStatus("완료!");
      setAnalysisResult(result);
    } catch (error: any) {
      alert(error.message);
    } finally {
      setLoading(false);
      setLoadingStatus("");
    }
  };

  const handleImageOCR = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    setOcrLoading(true);
    try {
      const result = await uploadImage(e.target.files[0]);
      setFormData({ ...formData, target_text: result.text });
    } catch (error: any) {
      alert("이미지 읽기 실패: " + error.message);
    } finally {
      setOcrLoading(false);
    }
  };

  const startChat = async () => {
    setChatLoading(true);
    try {
      const result = await post("/chat/start", chatSettings);
      setChatHistory(result.history);
      setCoachingTip(result.coaching_tip);
    } catch (error: any) {
      alert(error.message);
    } finally {
      setChatLoading(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    setChatLoading(true);
    const userInput = chatInput;
    setChatInput("");
    try {
      const result = await post("/chat", {
        ...chatSettings,
        history: chatHistory,
        user_input: userInput,
      });
      setChatHistory(result.history);
      setCoachingTip(result.coaching_tip);
    } catch (error: any) {
      alert(error.message);
    } finally {
      setChatLoading(false);
    }
  };

  const simulateReaction = async () => {
    if (!analysisResult?.advice) return;
    setLoading(true);
    try {
      const result = await post("/simulate", {
        my_mbti: formData.my_mbti,
        target_mbti_input: analysisResult.analysis_summary.includes("기 분석 결과") ? "자동 분석" : formData.target_mbti_input,
        situation: formData.situation,
        relationship: formData.relationship,
        advice_text: analysisResult.advice,
      });
      setReactionMsg(result.reaction);
    } catch (error: any) {
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="premium-gradient rounded-2xl p-8 mb-8 text-white shadow-xl animate-fade-in">
        <h1 className="text-4xl font-extrabold mb-2 flex items-center gap-3">
          <Sparkles className="w-8 h-8" />
          CommuniKate: MBTI 소통 전문가
        </h1>
        <p className="text-white/80 text-lg">
          정밀 성향 분석과 AI 코칭으로 당신의 대화를 최적화합니다.
        </p>
      </header>

      {/* Tabs */}
      <div className="flex gap-4 mb-8 bg-white/50 dark:bg-slate-900/50 p-1 rounded-xl w-fit glass">
        <button
          onClick={() => setActiveTab("analysis")}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-all ${
            activeTab === "analysis" ? "bg-white dark:bg-slate-800 shadow-sm text-indigo-600" : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <BarChart3 className="w-5 h-5" />
          분석 및 조언
        </button>
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-all ${
            activeTab === "chat" ? "bg-white dark:bg-slate-800 shadow-sm text-indigo-600" : "text-slate-500 hover:text-slate-700"
          }`}
        >
          <MessageSquare className="w-5 h-5" />
          연습하기 (AI 채팅)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {activeTab === "analysis" ? (
          <>
            {/* Analysis Inputs */}
            <div className="lg:col-span-4 space-y-6">
              <section className="card space-y-4">
                <h2 className="text-xl font-bold flex items-center gap-2 border-b pb-2">
                  <Settings2 className="w-5 h-5 text-indigo-500" />
                  설정 및 입력
                </h2>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-500">나의 MBTI</label>
                    <select 
                      value={formData.my_mbti}
                      onChange={(e) => setFormData({...formData, my_mbti: e.target.value})}
                      className="w-full p-2 rounded-lg border bg-white dark:bg-slate-800 outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"].map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-500">상대방 MBTI</label>
                    <select 
                      value={formData.target_mbti_input}
                      onChange={(e) => setFormData({...formData, target_mbti_input: e.target.value})}
                      className="w-full p-2 rounded-lg border bg-white dark:bg-slate-800 outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="자동 분석 (AI)">메시지로 분석하기</option>
                      {["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"].map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-500">대화 상황</label>
                  <select 
                    value={formData.situation}
                    onChange={(e) => setFormData({...formData, situation: e.target.value})}
                    className="w-full p-2 rounded-lg border bg-white dark:bg-slate-800 outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {["처음 만난 사이 (Ice-breaking)", "비즈니스 미팅", "갈등 상황", "호감 표현", "일상 대화"].map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-500">메시지 내용</label>
                  <textarea 
                    value={formData.target_text}
                    onChange={(e) => setFormData({...formData, target_text: e.target.value})}
                    placeholder="상대방이 보낸 메시지를 입력하거나 이미지를 업로드하세요."
                    className="w-full p-3 rounded-lg border bg-white dark:bg-slate-800 outline-none focus:ring-2 focus:ring-indigo-500 h-32 resize-none"
                  />
                </div>

                <div className="space-y-3 pt-2">
                  <button 
                    onClick={handleAnalysisSubmit}
                    disabled={loading}
                    className="w-full btn-primary bg-indigo-600 py-4 shadow-lg shadow-indigo-200 dark:shadow-none"
                  >
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                    분석 및 조언 받기
                  </button>
                  
                  <label className="block">
                    <div className="btn-secondary cursor-pointer flex items-center justify-center gap-2 py-3 border-dashed border-2 hover:border-indigo-400 hover:text-indigo-600 transition-all">
                      {ocrLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImageIcon className="w-4 h-4" />}
                      대화 캡처본 불러오기
                    </div>
                    <input type="file" className="hidden" accept="image/*" onChange={handleImageOCR} />
                  </label>
                </div>
              </section>
            </div>

            {/* Analysis Results */}
            <div className="lg:col-span-8 space-y-6 relative">
              {loading && (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/60 dark:bg-slate-900/60 backdrop-blur-sm rounded-2xl animate-fade-in">
                  <div className="bg-white dark:bg-slate-800 p-8 rounded-2xl shadow-2xl border flex flex-col items-center gap-4">
                    <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
                    <div className="text-center">
                      <p className="font-bold text-lg text-slate-800 dark:text-white">{loadingStatus}</p>
                      <p className="text-sm text-slate-500 mt-1">AI가 최적의 커뮤니케이션 전략을 짜고 있습니다...</p>
                    </div>
                  </div>
                </div>
              )}
              {analysisResult ? (
                <div className="animate-fade-in space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="card">
                      <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-emerald-500" />
                        분석 리포트
                      </h3>
                      <div className="prose prose-sm dark:prose-invert max-w-none mb-4 whitespace-pre-wrap">
                        {analysisResult.analysis_summary}
                      </div>
                      <MbtiChart data={analysisResult.axis_scores} />
                    </div>
                    
                    <div className="card bg-indigo-50/50 dark:bg-indigo-900/10 border-indigo-100 dark:border-indigo-900/50">
                      <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-indigo-600 dark:text-indigo-400">
                        <Sparkles className="w-5 h-5" />
                        솔루션 조언
                      </h3>
                      <div className="prose prose-indigo dark:prose-invert max-w-none whitespace-pre-wrap leading-relaxed">
                        {analysisResult.advice}
                      </div>
                      
                      <button 
                        onClick={simulateReaction}
                        className="mt-6 w-full btn-secondary text-indigo-600 border-indigo-200 bg-white"
                      >
                         🎭 상대방 반응 시뮬레이션
                      </button>
                    </div>
                  </div>

                  {reactionMsg && (
                    <div className="card border-amber-200 bg-amber-50/50 dark:bg-amber-900/10 dark:border-amber-900/50">
                      <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-amber-600">
                        💭 예상 반응 시뮬레이션 결과
                      </h3>
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {reactionMsg}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="card h-full flex flex-col items-center justify-center text-slate-400 py-20 border-dashed">
                  <BarChart3 className="w-16 h-16 mb-4 opacity-20" />
                  <p>왼쪽에서 정보를 입력하고 분석을 시작해보세요.</p>
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            {/* Chat Settings */}
            <div className="lg:col-span-3 space-y-6">
              <section className="card space-y-4">
                <h2 className="text-xl font-bold border-b pb-2 flex items-center gap-2">
                  <Settings2 className="w-5 h-5" />
                  채팅 설정
                </h2>
                
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-500">나의 MBTI</label>
                  <select 
                    value={chatSettings.user_mbti}
                    onChange={(e) => setChatSettings({...chatSettings, user_mbti: e.target.value})}
                    className="w-full p-2 rounded-lg border bg-white dark:bg-slate-800"
                  >
                    {["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"].map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-500">상대방 MBTI</label>
                  <select 
                    value={chatSettings.target_mbti}
                    onChange={(e) => setChatSettings({...chatSettings, target_mbti: e.target.value})}
                    className="w-full p-2 rounded-lg border bg-white dark:bg-slate-800"
                  >
                    {["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP", "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"].map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-500">대화 배경/상황</label>
                  <textarea 
                    value={chatSettings.situation}
                    onChange={(e) => setChatSettings({...chatSettings, situation: e.target.value})}
                    className="w-full p-2 rounded-lg border bg-white dark:bg-slate-800 h-24 resize-none text-sm"
                  />
                </div>

                <button 
                  onClick={startChat}
                  className="w-full btn-secondary flex items-center justify-center gap-2"
                >
                  <Loader2 className={`w-4 h-4 ${chatLoading ? "animate-spin" : "hidden"}`} />
                  대화 시작 / 초기화
                </button>
              </section>
            </div>

            {/* Chatbot */}
            <div className="lg:col-span-6 flex flex-col h-[700px] gap-4">
              <div className="card flex-1 overflow-hidden flex flex-col p-0">
                <div className="border-b p-4 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between">
                  <span className="font-bold flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    상대방과 가상 대화 중 ({chatSettings.target_mbti} 성향)
                  </span>
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {chatHistory.length === 0 && (
                    <div className="text-center text-slate-400 mt-20">
                      설정을 마치고 '대화 시작'을 눌러주세요.
                    </div>
                  )}
                  {chatHistory.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] p-3 rounded-2xl shadow-sm ${
                        msg.role === "user" 
                          ? "bg-indigo-600 text-white rounded-br-none" 
                          : "bg-white dark:bg-slate-800 border rounded-bl-none"
                      }`}>
                        <p className="text-sm">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex justify-start">
                      <div className="bg-white dark:bg-slate-800 border p-3 rounded-2xl rounded-bl-none italic text-slate-400 text-sm">
                        생각 중...
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-4 border-t bg-white dark:bg-slate-900">
                  <form onSubmit={(e) => { e.preventDefault(); sendChatMessage(); }} className="flex gap-2">
                    <input 
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="메시지 입력..."
                      className="flex-1 p-3 rounded-xl border bg-slate-50 dark:bg-slate-800 outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <button type="submit" className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors">
                      <Send className="w-5 h-5" />
                    </button>
                  </form>
                </div>
              </div>
            </div>

            {/* Coaching Tip */}
            <div className="lg:col-span-3 h-[700px]">
              <section className="card border-amber-200 bg-amber-50/30 h-full flex flex-col overflow-hidden">
                <h2 className="text-lg font-bold flex items-center gap-2 text-amber-700 mb-4 flex-shrink-0">
                  <Sparkles className="w-5 h-5" />
                  AI 실시간 가이드
                </h2>
                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                  <div className="prose prose-sm prose-amber dark:prose-invert max-w-none whitespace-pre-wrap italic text-slate-700 dark:text-slate-300">
                    {coachingTip || "대화를 시작하면 이곳에서 실시간 전략 조언을 받으실 수 있습니다."}
                  </div>
                </div>
                <div className="mt-8 pt-4 border-t text-[10px] text-slate-400 leading-relaxed flex-shrink-0">
                  TIP: 상대방의 MBTI 특성에 맞는 단어 선택이 호감도를 결정합니다. AI 코치의 조언을 참고하여 답변을 수정해 보세요.
                </div>
              </section>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
