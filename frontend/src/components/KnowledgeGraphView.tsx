import React, { useEffect, useRef, useState, useMemo } from 'react';
import axios from 'axios';
import {
  Users,
  Building2,
  Lightbulb,
  FileText,
  Search,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sparkles,
  ExternalLink,
  X,
  Layers,
  Compass
} from 'lucide-react';

interface GraphNode {
  id: string;
  name: string;
  type: 'person' | 'organization' | 'concept' | 'publication';
  val: number;
  details?: string;
  url?: string;
  is_root?: boolean;
  degree?: number;
  pagerank?: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
  weight: number;
}

interface GraphData {
  session_id: string;
  seed_topic: string;
  entity_type: string;
  stats: {
    total_nodes: number;
    total_edges: number;
    people_count: number;
    orgs_count: number;
    concepts_count: number;
    publications_count: number;
    density: number;
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
  categories: { id: string; label: string; color: string }[];
}

interface SessionOption {
  id: string;
  topic: string;
  sources_analyzed: number;
}

interface KnowledgeGraphViewProps {
  currentSessionId: string | null;
  apiBase: string;
  lang: 'ar' | 'en';
  onExpandTopic?: (topicName: string) => void;
}

const TYPE_COLORS: Record<string, { bg: string; border: string; glow: string }> = {
  root: { bg: '#38bdf8', border: '#0284c7', glow: 'rgba(56, 189, 248, 0.6)' },
  person: { bg: '#10b981', border: '#059669', glow: 'rgba(16, 185, 129, 0.45)' },
  organization: { bg: '#a855f7', border: '#7e22ce', glow: 'rgba(168, 85, 247, 0.45)' },
  concept: { bg: '#06b6d4', border: '#0891b2', glow: 'rgba(6, 182, 212, 0.45)' },
  publication: { bg: '#f43f5e', border: '#e11d48', glow: 'rgba(244, 63, 94, 0.45)' },
};

export const KnowledgeGraphView: React.FC<KnowledgeGraphViewProps> = ({
  currentSessionId,
  apiBase,
  lang,
  onExpandTopic
}) => {
  const [sessions, setSessions] = useState<SessionOption[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>(currentSessionId || '');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // High-performance refs for 60fps canvas loop without React state thrashing
  const hoveredNodeIdRef = useRef<string | null>(null);
  const selectedNodeRef = useRef<GraphNode | null>(null);
  const selectedCategoryRef = useRef<string>('all');
  const searchQueryRef = useRef<string>('');
  const alphaRef = useRef<number>(1.0);

  useEffect(() => { selectedNodeRef.current = selectedNode; }, [selectedNode]);
  useEffect(() => { selectedCategoryRef.current = selectedCategory; }, [selectedCategory]);
  useEffect(() => { searchQueryRef.current = searchQuery; }, [searchQuery]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement | null>(null);

  // Transform / Camera state
  const cameraRef = useRef({ x: 0, y: 0, zoom: 1.0 });
  const isDraggingCamera = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const draggedNode = useRef<GraphNode | null>(null);

  // Simulation physics state
  const simNodes = useRef<GraphNode[]>([]);
  const simEdges = useRef<GraphEdge[]>([]);
  const animFrameId = useRef<number | null>(null);

  // Background deep space cosmic stars
  const starsPathRef = useRef<Path2D | null>(null);
  useEffect(() => {
    const p = new Path2D();
    for (let i = 0; i < 90; i++) {
      const x = (Math.random() - 0.5) * 2800;
      const y = (Math.random() - 0.5) * 2000;
      const r = Math.random() * 1.1 + 0.35;
      p.arc(x, y, r, 0, Math.PI * 2);
      p.closePath();
    }
    starsPathRef.current = p;
  }, []);

  // Fetch all sessions for dropdown selector
  useEffect(() => {
    axios.get<SessionOption[]>(`${apiBase}/sessions`)
      .then(res => {
        setSessions(res.data || []);
        if (!selectedSessionId && res.data && res.data.length > 0) {
          setSelectedSessionId(res.data[0].id);
        }
      })
      .catch(err => console.error("Error loading graph sessions:", err));
  }, [apiBase]);

  // Update selected session if prop changes
  useEffect(() => {
    if (currentSessionId) {
      setSelectedSessionId(currentSessionId);
    }
  }, [currentSessionId]);

  // Fetch graph data for selected session
  useEffect(() => {
    if (!selectedSessionId) return;
    setLoading(true);
    setSelectedNode(null);
    axios.get<GraphData>(`${apiBase}/graph/${selectedSessionId}?lang=${lang}`)
      .then(res => {
        setGraphData(res.data);
        initSimulation(res.data);
      })
      .catch(err => console.error("Error fetching graph data:", err))
      .finally(() => setLoading(false));
  }, [selectedSessionId, apiBase, lang]);

  // Initialize simulation positions
  const initSimulation = (data: GraphData) => {
    const width = canvasContainerRef.current?.clientWidth || 900;
    const height = canvasContainerRef.current?.clientHeight || 600;

    cameraRef.current = { x: width / 2, y: height / 2, zoom: 1.0 };
    alphaRef.current = 1.0;

    const rootNode = data.nodes.find(n => n.is_root);
    const nonRootNodes = data.nodes.filter(n => !n.is_root);
    const total = nonRootNodes.length;

    const nodesCopy: GraphNode[] = [];

    if (rootNode) {
      nodesCopy.push({
        ...rootNode,
        x: 0,
        y: 0,
        vx: 0,
        vy: 0,
        fx: 0,
        fy: 0,
      });
    }

    nonRootNodes.forEach((n, idx) => {
      let orbitRadius = 220;
      if (n.type === 'organization') orbitRadius = 180;
      else if (n.type === 'person') orbitRadius = 260;
      else if (n.type === 'concept') orbitRadius = 340;
      else if (n.type === 'publication') orbitRadius = 420;

      const angle = (idx / Math.max(1, total)) * 2 * Math.PI + (idx % 2 === 0 ? 0.15 : -0.15);
      const r = orbitRadius + (idx % 3) * 30;
      const x = Math.cos(angle) * r;
      const y = Math.sin(angle) * r;

      nodesCopy.push({
        ...n,
        x,
        y,
        vx: 0,
        vy: 0,
        fx: null,
        fy: null,
      });
    });

    simNodes.current = nodesCopy;
    simEdges.current = data.edges;
  };

  // Connected nodes map for highlighting
  const connectedMap = useMemo(() => {
    const map = new Map<string, Set<string>>();
    if (!graphData) return map;
    graphData.edges.forEach(e => {
      if (!map.has(e.source)) map.set(e.source, new Set());
      if (!map.has(e.target)) map.set(e.target, new Set());
      map.get(e.source)!.add(e.target);
      map.get(e.target)!.add(e.source);
    });
    return map;
  }, [graphData]);

  // Physics simulation step with thermal cooling
  const tickPhysics = () => {
    if (alphaRef.current < 0.003) return;
    const alpha = alphaRef.current;

    const nodes = simNodes.current;
    const edges = simEdges.current;
    const count = nodes.length;
    if (count === 0) return;

    // Node-Node Repulsion (Coulomb)
    for (let i = 0; i < count; i++) {
      for (let j = i + 1; j < count; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x! - a.x!;
        const dy = b.y! - a.y!;
        const distSq = dx * dx + dy * dy + 1;
        const dist = Math.sqrt(distSq);
        if (dist < 420) {
          const force = (16000 / distSq) * alpha;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          if (a.fx === null || a.fx === undefined) { a.vx! -= fx; a.vy! -= fy; }
          if (b.fx === null || b.fx === undefined) { b.vx! += fx; b.vy! += fy; }
        }
      }
    }

    // Edge Attraction (Hooke's Spring)
    const nodeById = new Map<string, GraphNode>();
    nodes.forEach(n => nodeById.set(n.id, n));

    edges.forEach(e => {
      const a = nodeById.get(e.source);
      const b = nodeById.get(e.target);
      if (!a || !b) return;

      const dx = b.x! - a.x!;
      const dy = b.y! - a.y!;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 200 * (1 / Math.sqrt(e.weight || 1));
      const delta = dist - targetDist;
      const force = delta * 0.015 * alpha;

      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (a.fx === null || a.fx === undefined) { a.vx! -= fx; a.vy! -= fy; }
      if (b.fx === null || b.fx === undefined) { b.vx! += fx; b.vy! += fy; }
    });

    // Center Gravity & Damping
    nodes.forEach(n => {
      if (n.fx === null || n.fx === undefined) {
        n.vx! -= n.x! * 0.0005 * alpha;
        n.vy! -= n.y! * 0.0005 * alpha;

        n.vx! *= 0.88;
        n.vy! *= 0.88;

        n.x! += n.vx!;
        n.y! += n.vy!;
      } else {
        if (typeof n.fx === 'number') n.x = n.fx;
        if (typeof n.fy === 'number') n.y = n.fy;
      }
    });

    alphaRef.current *= 0.985;
  };

  // Canvas render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let isRunning = true;

    const render = () => {
      if (!isRunning) return;

      // Resize canvas to match display size of canvas container with DPR
      const container = canvasContainerRef.current;
      const width = container ? container.clientWidth : 800;
      const height = container ? container.clientHeight : 600;
      const dpr = window.devicePixelRatio || 1;

      const targetW = Math.round(width * dpr);
      const targetH = Math.round(height * dpr);

      if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
      }

      ctx.save();
      ctx.scale(dpr, dpr);

      // Pure deep space black background
      ctx.fillStyle = '#020408';
      ctx.fillRect(0, 0, width, height);

      // Apply camera pan & zoom
      const cam = cameraRef.current;
      ctx.translate(cam.x, cam.y);
      ctx.scale(cam.zoom, cam.zoom);

      // Draw subtle background celestial stars
      if (starsPathRef.current) {
        ctx.fillStyle = 'rgba(224, 242, 254, 0.35)';
        ctx.fill(starsPathRef.current);
      }

      // Run 1 physics tick per frame
      tickPhysics();

      const nodes = simNodes.current;
      const edges = simEdges.current;
      const nodeById = new Map<string, GraphNode>();
      nodes.forEach(n => nodeById.set(n.id, n));

      // Filter state using current refs
      const currentCat = selectedCategoryRef.current;
      const currentQuery = searchQueryRef.current;
      const isFiltered = (n: GraphNode) => {
        if (currentCat !== 'all' && n.type !== currentCat && !n.is_root) return false;
        if (currentQuery.trim() && !n.name.toLowerCase().includes(currentQuery.toLowerCase())) return false;
        return true;
      };

      const activeTargetId = selectedNodeRef.current?.id || hoveredNodeIdRef.current;

      // Draw Edges
      edges.forEach(e => {
        const u = nodeById.get(e.source);
        const v = nodeById.get(e.target);
        if (!u || !v) return;

        const uVisible = isFiltered(u);
        const vVisible = isFiltered(v);
        if (!uVisible && !vVisible) return;

        const isHighlighted = activeTargetId && (u.id === activeTargetId || v.id === activeTargetId);
        const isDimmed = activeTargetId && !isHighlighted;

        ctx.beginPath();
        ctx.moveTo(u.x!, u.y!);
        ctx.lineTo(v.x!, v.y!);

        if (isHighlighted) {
          ctx.strokeStyle = '#38bdf8';
          ctx.lineWidth = 2.5;
        } else if (isDimmed) {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
          ctx.lineWidth = 1;
        } else {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
          ctx.lineWidth = 1.2;
        }
        ctx.stroke();

        // Edge label when highlighted
        if (isHighlighted && e.label) {
          const midX = (u.x! + v.x!) / 2;
          const midY = (u.y! + v.y!) / 2;
          ctx.save();
          ctx.font = '10px Cairo, Inter, sans-serif';
          ctx.fillStyle = '#60a5fa';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(e.label, midX, midY - 6);
          ctx.restore();
        }
      });

      // Draw Nodes
      nodes.forEach(n => {
        if (!isFiltered(n)) return;
        const isSelected = selectedNodeRef.current?.id === n.id;
        const isHovered = hoveredNodeIdRef.current === n.id;
        const isConnected = activeTargetId && (n.id === activeTargetId || connectedMap.get(activeTargetId)?.has(n.id));
        const isDimmed = activeTargetId && !isConnected;

        const conf = TYPE_COLORS[n.is_root ? 'root' : n.type] || TYPE_COLORS.concept;
        const baseRadius = n.is_root ? 18 : (n.degree && n.degree > 3 ? 13 : 10);
        const radius = isSelected || isHovered ? baseRadius * 1.25 : baseRadius;

        ctx.save();
        ctx.translate(n.x!, n.y!);

        // Outer Glow for Root or Highlighted Node
        if (n.is_root || isSelected || isHovered) {
          ctx.beginPath();
          ctx.arc(0, 0, radius + 8, 0, Math.PI * 2);
          ctx.fillStyle = conf.glow;
          ctx.fill();
        }

        // Concentric radar ring for root
        if (n.is_root) {
          ctx.beginPath();
          ctx.arc(0, 0, radius + 12, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)';
          ctx.lineWidth = 1.4;
          ctx.setLineDash([3, 3]);
          ctx.stroke();
          ctx.setLineDash([]);
        }

        // Node Circle
        ctx.beginPath();
        ctx.arc(0, 0, radius, 0, Math.PI * 2);
        ctx.fillStyle = isDimmed ? 'rgba(40, 44, 56, 0.35)' : conf.bg;
        ctx.fill();

        ctx.lineWidth = isSelected ? 2.8 : 1.6;
        ctx.strokeStyle = isDimmed ? 'rgba(255, 255, 255, 0.08)' : conf.border;
        ctx.stroke();

        // Node Label
        ctx.font = (n.is_root ? "bold 11px" : "600 10px") + " Cairo, Inter, sans-serif";
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        const labelText = n.name.length > 24 ? n.name.slice(0, 24) + '...' : n.name;

        // Label Background Pill
        const textWidth = ctx.measureText(labelText).width;
        ctx.fillStyle = isDimmed ? 'rgba(10, 10, 14, 0.25)' : 'rgba(8, 12, 22, 0.88)';
        ctx.beginPath();
        ctx.roundRect(-textWidth / 2 - 6, radius + 4, textWidth + 12, 17, 4);
        ctx.fill();
        ctx.strokeStyle = isDimmed ? 'transparent' : (isSelected ? '#38bdf8' : 'rgba(255, 255, 255, 0.14)');
        ctx.stroke();

        ctx.fillStyle = isDimmed ? '#64748b' : (isSelected ? '#38bdf8' : '#f8fafc');
        ctx.fillText(labelText, 0, radius + 6);

        ctx.restore();
      });

      ctx.restore();
      animFrameId.current = requestAnimationFrame(render);
    };

    animFrameId.current = requestAnimationFrame(render);
    return () => {
      isRunning = false;
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [graphData, connectedMap]);

  // Screen coordinate to graph world coordinate
  const screenToWorld = (screenX: number, screenY: number) => {
    const cam = cameraRef.current;
    return {
      x: (screenX - cam.x) / cam.zoom,
      y: (screenY - cam.y) / cam.zoom,
    };
  };

  // Find node under cursor with generous hit area
  const getNodeAtPosition = (screenX: number, screenY: number): GraphNode | null => {
    const { x, y } = screenToWorld(screenX, screenY);
    const currentCat = selectedCategoryRef.current;
    const currentQuery = searchQueryRef.current;

    for (let i = simNodes.current.length - 1; i >= 0; i--) {
      const n = simNodes.current[i];
      if (currentCat !== 'all' && n.type !== currentCat && !n.is_root) continue;
      if (currentQuery.trim() && !n.name.toLowerCase().includes(currentQuery.toLowerCase())) continue;

      const baseRadius = n.is_root ? 18 : (n.degree && n.degree > 3 ? 13 : 10);
      const hitRadius = Math.max(baseRadius + 14, 26);
      const dx = n.x! - x;
      const dy = n.y! - y;

      // Node circle hit
      if (dx * dx + dy * dy <= hitRadius * hitRadius) {
        return n;
      }

      // Label pill hit
      if (Math.abs(dx) <= 65 && dy >= -baseRadius && dy <= -(baseRadius + 24)) {
        return n;
      }
    }
    return null;
  };

  const mouseDownPos = useRef({ x: 0, y: 0 });
  const hasDragged = useRef(false);

  // Mouse handlers for drag, pan, zoom
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;

    mouseDownPos.current = { x: e.clientX, y: e.clientY };
    hasDragged.current = false;

    const hit = getNodeAtPosition(sx, sy);
    if (hit) {
      draggedNode.current = hit;
      alphaRef.current = Math.max(alphaRef.current, 0.4);
    } else {
      isDraggingCamera.current = true;
      dragStart.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;

    const dist = Math.hypot(e.clientX - mouseDownPos.current.x, e.clientY - mouseDownPos.current.y);
    if (dist > 8) {
      hasDragged.current = true;
    }

    if (draggedNode.current) {
      if (hasDragged.current) {
        const { x, y } = screenToWorld(sx, sy);
        draggedNode.current.fx = x;
        draggedNode.current.fy = y;
        draggedNode.current.x = x;
        draggedNode.current.y = y;
        draggedNode.current.vx = 0;
        draggedNode.current.vy = 0;
        alphaRef.current = Math.max(alphaRef.current, 0.3);
      }
    } else if (isDraggingCamera.current) {
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      cameraRef.current.x += dx;
      cameraRef.current.y += dy;
      dragStart.current = { x: e.clientX, y: e.clientY };
    } else {
      const hit = getNodeAtPosition(sx, sy);
      hoveredNodeIdRef.current = hit ? hit.id : null;
      if (canvasRef.current) {
        canvasRef.current.style.cursor = hit ? 'pointer' : 'grab';
      }
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      const sx = e.clientX - rect.left;
      const sy = e.clientY - rect.top;

      if (!hasDragged.current) {
        // Pure click: select hit node or deselect
        const hit = getNodeAtPosition(sx, sy) || draggedNode.current;
        if (hit) {
          setSelectedNode(prev => (prev?.id === hit.id ? null : hit));
        } else {
          setSelectedNode(null);
        }
      }
    }

    if (draggedNode.current) {
      if (hasDragged.current && !draggedNode.current.is_root) {
        draggedNode.current.fx = null;
        draggedNode.current.fy = null;
      }
      draggedNode.current = null;
    }

    isDraggingCamera.current = false;
    hasDragged.current = false;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88;
    const newZoom = Math.max(0.2, Math.min(3.5, cameraRef.current.zoom * zoomFactor));

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const sx = e.clientX - rect.left;
    const sy = e.clientY - rect.top;

    // Zoom towards cursor
    cameraRef.current.x = sx - (sx - cameraRef.current.x) * (newZoom / cameraRef.current.zoom);
    cameraRef.current.y = sy - (sy - cameraRef.current.y) * (newZoom / cameraRef.current.zoom);
    cameraRef.current.zoom = newZoom;
    alphaRef.current = Math.max(alphaRef.current, 0.2);
  };

  const resetCamera = () => {
    const width = canvasContainerRef.current?.clientWidth || 900;
    const height = canvasContainerRef.current?.clientHeight || 600;
    cameraRef.current = { x: width / 2, y: height / 2, zoom: 1.0 };
    alphaRef.current = 0.8;
  };

  const getNodeTypeBadge = (type: string, isRoot?: boolean) => {
    if (isRoot) return { label: lang === 'ar' ? 'الكيان الرئيسي' : 'Root Entity', icon: Sparkles, color: '#38bdf8' };
    switch (type) {
      case 'person': return { label: lang === 'ar' ? 'شخص / زميل' : 'Person / Colleague', icon: Users, color: '#10b981' };
      case 'organization': return { label: lang === 'ar' ? 'مؤسسة / جامعة' : 'University / Org', icon: Building2, color: '#a855f7' };
      case 'publication': return { label: lang === 'ar' ? 'بحث / منشور' : 'Publication', icon: FileText, color: '#f43f5e' };
      default: return { label: lang === 'ar' ? 'مفهوم / تخصص' : 'Concept / Domain', icon: Lightbulb, color: '#06b6d4' };
    }
  };

  return (
    <div className="glass-panel knowledge-graph-panel">
      {/* Top Header Bar - Exact match to Image 1 & 2 */}
      <div className="graph-header-bar">
        <div className="graph-title-group">
          <div>
            <div className="graph-main-title-row">
              <h2 className="graph-main-title">
                {lang === 'ar' ? 'مخطط المعرفة وشبكة العلاقات (Knowledge Graph)' : 'Knowledge Graph & Relations'}
              </h2>
              {graphData?.seed_topic && (
                <span className="graph-seed-badge">{graphData.seed_topic}</span>
              )}
            </div>
            <p className="graph-subtitle">
              {lang === 'ar'
                ? 'استكشاف بصري تفاعلي للأشخاص والزملاء، الجامعات، والمفاهيم المترابطة'
                : 'Interactive visual exploration of peers, institutions, and connected concepts'}
              {graphData?.stats && (
                <span className="graph-stats-subtext">
                  {' • '}{graphData.stats.total_nodes} {lang === 'ar' ? 'عقدة مستخلصة' : 'nodes'} • {graphData.stats.total_edges} {lang === 'ar' ? 'علاقة مترابطة' : 'relationships'}
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Controls: Search & Session dropdown */}
        <div className="graph-controls-group">
          <div className="graph-search-wrapper">
            <Search size={14} className="graph-search-icon" />
            <input
              type="text"
              className="graph-search-input"
              placeholder={lang === 'ar' ? 'بحث عن شخص أو مفهوم...' : 'Search person or concept...'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="graph-search-clear"
                onClick={() => setSearchQuery('')}
                title={lang === 'ar' ? 'مسح' : 'Clear'}
              >
                <X size={12} />
              </button>
            )}
          </div>

          <select
            className="graph-session-select"
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.topic || s.id.slice(0, 8)} ({s.sources_analyzed || 0} {lang === 'ar' ? 'مصادر' : 'sources'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category Filter Pills & Statistics Bar */}
      <div className="graph-toolbar">
        <div className="category-pills-row">
          <button
            type="button"
            className={`cat-pill ${selectedCategory === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('all')}
          >
            <Layers size={13} />
            <span>{lang === 'ar' ? 'الكل' : 'All'} ({graphData?.stats.total_nodes || 0})</span>
          </button>
          <button
            type="button"
            className={`cat-pill cat-person ${selectedCategory === 'person' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('person')}
          >
            <Users size={13} />
            <span>{lang === 'ar' ? 'الأشخاص والزملاء' : 'People & Peers'} ({graphData?.stats.people_count || 0})</span>
          </button>
          <button
            type="button"
            className={`cat-pill cat-org ${selectedCategory === 'organization' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('organization')}
          >
            <Building2 size={13} />
            <span>{lang === 'ar' ? 'المؤسسات والجامعات' : 'Universities & Orgs'} ({graphData?.stats.orgs_count || 0})</span>
          </button>
          <button
            type="button"
            className={`cat-pill cat-concept ${selectedCategory === 'concept' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('concept')}
          >
            <Lightbulb size={13} />
            <span>{lang === 'ar' ? 'المفاهيم والتخصصات' : 'Concepts & Fields'} ({graphData?.stats.concepts_count || 0})</span>
          </button>
          <button
            type="button"
            className={`cat-pill cat-pub ${selectedCategory === 'publication' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('publication')}
          >
            <FileText size={13} />
            <span>{lang === 'ar' ? 'الأوراق والمنشورات' : 'Publications'} ({graphData?.stats.publications_count || 0})</span>
          </button>
        </div>

        {/* Canvas Camera Zoom Controls */}
        <div className="graph-camera-controls">
          <button
            type="button"
            className="cam-btn"
            onClick={() => {
              cameraRef.current.zoom = Math.min(3.5, cameraRef.current.zoom * 1.25);
              alphaRef.current = Math.max(alphaRef.current, 0.2);
            }}
            title={lang === 'ar' ? 'تكبير (+)' : 'Zoom In'}
          >
            <ZoomIn size={16} />
          </button>
          <button
            type="button"
            className="cam-btn"
            onClick={() => {
              cameraRef.current.zoom = Math.max(0.2, cameraRef.current.zoom * 0.8);
              alphaRef.current = Math.max(alphaRef.current, 0.2);
            }}
            title={lang === 'ar' ? 'تصغير (-)' : 'Zoom Out'}
          >
            <ZoomOut size={16} />
          </button>
          <button
            type="button"
            className="cam-btn"
            onClick={resetCamera}
            title={lang === 'ar' ? 'إعادة ضبط العرض' : 'Reset View'}
          >
            <RotateCcw size={15} />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="graph-canvas-container" ref={canvasContainerRef}>
        {loading && (
          <div className="graph-loading-overlay">
            <div className="graph-loading-spinner" />
            <p>{lang === 'ar' ? 'جاري بناء وتحليل شبكة المعرفة واستخراج العلاقات...' : 'Building knowledge graph and mapping relationships...'}</p>
          </div>
        )}

        <canvas
          ref={canvasRef}
          className="graph-canvas"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        />

        {/* Selected Node Details Card (Side Panel) */}
        {selectedNode && (
          <div className="node-inspector-card" onClick={(e) => e.stopPropagation()}>
            <div className="inspector-header">
              <div className="inspector-badge" style={{ color: getNodeTypeBadge(selectedNode.type, selectedNode.is_root).color }}>
                {React.createElement(getNodeTypeBadge(selectedNode.type, selectedNode.is_root).icon, { size: 14 })}
                <span>{getNodeTypeBadge(selectedNode.type, selectedNode.is_root).label}</span>
              </div>
              <button
                type="button"
                className="inspector-close-btn"
                onClick={() => setSelectedNode(null)}
                title={lang === 'ar' ? 'إغلاق' : 'Close'}
              >
                <X size={15} />
              </button>
            </div>

            <h3 className="inspector-title" style={{ color: getNodeTypeBadge(selectedNode.type, selectedNode.is_root).color }}>
              {selectedNode.name}
            </h3>

            <p className="inspector-desc">
              {selectedNode.details || (lang === 'ar' ? 'كيان مستخلص ضمن شبكة المعرفة.' : 'Entity mapped in knowledge network.')}
            </p>

            <div className="inspector-stats-row">
              <div className="inspector-stat">
                <span className="stat-label">{lang === 'ar' ? 'درجة الترابط' : 'Degree'}</span>
                <span className="stat-val">{selectedNode.degree || 1}</span>
              </div>
              <div className="inspector-stat">
                <span className="stat-label">{lang === 'ar' ? 'الأهمية النسبية' : 'PageRank'}</span>
                <span className="stat-val">{selectedNode.pagerank ? Math.round(selectedNode.pagerank * 100) : 10}%</span>
              </div>
            </div>

            {/* Connected Neighbors List */}
            {connectedMap.has(selectedNode.id) && (
              <div className="inspector-section">
                <span className="section-title">{lang === 'ar' ? 'الكيانات المرتبطة:' : 'Connected Entities:'}</span>
                <div className="connected-tags-list">
                  {Array.from(connectedMap.get(selectedNode.id) || []).slice(0, 10).map(targetId => {
                    const targetNode = simNodes.current.find(n => n.id === targetId);
                    if (!targetNode) return null;
                    return (
                      <span
                        key={targetId}
                        className="connected-tag"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedNode(targetNode);
                        }}
                        title={targetNode.name}
                      >
                        {targetNode.name}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="inspector-actions">
              {selectedNode.url && (
                <a
                  href={selectedNode.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-inspector-link"
                >
                  <ExternalLink size={13} />
                  <span>{lang === 'ar' ? 'فتح المصدر الأصلي' : 'Open Source'}</span>
                </a>
              )}
              {onExpandTopic && !selectedNode.is_root && (
                <button
                  type="button"
                  className="btn-inspector-expand"
                  onClick={() => onExpandTopic(selectedNode.name)}
                >
                  <Compass size={13} />
                  <span>{lang === 'ar' ? 'بدء زحف حول هذا الكيان' : 'Crawl this entity'}</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
