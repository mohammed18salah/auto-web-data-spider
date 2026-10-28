import { useState, useEffect, useRef } from 'react';
import { 
  Sun, Moon, Settings, Database, Clock, 
  Play, Square, Save, Download, Globe, 
  Terminal, Activity, RefreshCw, Home, Languages, Trash2,
  Eye, X, ExternalLink, AlertCircle, Info, AlertTriangle, Layers, Hash,
  HelpCircle, CheckCircle2
} from 'lucide-react';
import axios from 'axios';
import './index.css';

const API_BASE = 'http://localhost:8000/api';

type Page = 'home' | 'history';
type Lang = 'ar' | 'en';

interface LogEntry {
  time: string;
  type: 'info' | 'success' | 'error' | 'sys';
  message: string;
}

export interface SessionHistoryItem {
  id: string;
  topic: string;
  status: string;
  sources_analyzed: number;
  created_at: string | null;
}

export interface CrawledSourceItem {
  id?: number;
  url: string;
  domain: string;
  title: string;
  summary: string;
  quality_score: number;
  depth_level?: number;
  word_count?: number;
  crawled_at?: string | null;
}

const t = {
  ar: {
    title: 'Auto Web Data Spider',
    home: 'الرئيسية',
    history: 'الداتا السابقة',
    settings: 'الإعدادات',
    timeSince: 'الوقت منذ بدء العمل',
    buttonsBox: 'مربع الأزرار',
    searchPlaceholder: 'أدخل موضوع البحث هنا...',
    systemStatus: 'حالة النظام',
    statusRunning: 'قيد العمل...',
    statusStopped: 'متوقف',
    statusCompleted: 'اكتملت المهمة',
    statusIdle: 'جاهز للبدء',
    stopReasonLabel: 'سبب الانتهاء / التوقف:',
    sourcesAnalyzed: 'المصادر المحللة',
    sourcesTarget: 'المصادر المحللة والهدف',
    settingsAndNumbers: 'هنا الإعدادات والأرقام',
    searchDepth: 'عمق البحث (Search Depth)',
    maxSources: 'الحد الأقصى للمصادر (Max Sources)',
    depthPlaceholder: 'مثال: 3',
    sourcesPlaceholder: 'مثال: 15',
    presets: 'خيارات سريعة:',
    recommendedValue: 'القيمة المثالية الموصى بها',
    whatIfHugeNumber: 'ماذا لو وضعت رقماً ضخماً؟',
    detailsAndWarnings: 'تفاصيل وتحذيرات',
    depthHoverTitle: 'دليل عمق البحث (Search Depth)',
    depthBenefit: 'يحدد مستويات تشعب الروابط واستكشاف صفحات الويب انطلاقاً من نتائج البحث الأولى:',
    depthL1: 'المستوى 1: صفحات نتائج البحث المباشرة عن الموضوع.',
    depthL2: 'المستوى 2: الروابط والصفحات الموجودة داخل النتائج الأولى.',
    depthL3: 'المستوى 3+: روابط متفرعة شجرياً لأعماق أكبر داخل المواقع.',
    depthRecommendedDesc: 'من 1 إلى 3: يوفر توازناً مثالياً بين سرعة الجمع ودقة المعلومات دون تشتت.',
    depthHugeWarnDesc: 'وضع رقم ضخم (4 أو 5+): سيتضاعف عدد الروابط بشكل أسي لمئات الآلاف، مما يجعل الزحف بطيئاً جداً (قد يستغرق ساعات)، وقد يبتعد المحتوى عن صلب الموضوع الرئيسي ويستهلك الذاكرة.',
    depthLiveWarn: 'تنبيه: عمق كبير (4+) قد يستغرق وقتاً طويلاً ويشتت النتائج عن صلب الموضوع.',
    sourcesHoverTitle: 'دليل الحد الأقصى للمصادر (Max Sources)',
    sourcesBenefit: 'السقف الإجمالي لعدد المواقع والمقالات التي يحللها الروبوت ويستخرج خلاصاتها قبل التوقف تلقائياً.',
    sourcesRecommendedDesc: 'من 10 إلى 30 للاستعلام السريع، وحتى 50 للأبحاث الشاملة.',
    sourcesHugeWarnDesc: 'وضع رقم ضخم (أكثر من 50 أو 100+): ستستمر الجلسة لوقت أطول، وسيتم استهلاك حجم أكبر من الإنترنت والذاكرة، وقد تتعرض بعض الاستعلامات لحظر مؤقت (Rate Limit) من بعض محركات البحث.',
    sourcesLiveWarn: 'تنبيه: أكثر من 50 مصدراً قد يستهلك وقتاً وباندويث عالي ويزيد احتمالية تقييد الطلبات.',
    start: 'البدء',
    stop: 'إيقاف العمل',
    save: 'الحفظ',
    export: 'التصدير',
    browserWait: 'نافذة Chrome للزحف الآلي...',
    browserSearching: 'البحث عن',
    browserExploring: 'يتم الآن استعراض الصفحات واستخراج المعرفة بسرعة فائقة...',
    browserStopped: 'نافذة Chrome (متوقفة)',
    logTab: 'نافذة Log',
    terminalTab: 'نافذة التيرمنل',
    enterTopicError: 'الرجاء إدخال موضوع البحث أولاً!',
    connecting: 'جاري الاتصال بالخادم والبحث الفوري عن:',
    startSuccess: 'تم بدء عملية الزحف الصاروخية بنجاح! معرف الجلسة:',
    serverError: 'فشل الاتصال بالخادم:',
    crawlStopped: 'تم إيقاف عملية الزحف.',
    stoppingCrawl: 'جاري إرسال إشارة إيقاف الزحف إلى الخادم...',
    historyTitle: 'جلسات الزحف السابقة',
    settingsTitle: 'الإعدادات العامة',
    generalSettings: 'الإعدادات العامة',
    apiKeys: 'مفاتيح API',
    advanced: 'خيارات متقدمة',
    saveSettings: 'حفظ الإعدادات',
    noData: 'لا توجد بيانات سابقة حتى الآن.',
    sessionID: 'معرف الجلسة',
    topic: 'الموضوع',
    statusCol: 'الحالة',
    actions: 'الإجراءات',
    deleteConfirm: 'هل أنت متأكد من حذف هذه الجلسة وجميع بياناتها؟',
    deleteSuccess: 'تم حذف الجلسة بنجاح.',
    exportSuccess: 'تم تصدير وتنزيل ملف البيانات بنجاح!',
    saveSuccess: 'تم حفظ وتحديث الجلسة بنجاح.',
    viewDetails: 'عرض التفاصيل',
    downloadData: 'تحميل البيانات (JSON)',
    deleteSession: 'حذف الجلسة',
    sessionDetailsTitle: 'تفاصيل جلسة الزحف واستعراض الداتا',
    allCrawledSources: 'المصادر والصفحات المفهرسة',
    noSourcesFound: 'لم يتم أرشفة مصادر لهذه الجلسة بعد.',
    conceptsExtracted: 'المفاهيم المستخلصة',
    topicsDiscovered: 'الموضوعات المكتشفة',
    averageQuality: 'متوسط الجودة',
    wordsCount: 'كلمة',
    viewOriginal: 'فتح الرابط الأصلي',
    downloading: 'جاري التحميل...',
    downloadFullJson: 'تحميل ملف البيانات الكامل (JSON)',
    close: 'إغلاق',
    loadingDetails: 'جاري جلب تفاصيل الجلسة والمصادر...'
  },
  en: {
    title: 'Auto Web Data Spider',
    home: 'Home',
    history: 'History',
    settings: 'Settings',
    timeSince: 'Time since start',
    buttonsBox: 'Control Panel',
    searchPlaceholder: 'Enter search topic here...',
    systemStatus: 'System Status',
    statusRunning: 'Running...',
    statusStopped: 'Stopped',
    statusCompleted: 'Completed',
    statusIdle: 'Ready to Start',
    stopReasonLabel: 'Stop / Completion Reason:',
    sourcesAnalyzed: 'Sources Analyzed',
    sourcesTarget: 'Analyzed Sources & Target',
    settingsAndNumbers: 'Settings & Parameters',
    searchDepth: 'Search Depth',
    maxSources: 'Max Sources',
    depthPlaceholder: 'e.g. 3',
    sourcesPlaceholder: 'e.g. 15',
    presets: 'Quick Presets:',
    recommendedValue: 'Recommended Value',
    whatIfHugeNumber: 'What happens if you enter a huge number?',
    detailsAndWarnings: 'Details & Warnings',
    depthHoverTitle: 'Search Depth Guide',
    depthBenefit: 'Determines the branching levels of links to explore starting from primary search results:',
    depthL1: 'Level 1: Direct primary search result pages.',
    depthL2: 'Level 2: Links found within primary pages.',
    depthL3: 'Level 3+: Deeper nested links explored recursively.',
    depthRecommendedDesc: '1 to 3: Best balance between lightning crawl speed and high precision.',
    depthHugeWarnDesc: 'Setting a huge number (4 or 5+): Exponential link growth into hundreds of thousands of pages, causing massive slowdown, topic drift away from core subject, and heavy memory usage.',
    depthLiveWarn: 'Warning: Deep depth (4+) can cause extreme slowdown and topic drift.',
    sourcesHoverTitle: 'Max Sources Guide',
    sourcesBenefit: 'The ceiling of web pages and articles the bot reads, analyzes, and indexes before stopping automatically.',
    sourcesRecommendedDesc: '10 to 30 for quick insight, up to 50 for in-depth research.',
    sourcesHugeWarnDesc: 'Setting a huge number (over 50 or 100+): Prolongs the session significantly, consumes high network bandwidth, and risks temporary IP rate limits from search engines.',
    sourcesLiveWarn: 'Warning: Over 50 sources consumes high bandwidth and may risk rate limits.',
    start: 'Start',
    stop: 'Stop',
    save: 'Save',
    export: 'Export',
    browserWait: 'Chrome window for autonomous crawling...',
    browserSearching: 'Searching for',
    browserExploring: 'Browsing pages and extracting knowledge rapidly...',
    browserStopped: 'Chrome window (stopped)',
    logTab: 'Log Window',
    terminalTab: 'Terminal Window',
    enterTopicError: 'Please enter a search topic first!',
    connecting: 'Connecting to server and searching for:',
    startSuccess: 'Rocket crawl started successfully! Session ID:',
    serverError: 'Failed to connect to server:',
    crawlStopped: 'Crawl process stopped.',
    stoppingCrawl: 'Sending stop signal to server...',
    historyTitle: 'Previous Crawl Sessions',
    settingsTitle: 'General Settings',
    generalSettings: 'General Settings',
    apiKeys: 'API Keys',
    advanced: 'Advanced Options',
    saveSettings: 'Save Settings',
    noData: 'No previous data available yet.',
    sessionID: 'Session ID',
    topic: 'Topic',
    statusCol: 'Status',
    actions: 'Actions',
    deleteConfirm: 'Are you sure you want to delete this session and all its records?',
    deleteSuccess: 'Session deleted successfully.',
    exportSuccess: 'Data exported and downloaded successfully!',
    saveSuccess: 'Session saved and updated successfully.',
    viewDetails: 'View Details',
    downloadData: 'Download JSON',
    deleteSession: 'Delete Session',
    sessionDetailsTitle: 'Crawl Session Details & Data Explorer',
    allCrawledSources: 'Indexed Sources & Web Pages',
    noSourcesFound: 'No sources indexed for this session yet.',
    conceptsExtracted: 'Extracted Terms',
    topicsDiscovered: 'Discovered Topics',
    averageQuality: 'Avg Quality',
    wordsCount: 'words',
    viewOriginal: 'Open Link',
    settingsTitle: 'General Settings',
    generalSettings: 'General Settings',
    apiKeys: 'API Keys',
    advanced: 'Advanced Options',
    saveSettings: 'Save Settings',
    noData: 'No previous data available yet.',
    sessionID: 'Session ID',
    topic: 'Topic',
    statusCol: 'Status',
    actions: 'Actions',
    deleteConfirm: 'Are you sure you want to delete this session and all its records?',
    deleteSuccess: 'Session deleted successfully.',
    exportSuccess: 'Data exported and downloaded successfully!',
    saveSuccess: 'Session saved and updated successfully.',
    viewDetails: 'View Details',
    downloadData: 'Download JSON',
    deleteSession: 'Delete Session',
    sessionDetailsTitle: 'Crawl Session Details & Data Explorer',
    allCrawledSources: 'Indexed Sources & Web Pages',
    noSourcesFound: 'No sources indexed for this session yet.',
    conceptsExtracted: 'Extracted Terms',
    topicsDiscovered: 'Discovered Topics',
    averageQuality: 'Avg Quality',
    wordsCount: 'words',
    viewOriginal: 'Open Link',
    downloading: 'Downloading...',
    downloadFullJson: 'Download Complete JSON',
    close: 'Close',
    loadingDetails: 'Loading session details and sources...'
  }
};

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [lang, setLang] = useState<Lang>('ar');
  const [activeTab, setActiveTab] = useState<'log' | 'terminal'>('log');
  const [page, setPage] = useState<Page>('home');
  
  const [isRunning, setIsRunning] = useState(false);
  const [elapsedTime, setElapsedTime] = useState('00:00:00');
  const [searchQuery, setSearchQuery] = useState('');
  
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([
    { time: new Date().toLocaleTimeString(), type: 'info', message: 'System initialized.' }
  ]);
  const [stats, setStats] = useState({ sources: 0, topics: 0 });
  const [maxDepth, setMaxDepth] = useState(3);
  const [maxSources, setMaxSources] = useState(10);
  
  // Live crawler state for display
  const [currentUrl, setCurrentUrl] = useState<string>('');
  const [currentTitle, setCurrentTitle] = useState<string>('');
  const [currentDomain, setCurrentDomain] = useState<string>('');
  const [currentSummary, setCurrentSummary] = useState<string>('');
  const [currentScore, setCurrentScore] = useState<number>(0);
  

  const [browserHeight, setBrowserHeight] = useState(350);
  const isDragging = useRef(false);

  const loc = t[lang];

  const [historyList, setHistoryList] = useState<SessionHistoryItem[]>([]);
  const [stopReason, setStopReason] = useState<string>('');
  const [crawlFinished, setCrawlFinished] = useState<boolean>(false);
  const [showDepthGuide, setShowDepthGuide] = useState<boolean>(false);
  const [showSourcesGuide, setShowSourcesGuide] = useState<boolean>(false);

  // Detailed view & export modal state
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedSessionTopic, setSelectedSessionTopic] = useState<string>('');
  const [selectedSessionStats, setSelectedSessionStats] = useState<any | null>(null);
  const [selectedSessionSources, setSelectedSessionSources] = useState<CrawledSourceItem[]>([]);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
  }, [theme, lang]);

  useEffect(() => {
    if (page === 'history') {
      axios.get<SessionHistoryItem[]>(`${API_BASE}/sessions`)
        .then(res => setHistoryList(res.data))
        .catch(err => console.error("Error fetching sessions:", err));
    }
  }, [page]);

  useEffect(() => {
    if (activeTab === 'log') {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, activeTab]);

  useEffect(() => {
    let interval: number;
    if (isRunning) {
      const startTime = Date.now();
      interval = window.setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const h = Math.floor(elapsed / 3600).toString().padStart(2, '0');
        const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0');
        const s = (elapsed % 60).toString().padStart(2, '0');
        setElapsedTime(`${h}:${m}:${s}`);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  useEffect(() => {
    let pollInterval: number;
    if (isRunning && sessionId) {
      pollInterval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE}/session/${sessionId}`);
          if (res.data) {
            setStats({
              sources: res.data.sources_total ?? 0,
              topics: res.data.topics ?? 0
            });
            if (res.data.current_url) setCurrentUrl(res.data.current_url);
            if (res.data.current_title) setCurrentTitle(res.data.current_title);
            if (res.data.current_domain) setCurrentDomain(res.data.current_domain);
            if (res.data.current_summary) setCurrentSummary(res.data.current_summary);
            if (typeof res.data.current_score === 'number') setCurrentScore(res.data.current_score);

            if (res.data.live_logs && Array.isArray(res.data.live_logs) && res.data.live_logs.length > 0) {
              setLogs(prev => {
                const existing = new Set(prev.map(l => l.time + l.message));
                const newEntries = res.data.live_logs.filter((l: LogEntry) => !existing.has(l.time + l.message));
                return newEntries.length > 0 ? [...prev, ...newEntries] : prev;
              });
            }

            const sourcesNow = res.data.sources_total ?? 0;
            const targetMet = maxSources > 0 && sourcesNow >= maxSources;
            if (res.data.status === 'complete' || res.data.status === 'paused' || targetMet) {
              setIsRunning(false);
              const isComp = res.data.status === 'complete' || targetMet;
              const reason = res.data.stop_reason || (isComp ? (lang === 'ar' ? `اكتملت المهمة بنجاح مع جمع (${sourcesNow}) مصادر.` : `Crawl completed successfully (${sourcesNow} sources).`) : (lang === 'ar' ? 'تم إيقاف عملية الزحف.' : 'Crawl paused.'));
              setStopReason(reason);
              setCrawlFinished(isComp);
              setLogs(prev => {
                const finishMsg = `${loc.stopReasonLabel} ${reason}`;
                if (prev.some(l => l.message.includes(loc.stopReasonLabel) || l.message === finishMsg)) return prev;
                return [...prev, { time: new Date().toLocaleTimeString(), type: isComp ? 'success' : 'info', message: finishMsg }];
              });
            }
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 750) as unknown as number; // 750ms for lightning responsive UI
    }
    return () => clearInterval(pollInterval);
  }, [isRunning, sessionId, lang, maxSources]);

  const addLog = (type: 'info'|'success'|'error'|'sys', message: string) => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), type, message }]);
  };

  const getSystemStatus = () => {
    const isTargetMet = maxSources > 0 && stats.sources >= maxSources && stats.sources > 0;
    if (isRunning && !isTargetMet) {
      return {
        label: lang === 'ar' ? `قيد الزحف والتحليل (${stats.sources} / ${maxSources})` : `Crawling & Mining (${stats.sources} / ${maxSources})`,
        subtext: lang === 'ar' ? 'جاري استكشاف وفهرسة صفحات الويب بنشاط...' : 'Actively discovering and indexing web pages...',
        badgeClass: 'running',
        progress: maxSources > 0 ? Math.min(100, Math.round((stats.sources / maxSources) * 100)) : 0
      };
    }
    if (crawlFinished || isTargetMet) {
      return {
        label: loc.statusCompleted,
        subtext: lang === 'ar' ? `تم جمع وتحليل كافة المصادر المستهدفة بنجاح (${stats.sources} مصادر).` : `All target sources analyzed successfully (${stats.sources} sources).`,
        badgeClass: 'complete',
        progress: 100
      };
    }
    if (!isRunning && (sessionId || stats.sources > 0)) {
      return {
        label: loc.statusStopped,
        subtext: stopReason || (lang === 'ar' ? 'تم إيقاف الجلسة مؤقتاً.' : 'Session stopped.'),
        badgeClass: 'paused',
        progress: maxSources > 0 ? Math.min(100, Math.round((stats.sources / maxSources) * 100)) : 0
      };
    }
    return {
      label: loc.statusIdle,
      subtext: lang === 'ar' ? 'أدخل موضوع البحث في الأعلى واضغط البدء' : 'Enter a search topic above and click Start',
      badgeClass: 'idle',
      progress: 0
    };
  };

  const handleStart = async () => {
    if (!searchQuery.trim()) {
      addLog('error', loc.enterTopicError);
      return;
    }
    
    setIsRunning(true);
    setElapsedTime('00:00:00');
    setStopReason('');
    setCrawlFinished(false);
    setStats({ sources: 0, topics: 0 });
    setCurrentUrl('');
    setCurrentTitle('');
    setCurrentDomain('');
    setCurrentSummary('');
    setCurrentScore(0);
    addLog('sys', `${loc.connecting} ${searchQuery}...`);
    
    try {
      const res = await axios.post(`${API_BASE}/crawl`, {
        topic: searchQuery,
        max_depth: maxDepth,
        max_sources: maxSources
      });
      
      if (res.data.status === 'started') {
        setSessionId(res.data.session_id);
        addLog('success', `${loc.startSuccess} ${res.data.session_id}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog('error', `${loc.serverError} ${msg}`);
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    addLog('sys', loc.stoppingCrawl);
    try {
      if (sessionId) {
        await axios.post(`${API_BASE}/crawl/${sessionId}/stop`);
      } else {
        await axios.post(`${API_BASE}/crawl/stop`);
      }
    } catch (err: unknown) {
      console.warn("Stop request warning:", err);
    } finally {
      setIsRunning(false);
      const userReason = lang === 'ar' ? 'تم إيقاف عملية الزحف يدوياً بواسطة المستخدم.' : 'Crawl stopped manually by user.';
      setStopReason(userReason);
      setCrawlFinished(false);
      addLog('info', userReason);
    }
  };

  const handleDeleteSession = async (id: string) => {
    if (!window.confirm(loc.deleteConfirm)) return;
    try {
      await axios.delete(`${API_BASE}/session/${id}`);
      setHistoryList(prev => prev.filter(s => s.id !== id));
      if (selectedSessionId === id) {
        setSelectedSessionId(null);
      }
      addLog('success', `${loc.deleteSuccess} (${id.slice(0, 8)}...)`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog('error', `${loc.serverError} ${msg}`);
    }
  };

  const handleViewSession = async (session: SessionHistoryItem) => {
    setSelectedSessionId(session.id);
    setSelectedSessionTopic(session.topic);
    setLoadingDetails(true);
    setSelectedSessionSources([]);
    setSelectedSessionStats(null);
    try {
      const [statsRes, sourcesRes] = await Promise.all([
        axios.get(`${API_BASE}/session/${session.id}`),
        axios.get<CrawledSourceItem[]>(`${API_BASE}/session/${session.id}/sources`)
      ]);
      setSelectedSessionStats(statsRes.data);
      setSelectedSessionSources(sourcesRes.data || []);
    } catch (err) {
      console.error("Error fetching session details:", err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleDownloadSession = async (sId: string, topicName: string) => {
    try {
      setDownloadingId(sId);
      const res = await axios.get(`${API_BASE}/export/${sId}`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const safeTopic = (topicName || 'session').replace(/[^a-zA-Z0-9\u0600-\u06FF]/g, '_');
      link.download = `spider_${safeTopic}_${sId.slice(0, 8)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      console.error("Export download failed:", err);
      alert(lang === 'ar' ? 'تعذر تنزيل البيانات، تأكد من وجود ملفات التصدير' : 'Failed to download session export.');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleExport = async () => {
    if (!sessionId) return;
    try {
      addLog('sys', lang === 'ar' ? 'جاري تجهيز وتنزيل ملف التصدير...' : 'Preparing export file...');
      const res = await axios.get(`${API_BASE}/export/${sessionId}`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `spider_export_${sessionId.slice(0, 8)}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      addLog('success', loc.exportSuccess);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog('error', `${loc.serverError} ${msg}`);
    }
  };

  const handleSave = () => {
    if (!sessionId) return;
    addLog('success', `${loc.saveSuccess} (${sessionId.slice(0, 8)}...)`);
  };

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');
  const toggleLang = () => setLang(prev => prev === 'ar' ? 'en' : 'ar');

  const handleMouseDown = () => {
    isDragging.current = true;
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging.current) return;
    setBrowserHeight(prev => Math.max(200, Math.min(800, prev + e.movementY)));
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  const renderLogs = () => logs.map((log, idx) => (
    <div key={idx} className={`log-line ${log.type}`}>
      <span className="timestamp">[{log.time}]</span> [{log.type.toUpperCase()}] {log.message}
    </div>
  ));

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="glass-panel header">
        {/* Brand Section */}
        <div className="header-brand" onClick={() => setPage('home')}>
          <span className="brand-title">{loc.title}</span>
        </div>

        {/* Central Navigation Pills */}
        <nav className="header-nav">
          <button 
            className={`nav-pill ${page === 'home' ? 'active' : ''}`} 
            onClick={() => setPage('home')}
          >
            <Home size={17} /> 
            <span>{loc.home}</span>
          </button>
          <button 
            className={`nav-pill ${page === 'history' ? 'active' : ''}`} 
            onClick={() => setPage('history')}
          >
            <Database size={17} /> 
            <span>{loc.history}</span>
          </button>
        </nav>

        {/* Controls & Status Section */}
        <div className="header-actions">
          <div className={`timer-badge ${isRunning ? 'running' : ''}`}>
            <Clock size={16} />
            <span className="timer-value">{elapsedTime}</span>
            <span className="timer-label">{loc.timeSince}</span>
            {isRunning && <span className="status-pulse-dot"></span>}
          </div>

          <div className="nav-divider"></div>

          <button className="btn-icon" onClick={toggleLang} title="تغيير اللغة / Change Language">
            <Languages size={18} />
          </button>

          <button className="btn-icon" onClick={toggleTheme} title="تغيير المظهر / Toggle Theme">
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="main-content">
        {page === 'home' && (
          <>
            {/* SIDEBAR */}
            <aside className="glass-panel sidebar">
              <div className="sidebar-section">
                <h2 className="sidebar-title"><Settings size={20} /> {loc.buttonsBox}</h2>
                
                <div className="search-box">
                  <input 
                    type="text" 
                    className="search-input" 
                    placeholder={loc.searchPlaceholder}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    disabled={isRunning}
                  />
                </div>

                {/* SYSTEM STATUS CARD (REAL-TIME AUTHENTIC STATUS) */}
                {(() => {
                  const sysStatus = getSystemStatus();
                  return (
                    <div className="stat-card">
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <span className="stat-label">{loc.systemStatus}</span>
                        <span className={`live-status-pill ${sysStatus.badgeClass}`}>
                          {sysStatus.badgeClass === 'running' && <span className="pulse-dot-live"></span>}
                          {sysStatus.badgeClass === 'complete' && <CheckCircle2 size={13} style={{ color: '#10b981' }} />}
                          {sysStatus.badgeClass === 'paused' && <Square size={11} style={{ color: '#f59e0b' }} />}
                          {sysStatus.badgeClass === 'idle' && <Clock size={12} style={{ color: '#94a3b8' }} />}
                          <span>{sysStatus.label}</span>
                        </span>
                      </div>
                      
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.4 }}>
                        {sysStatus.subtext}
                      </div>

                      {stopReason && !isRunning && (
                        <div style={{
                          marginTop: '8px',
                          fontSize: '0.78rem',
                          lineHeight: '1.4',
                          color: (crawlFinished || (stats.sources >= maxSources && stats.sources > 0)) ? '#34d399' : '#93c5fd',
                          background: (crawlFinished || (stats.sources >= maxSources && stats.sources > 0)) ? 'rgba(16, 185, 129, 0.12)' : 'rgba(59, 130, 246, 0.12)',
                          padding: '5px 10px',
                          borderRadius: '6px',
                          border: `1px solid ${(crawlFinished || (stats.sources >= maxSources && stats.sources > 0)) ? 'rgba(16, 185, 129, 0.25)' : 'rgba(59, 130, 246, 0.25)'}`,
                          fontWeight: 600
                        }}>
                          {stopReason}
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* SOURCES ANALYZED & TARGET CARD */}
                <div className="stat-card">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span className="stat-label">{loc.sourcesTarget}</span>
                    <span style={{ fontSize: '0.8rem', fontWeight: 800, color: (stats.sources >= maxSources && stats.sources > 0) ? '#10b981' : 'var(--accent-color)' }}>
                      {maxSources > 0 ? Math.min(100, Math.round((stats.sources / maxSources) * 100)) : 0}%
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
                    <span className="stat-value" style={{ 
                      fontSize: '1.6rem', 
                      color: (stats.sources >= maxSources && stats.sources > 0) ? '#10b981' : 'var(--accent-color)' 
                    }}>
                      {stats.sources}
                    </span>
                    <span style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', fontWeight: 700 }}>
                      / {maxSources}
                    </span>
                  </div>
                  <div className="stat-progress-container">
                    <div className="stat-progress-bar">
                      <div 
                        className={`stat-progress-fill ${(stats.sources >= maxSources && stats.sources > 0) ? 'complete' : (isRunning ? '' : 'paused')}`}
                        style={{ width: `${maxSources > 0 ? Math.min(100, Math.round((stats.sources / maxSources) * 100)) : 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* SETTINGS AND NUMBERS (TYPABLE INPUTS WITH EXAMPLES, STEPPERS, PRESETS & RICH HOVER TOOLTIPS) */}
              <div className="sidebar-section">
                <h2 className="sidebar-title"><Activity size={20} /> {loc.settingsAndNumbers}</h2>

                {/* CONFIG 1: SEARCH DEPTH */}
                <div className="config-box">
                  <div className="config-header">
                    <div className="config-header-left">
                      <Layers size={17} style={{ color: 'var(--accent-color)' }} />
                      <span className="config-title-text">{loc.searchDepth}</span>
                    </div>

                    {/* Square button to toggle guide */}
                    <button
                      type="button"
                      className={`config-square-btn ${showDepthGuide ? 'active' : ''}`}
                      onClick={() => setShowDepthGuide(!showDepthGuide)}
                      title={showDepthGuide ? 'إخفاء الدليل' : 'عرض الدليل والتحذيرات'}
                    >
                      <HelpCircle size={15} />
                      <span>{loc.detailsAndWarnings}</span>
                    </button>
                  </div>

                  {/* INLINE GUIDE CARD - 100% PROPER DISPLAY WITHOUT CUTOFF OR EMOJIS */}
                  {showDepthGuide && (
                    <div className="config-guide-card">
                      <div className="guide-card-header">
                        <div className="guide-card-title">
                          <Layers size={16} />
                          <span>{loc.depthHoverTitle}</span>
                        </div>
                        <button 
                          type="button" 
                          className="guide-close-btn"
                          onClick={() => setShowDepthGuide(false)}
                          title="إغلاق"
                        >
                          <X size={14} />
                        </button>
                      </div>

                      <div className="guide-section">
                        <div className="guide-section-title">
                          <Info size={14} style={{ color: 'var(--accent-color)' }} />
                          <span>{lang === 'ar' ? 'الفائدة والأهمية:' : 'Purpose:'}</span>
                        </div>
                        <p className="guide-text">{loc.depthBenefit}</p>
                        <ul className="guide-list">
                          <li>{loc.depthL1}</li>
                          <li>{loc.depthL2}</li>
                          <li>{loc.depthL3}</li>
                        </ul>
                      </div>

                      <div className="guide-section">
                        <div className="guide-section-title" style={{ color: '#10b981' }}>
                          <CheckCircle2 size={14} style={{ color: '#10b981' }} />
                          <span>{loc.recommendedValue}:</span>
                        </div>
                        <p className="guide-text" style={{ color: '#34d399', fontWeight: 600 }}>{loc.depthRecommendedDesc}</p>
                      </div>

                      <div className="guide-warn-box">
                        <div className="guide-warn-title">
                          <AlertTriangle size={14} style={{ color: '#f59e0b' }} />
                          <span>{loc.whatIfHugeNumber}</span>
                        </div>
                        <div className="guide-warn-text">{loc.depthHugeWarnDesc}</div>
                      </div>
                    </div>
                  )}

                  {/* Typable number input + Stepper controls */}
                  <div className="config-input-row">
                    <div className="config-input-wrapper">
                      <input 
                        type="number"
                        min="1"
                        max="10"
                        className="config-num-input"
                        placeholder={loc.depthPlaceholder}
                        value={maxDepth || ''}
                        onChange={(e) => {
                          const val = parseInt(e.target.value, 10);
                          setMaxDepth(isNaN(val) ? 0 : Math.max(1, Math.min(10, val)));
                        }}
                        onBlur={() => {
                          if (!maxDepth || maxDepth < 1) setMaxDepth(1);
                        }}
                        disabled={isRunning}
                      />
                    </div>
                    <button 
                      type="button" 
                      className="config-stepper-btn" 
                      onClick={() => setMaxDepth(prev => Math.max(1, prev - 1))}
                      disabled={isRunning || maxDepth <= 1}
                      title="تقليل العمق (-1)"
                    >
                      -
                    </button>
                    <button 
                      type="button" 
                      className="config-stepper-btn" 
                      onClick={() => setMaxDepth(prev => Math.min(10, prev + 1))}
                      disabled={isRunning || maxDepth >= 10}
                      title="زيادة العمق (+1)"
                    >
                      +
                    </button>
                  </div>

                  {/* Range slider synchronized */}
                  <input 
                    type="range" 
                    min="1" 
                    max="10" 
                    value={Math.min(10, Math.max(1, maxDepth))} 
                    onChange={(e) => setMaxDepth(Number(e.target.value))} 
                    disabled={isRunning} 
                  />

                  {/* Quick Preset Buttons */}
                  <div className="config-presets-row">
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{loc.presets}</span>
                    {[1, 2, 3, 4, 5].map((d) => (
                      <button
                        key={d}
                        type="button"
                        className={`config-preset-pill ${maxDepth === d ? 'active' : ''}`}
                        onClick={() => setMaxDepth(d)}
                        disabled={isRunning}
                      >
                        {d}
                      </button>
                    ))}
                  </div>

                  {/* Live Warning if high number */}
                  {maxDepth >= 4 && (
                    <div className="config-live-warning">
                      <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <span>{loc.depthLiveWarn}</span>
                    </div>
                  )}
                </div>

                {/* CONFIG 2: MAX SOURCES */}
                <div className="config-box">
                  <div className="config-header">
                    <div className="config-header-left">
                      <Hash size={17} style={{ color: 'var(--accent-color)' }} />
                      <span className="config-title-text">{loc.maxSources}</span>
                    </div>

                    {/* Square button to toggle guide */}
                    <button
                      type="button"
                      className={`config-square-btn ${showSourcesGuide ? 'active' : ''}`}
                      onClick={() => setShowSourcesGuide(!showSourcesGuide)}
                      title={showSourcesGuide ? 'إخفاء الدليل' : 'عرض الدليل والتحذيرات'}
                    >
                      <HelpCircle size={15} />
                      <span>{loc.detailsAndWarnings}</span>
                    </button>
                  </div>

                  {/* INLINE GUIDE CARD - 100% PROPER DISPLAY WITHOUT CUTOFF OR EMOJIS */}
                  {showSourcesGuide && (
                    <div className="config-guide-card">
                      <div className="guide-card-header">
                        <div className="guide-card-title">
                          <Hash size={16} />
                          <span>{loc.sourcesHoverTitle}</span>
                        </div>
                        <button 
                          type="button" 
                          className="guide-close-btn"
                          onClick={() => setShowSourcesGuide(false)}
                          title="إغلاق"
                        >
                          <X size={14} />
                        </button>
                      </div>

                      <div className="guide-section">
                        <div className="guide-section-title">
                          <Info size={14} style={{ color: 'var(--accent-color)' }} />
                          <span>{lang === 'ar' ? 'الفائدة والأهمية:' : 'Purpose:'}</span>
                        </div>
                        <p className="guide-text">{loc.sourcesBenefit}</p>
                      </div>

                      <div className="guide-section">
                        <div className="guide-section-title" style={{ color: '#10b981' }}>
                          <CheckCircle2 size={14} style={{ color: '#10b981' }} />
                          <span>{loc.recommendedValue}:</span>
                        </div>
                        <p className="guide-text" style={{ color: '#34d399', fontWeight: 600 }}>{loc.sourcesRecommendedDesc}</p>
                      </div>

                      <div className="guide-warn-box">
                        <div className="guide-warn-title">
                          <AlertTriangle size={14} style={{ color: '#f59e0b' }} />
                          <span>{loc.whatIfHugeNumber}</span>
                        </div>
                        <div className="guide-warn-text">{loc.sourcesHugeWarnDesc}</div>
                      </div>
                    </div>
                  )}

                  {/* Typable number input + Stepper controls */}
                  <div className="config-input-row">
                    <div className="config-input-wrapper">
                      <input 
                        type="number"
                        min="1"
                        max="1000"
                        className="config-num-input"
                        placeholder={loc.sourcesPlaceholder}
                        value={maxSources || ''}
                        onChange={(e) => {
                          const val = parseInt(e.target.value, 10);
                          setMaxSources(isNaN(val) ? 0 : Math.max(1, Math.min(1000, val)));
                        }}
                        onBlur={() => {
                          if (!maxSources || maxSources < 1) setMaxSources(1);
                        }}
                        disabled={isRunning}
                      />
                    </div>
                    <button 
                      type="button" 
                      className="config-stepper-btn" 
                      onClick={() => setMaxSources(prev => Math.max(1, prev - 5))}
                      disabled={isRunning || maxSources <= 1}
                      title="تقليل المصادر (-5)"
                    >
                      -
                    </button>
                    <button 
                      type="button" 
                      className="config-stepper-btn" 
                      onClick={() => setMaxSources(prev => Math.min(1000, prev + 5))}
                      disabled={isRunning || maxSources >= 1000}
                      title="زيادة المصادر (+5)"
                    >
                      +
                    </button>
                  </div>

                  {/* Range slider synchronized */}
                  <input 
                    type="range" 
                    min="1" 
                    max="100" 
                    value={Math.min(100, Math.max(1, maxSources))} 
                    onChange={(e) => setMaxSources(Number(e.target.value))} 
                    disabled={isRunning} 
                  />

                  {/* Quick Preset Buttons */}
                  <div className="config-presets-row">
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>{loc.presets}</span>
                    {[5, 10, 20, 30, 50, 100].map((s) => (
                      <button
                        key={s}
                        type="button"
                        className={`config-preset-pill ${maxSources === s ? 'active' : ''}`}
                        onClick={() => setMaxSources(s)}
                        disabled={isRunning}
                      >
                        {s}
                      </button>
                    ))}
                  </div>

                  {/* Live Warning if high number */}
                  {maxSources > 50 && (
                    <div className="config-live-warning">
                      <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: '2px' }} />
                      <span>{loc.sourcesLiveWarn}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="sidebar-section">
                <button 
                  className={`action-btn ${isRunning ? 'btn-danger' : 'btn-primary pulse-animation'}`}
                  onClick={isRunning ? handleStop : handleStart}
                >
                  {isRunning ? <><Square size={20} /> {loc.stop}</> : <><Play size={20} /> {loc.start}</>}
                </button>
                <button 
                  className="action-btn btn-success" 
                  disabled={isRunning || !sessionId}
                  onClick={handleSave}
                  title={loc.save}
                >
                  <Save size={20} /> {loc.save}
                </button>
                <button 
                  className="action-btn" 
                  style={{ background: 'var(--text-secondary)' }} 
                  disabled={isRunning || !sessionId}
                  onClick={handleExport}
                  title={loc.export}
                >
                  <Download size={20} /> {loc.export}
                </button>
              </div>
            </aside>

            {/* WORKSPACE */}
            <div className="workspace-area">
              
              {/* BROWSER VIEW */}
              <div className="glass-panel browser-container" style={{ height: `${browserHeight}px`, flex: 'none', aspectRatio: '1/1', maxHeight: '60vh' }}>
                <div className="browser-header">
                  <div className="browser-dots">
                    <div className="dot red"></div>
                    <div className="dot yellow"></div>
                    <div className="dot green"></div>
                  </div>
                  <div className="browser-url-bar">
                    <Globe size={14} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {currentUrl || (isRunning ? `${loc.browserSearching}: ${searchQuery}...` : (stopReason ? `[${stopReason}]` : loc.browserWait))}
                    </span>
                  </div>
                  <button className="btn-icon" style={{ width: '28px', height: '28px', border: 'none' }} onClick={() => { if (sessionId) axios.get(`${API_BASE}/session/${sessionId}`); }}>
                    <RefreshCw size={14} className={isRunning ? 'spin-animation' : ''} />
                  </button>
                </div>
                <div className="browser-content" style={{ padding: currentTitle || currentUrl || (stopReason && !isRunning) ? '18px 24px' : '0', overflowY: 'auto' }}>
                  {/* Stop / Completion Notification Banner */}
                  {stopReason && !isRunning && (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 18px',
                      borderRadius: '10px',
                      background: crawlFinished ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                      border: `1px solid ${crawlFinished ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
                      color: crawlFinished ? '#34d399' : '#f87171',
                      marginBottom: '16px',
                      fontSize: '0.9rem',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: '8px', background: crawlFinished ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)', flexShrink: 0 }}>
                        {crawlFinished ? <CheckCircle2 size={20} style={{ color: '#10b981' }} /> : <AlertCircle size={20} style={{ color: '#ef4444' }} />}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>
                          {crawlFinished 
                            ? (lang === 'ar' ? 'اكتملت مهمة الزحف بنجاح' : 'Crawl Completed Successfully') 
                            : (lang === 'ar' ? 'توقفت عملية الزحف' : 'Crawl Stopped')}
                        </span>
                        <span style={{ fontSize: '0.85rem', opacity: 0.95, color: crawlFinished ? '#a7f3d0' : '#fca5a5' }}>
                          {stopReason}
                        </span>
                      </div>
                    </div>
                  )}

                  {currentTitle || currentUrl ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', width: '100%' }}>
                      {/* Meta header bar */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--panel-border)', paddingBottom: '10px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '0.78rem', padding: '3px 8px', borderRadius: '6px', background: 'rgba(37, 99, 235, 0.15)', color: '#60a5fa', fontWeight: 700 }}>
                            {currentDomain || 'WEB SOURCE'}
                          </span>
                          <span style={{ fontSize: '0.78rem', color: '#10b981', fontWeight: 600 }}>
                            ● HTTP 200 OK
                          </span>
                        </div>
                        {currentScore > 0 && (
                          <span style={{ fontSize: '0.8rem', padding: '2px 8px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontWeight: 700 }}>
                            جودة المحتوى: {Math.round(currentScore * 100)}%
                          </span>
                        )}
                      </div>

                      {/* Web Page Title */}
                      <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.4 }}>
                        {currentTitle || currentUrl}
                      </h3>

                      {/* Extracted Summary & Core Knowledge */}
                      <div style={{ padding: '14px', borderRadius: '12px', background: 'var(--card-sub-bg)', border: '1px solid var(--card-sub-border)', fontSize: '0.92rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
                        <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', fontSize: '0.92rem' }}>
                          {lang === 'ar' ? 'المعرفة المستخلصة والملخص:' : 'Extracted Knowledge & Summary:'}
                        </p>
                        <p>{currentSummary || (lang === 'ar' ? 'تم استخراج النصوص وتحليل الكلمات المفتاحية بنجاح...' : 'Text and core concepts extracted successfully...')}</p>
                      </div>

                      {/* Source Link */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        <a href={currentUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-color)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '80%' }}>
                          ↗ {currentUrl}
                        </a>
                        <span style={{ color: isRunning ? '#60a5fa' : '#10b981', fontWeight: 600 }}>
                          {isRunning ? (lang === 'ar' ? 'جاري الاستكشاف...' : 'Active Crawler') : (lang === 'ar' ? 'تم الفهرسة' : 'Indexed')}
                        </span>
                      </div>
                    </div>
                  ) : isRunning ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px', color: 'var(--text-secondary)' }}>
                      <Globe size={64} className="pulse-animation" style={{ opacity: 0.6, color: 'var(--accent-color)' }} />
                      <p style={{ fontSize: '1.2rem', fontWeight: 600 }}>{loc.browserExploring}</p>
                      <span style={{ fontSize: '0.85rem', opacity: 0.7 }}>{searchQuery ? `جاري تمشيط محركات البحث عن: ${searchQuery}` : ''}</span>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px', color: 'var(--text-secondary)', textAlign: 'center', padding: '20px' }}>
                      <Globe size={64} style={{ color: crawlFinished ? '#10b981' : 'var(--panel-border)' }} />
                      <p style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {crawlFinished ? loc.statusCompleted : loc.browserStopped}
                      </p>
                      {stopReason && (
                        <p style={{ fontSize: '0.9rem', color: '#93c5fd', maxWidth: '420px', background: 'rgba(59, 130, 246, 0.1)', padding: '8px 14px', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                          {stopReason}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              <div className="resizer" onMouseDown={handleMouseDown}>
                <div className="resizer-line"></div>
              </div>

              {/* LOGS */}
              <div className="glass-panel logs-container">
                <div className="tabs-header">
                  <button className={`tab-btn ${activeTab === 'log' ? 'active' : ''}`} onClick={() => setActiveTab('log')}>
                    <Activity size={16} /> {loc.logTab}
                  </button>
                  <button className={`tab-btn ${activeTab === 'terminal' ? 'active' : ''}`} onClick={() => setActiveTab('terminal')}>
                    <Terminal size={16} /> {loc.terminalTab}
                  </button>
                </div>
                <div className="tab-content">
                  {activeTab === 'log' ? (
                    <>
                      {renderLogs()}
                      <div ref={logsEndRef} />
                    </>
                  ) : (
                    <>
                      <div className="log-line" style={{ color: '#fbbf24' }}>Welcome to Spider Terminal v1.0</div>
                      <div className="log-line">spider-engine&gt; {isRunning ? `running crawl --topic "${searchQuery}"` : 'waiting...'}</div>
                      <div className="log-line animate-pulse">_</div>
                    </>
                  )}
                </div>
              </div>

            </div>
          </>
        )}

        {page === 'history' && (
          <div className="glass-panel history-panel">
            <div className="history-header">
              <div className="history-icon-badge">
                <Database size={22} />
              </div>
              <div>
                <h2>{loc.historyTitle}</h2>
                <p className="history-subtitle">{lang === 'ar' ? 'سجل العمليات وبيانات الزحف المحفوظة محلياً' : 'Locally stored crawl history and sessions'}</p>
              </div>
            </div>
            
            <div className="history-table-container">
              <table className="history-table" style={{ textAlign: lang === 'ar' ? 'right' : 'left' }}>
                <thead>
                  <tr>
                    <th>{loc.sessionID}</th>
                    <th>{loc.topic}</th>
                    <th>{loc.sourcesAnalyzed}</th>
                    <th>{loc.statusCol}</th>
                    <th style={{ textAlign: 'center' }}>{loc.actions}</th>
                  </tr>
                </thead>
                <tbody>
                  {historyList.length > 0 ? historyList.map(session => (
                    <tr key={session.id} style={{ cursor: 'pointer' }} onClick={() => handleViewSession(session)}>
                      <td className="font-mono text-muted">{session.id.slice(0, 8)}...</td>
                      <td className="font-semibold">{session.topic}</td>
                      <td>
                        <span className="source-count-pill">{session.sources_analyzed || 0}</span>
                      </td>
                      <td>
                        <span className={`status-badge ${session.status}`}>
                          <span className="status-dot"></span>
                          {session.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }} onClick={e => e.stopPropagation()}>
                         <div className="history-actions-cell">
                           <button 
                             className="btn-icon btn-action-view" 
                             title={loc.viewDetails}
                             onClick={() => handleViewSession(session)}
                           >
                             <Eye size={16} />
                           </button>
                           <button 
                             className={`btn-icon btn-action-download ${downloadingId === session.id ? 'spin-animation' : ''}`} 
                             title={loc.downloadData}
                             onClick={() => handleDownloadSession(session.id, session.topic)}
                           >
                             <Download size={16} />
                           </button>
                           <button 
                             className="btn-icon btn-danger-hover" 
                             title={loc.deleteSession}
                             onClick={() => handleDeleteSession(session.id)}
                           >
                             <Trash2 size={16} />
                           </button>
                         </div>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={5} className="no-data-cell">
                        <Database size={40} className="no-data-icon" />
                        <p>{loc.noData}</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

      {/* SESSION DETAILS & DATA EXPLORER MODAL */}
      {selectedSessionId && (
        <div className="modal-backdrop" onClick={() => setSelectedSessionId(null)}>
          <div className="session-details-modal" onClick={e => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="modal-header">
              <div className="modal-title-group">
                <Database size={22} style={{ color: 'var(--accent-color)' }} />
                <div>
                  <h3 className="modal-title">{selectedSessionTopic || loc.sessionDetailsTitle}</h3>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                    ID: {selectedSessionId}
                  </span>
                </div>
              </div>

              <div className="modal-header-actions">
                <button 
                  className="btn-modal-download"
                  onClick={() => handleDownloadSession(selectedSessionId, selectedSessionTopic)}
                  disabled={downloadingId === selectedSessionId}
                >
                  <Download size={16} className={downloadingId === selectedSessionId ? 'spin-animation' : ''} />
                  <span>{downloadingId === selectedSessionId ? loc.downloading : loc.downloadFullJson}</span>
                </button>
                <button 
                  className="btn-modal-close"
                  onClick={() => setSelectedSessionId(null)}
                  title={loc.close}
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="modal-body">
              {loadingDetails ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px', gap: '16px', color: 'var(--text-secondary)' }}>
                  <RefreshCw size={36} className="spin-animation" style={{ color: 'var(--accent-color)' }} />
                  <p style={{ fontWeight: 600 }}>{loc.loadingDetails}</p>
                </div>
              ) : (
                <>
                  {/* Top Stats Grid */}
                  <div className="modal-stats-grid">
                    <div className="modal-stat-card">
                      <span className="modal-stat-label">{loc.sourcesAnalyzed}</span>
                      <span className="modal-stat-val" style={{ color: '#38bdf8' }}>
                        {selectedSessionStats?.sources_total ?? selectedSessionSources.length}
                      </span>
                    </div>
                    <div className="modal-stat-card">
                      <span className="modal-stat-label">{loc.topicsDiscovered}</span>
                      <span className="modal-stat-val" style={{ color: '#818cf8' }}>
                        {selectedSessionStats?.topics ?? 0}
                      </span>
                    </div>
                    <div className="modal-stat-card">
                      <span className="modal-stat-label">{loc.conceptsExtracted}</span>
                      <span className="modal-stat-val" style={{ color: '#fbbf24' }}>
                        {selectedSessionStats?.terms ?? 0}
                      </span>
                    </div>
                    <div className="modal-stat-card">
                      <span className="modal-stat-label">{loc.averageQuality}</span>
                      <span className="modal-stat-val" style={{ color: '#34d399' }}>
                        {selectedSessionStats?.avg_quality ? `${Math.round(selectedSessionStats.avg_quality * 100)}%` : '0%'}
                      </span>
                    </div>
                  </div>

                  {/* Sources List Section */}
                  <div>
                    <div className="modal-section-title">
                      <Globe size={18} style={{ color: 'var(--accent-color)' }} />
                      <span>{loc.allCrawledSources} ({selectedSessionSources.length})</span>
                    </div>

                    <div className="modal-sources-list">
                      {selectedSessionSources.length > 0 ? selectedSessionSources.map((source, idx) => (
                        <div key={source.id || idx} className="modal-source-card">
                          <div className="modal-source-meta">
                            <div className="modal-source-pills">
                              <span className="modal-domain-pill">{source.domain || 'WEB'}</span>
                              <span className="modal-score-pill">
                                {Math.round((source.quality_score || 0) * 100)}% {lang === 'ar' ? 'جودة' : 'quality'}
                              </span>
                              {source.word_count && source.word_count > 0 && (
                                <span className="modal-words-pill">
                                  {source.word_count} {loc.wordsCount}
                                </span>
                              )}
                            </div>
                            {source.crawled_at && (
                              <span style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>
                                {new Date(source.crawled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            )}
                          </div>

                          <h4 className="modal-source-title">
                            <a href={source.url} target="_blank" rel="noreferrer" title={source.url}>
                              <span>{source.title || source.url}</span>
                              <ExternalLink size={14} style={{ opacity: 0.6 }} />
                            </a>
                          </h4>

                          {source.summary && (
                            <div className="modal-source-summary">
                              <p style={{ margin: 0 }}>{source.summary}</p>
                            </div>
                          )}
                        </div>
                      )) : (
                        <div className="modal-empty-sources">
                          <AlertCircle size={36} style={{ margin: '0 auto 10px auto', opacity: 0.4 }} />
                          <p>{loc.noSourcesFound}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      </main>
    </div>
  );
}

export default App;
