import { useState, useEffect, useRef } from 'react';
import { 
  Sun, Moon, Settings, Database, Clock, 
  Play, Square, Save, Download, Globe, 
  Terminal, Activity, RefreshCw, Home, Languages, Trash2
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
    sourcesAnalyzed: 'المصادر المحللة',
    settingsAndNumbers: 'هنا الإعدادات والأرقام',
    searchDepth: 'عمق البحث',
    maxSources: 'الحد الأقصى للمصادر',
    start: 'البدء',
    stop: 'إيقاف العمل',
    save: 'الحفظ',
    export: 'التصدير',
    browserWait: 'نافذة Chrome للزحف الآلي...',
    browserSearching: 'البحث عن',
    browserExploring: 'يتم الآن استعراض الصفحات واستخراج المعرفة...',
    browserStopped: 'نافذة Chrome (متوقفة)',
    logTab: 'نافذة Log',
    terminalTab: 'نافذة التيرمنل',
    enterTopicError: 'الرجاء إدخال موضوع البحث أولاً!',
    connecting: 'جاري الاتصال بالخادم لبدء الزحف عن:',
    startSuccess: 'تم بدء عملية الزحف بنجاح! معرف الجلسة:',
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
    saveSuccess: 'تم حفظ وتحديث الجلسة بنجاح.'
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
    sourcesAnalyzed: 'Sources Analyzed',
    settingsAndNumbers: 'Settings & Parameters',
    searchDepth: 'Search Depth',
    maxSources: 'Max Sources',
    start: 'Start',
    stop: 'Stop',
    save: 'Save',
    export: 'Export',
    browserWait: 'Chrome window for autonomous crawling...',
    browserSearching: 'Searching for',
    browserExploring: 'Browsing pages and extracting knowledge...',
    browserStopped: 'Chrome window (stopped)',
    logTab: 'Log Window',
    terminalTab: 'Terminal Window',
    enterTopicError: 'Please enter a search topic first!',
    connecting: 'Connecting to server to start crawl for:',
    startSuccess: 'Crawl process started successfully! Session ID:',
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
    saveSuccess: 'Session saved and updated successfully.'
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
  

  const [browserHeight, setBrowserHeight] = useState(350);
  const isDragging = useRef(false);

  const loc = t[lang];

  const [historyList, setHistoryList] = useState<SessionHistoryItem[]>([]);

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
    } else {
      setElapsedTime('00:00:00');
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
              sources: res.data.sources_total || 0,
              topics: res.data.topics || 0
            });
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 3000) as unknown as number;
    }
    return () => clearInterval(pollInterval);
  }, [isRunning, sessionId]);

  const addLog = (type: 'info'|'success'|'error'|'sys', message: string) => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), type, message }]);
  };

  const handleStart = async () => {
    if (!searchQuery.trim()) {
      addLog('error', loc.enterTopicError);
      return;
    }
    
    setIsRunning(true);
    setStats({ sources: 0, topics: 0 });
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
      addLog('info', loc.crawlStopped);
    }
  };

  const handleDeleteSession = async (id: string) => {
    if (!window.confirm(loc.deleteConfirm)) return;
    try {
      await axios.delete(`${API_BASE}/session/${id}`);
      setHistoryList(prev => prev.filter(s => s.id !== id));
      addLog('success', `${loc.deleteSuccess} (${id.slice(0, 8)}...)`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      addLog('error', `${loc.serverError} ${msg}`);
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
        <div className="header-right">
          <div className="timer-box">
            <Clock size={18} />
            <span>{elapsedTime}</span>
            <span style={{ fontSize: '0.8rem', opacity: 0.8, margin: '0 4px' }}>{loc.timeSince}</span>
          </div>
        </div>

        <div className="header-title" style={{ cursor: 'pointer' }} onClick={() => setPage('home')}>
          {loc.title}
        </div>

        <div className="header-left">
          <button className={`btn-text ${page === 'home' ? 'active-page' : ''}`} onClick={() => setPage('home')}>
            <Home size={18} /> {loc.home}
          </button>
          <button className={`btn-text ${page === 'history' ? 'active-page' : ''}`} onClick={() => setPage('history')}>
            <Database size={18} /> {loc.history}
          </button>


          <div style={{ width: '1px', height: '24px', background: 'var(--panel-border)', margin: '0 8px' }}></div>

          <button className="btn-icon" onClick={toggleLang} title="تغيير اللغة / Change Language">
            <Languages size={20} />
          </button>

          <button className="btn-icon" onClick={toggleTheme} title="تغيير المظهر">
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
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

                <div className="stat-card">
                  <span className="stat-label">{loc.systemStatus}</span>
                  <span className="stat-value" style={{ fontSize: '1.2rem', color: isRunning ? 'var(--success-color)' : 'var(--text-secondary)' }}>
                    {isRunning ? loc.statusRunning : loc.statusStopped}
                  </span>
                </div>
                <div className="stat-card">
                  <span className="stat-label">{loc.sourcesAnalyzed}</span>
                  <span className="stat-value">{stats.sources}</span>
                </div>
              </div>

              <div className="sidebar-section" style={{ flex: 1 }}>
                <h2 className="sidebar-title"><Activity size={20} /> {loc.settingsAndNumbers}</h2>
                <div className="config-box">
                   <label>{loc.searchDepth}: {maxDepth}</label>
                   <input type="range" min="1" max="5" value={maxDepth} onChange={(e)=>setMaxDepth(Number(e.target.value))} disabled={isRunning} />
                </div>
                <div className="config-box">
                   <label>{loc.maxSources}: {maxSources}</label>
                   <input type="range" min="1" max="50" value={maxSources} onChange={(e)=>setMaxSources(Number(e.target.value))} disabled={isRunning} />
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
                    <span>{isRunning ? `${loc.browserSearching}: ${searchQuery}...` : loc.browserWait}</span>
                  </div>
                  <button className="btn-icon" style={{ width: '28px', height: '28px', border: 'none' }}>
                    <RefreshCw size={14} />
                  </button>
                </div>
                <div className="browser-content">
                  {isRunning ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', color: 'var(--text-secondary)' }}>
                      <Globe size={64} className="pulse-animation" style={{ opacity: 0.5 }} />
                      <p style={{ fontSize: '1.2rem', fontWeight: 600 }}>{loc.browserExploring}</p>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', color: 'var(--panel-border)' }}>
                      <Globe size={64} />
                      <p style={{ fontSize: '1.2rem', fontWeight: 600 }}>{loc.browserStopped}</p>
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
                  {activeTab === 'log' ? renderLogs() : (
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
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <Database size={28} color="var(--accent-color)" />
              <h2>{loc.historyTitle}</h2>
            </div>
            
            <div className="history-table-container" style={{ background: 'rgba(0,0,0,0.05)', borderRadius: '12px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: lang === 'ar' ? 'right' : 'left' }}>
                <thead>
                  <tr style={{ background: 'rgba(0,0,0,0.1)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '16px' }}>{loc.sessionID}</th>
                    <th style={{ padding: '16px' }}>{loc.topic}</th>
                    <th style={{ padding: '16px' }}>{loc.sourcesAnalyzed}</th>
                    <th style={{ padding: '16px' }}>{loc.statusCol}</th>
                    <th style={{ padding: '16px', textAlign: 'center' }}>{loc.actions}</th>
                  </tr>
                </thead>
                <tbody>
                  {historyList.length > 0 ? historyList.map(session => (
                    <tr key={session.id} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                      <td style={{ padding: '16px' }}>{session.id.slice(0, 8)}...</td>
                      <td style={{ padding: '16px' }}>{session.topic}</td>
                      <td style={{ padding: '16px' }}>{session.sources_analyzed || 0}</td>
                      <td style={{ padding: '16px' }}>
                        <span style={{ 
                          padding: '4px 8px', 
                          borderRadius: '12px', 
                          fontSize: '0.8rem',
                          background: session.status === 'complete' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                          color: session.status === 'complete' ? '#22c55e' : '#eab308'
                        }}>
                          {session.status}
                        </span>
                      </td>
                      <td style={{ padding: '16px', textAlign: 'center' }}>
                         <button 
                           className="btn-icon" 
                           title={lang === 'ar' ? 'حذف الجلسة' : 'Delete Session'}
                           onClick={() => handleDeleteSession(session.id)}
                         >
                           <Trash2 size={16} />
                         </button>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={5} style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        {loc.noData}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
