import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis,
    CartesianGrid, Tooltip, Legend, BarChart, Bar
} from 'recharts';
import {
    Activity, LogOut, Users, AlertTriangle, CheckCircle, Clock, RefreshCw,
    MapPin, Eye, FileText, X, Shield, TrendingUp, Database, Cigarette,
    ChevronRight, AlertCircle, Image, Zap, Search, Download, Calendar, Brain
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

// ── Utilities ─────────────────────────────────────────────────────────────────
function timeAgo(isoStr) {
    if (!isoStr) return '—';
    const diff = (Date.now() - new Date(isoStr).getTime()) / 1000;
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

function useCountUp(target, duration = 800) {
    const [val, setVal] = useState(0);
    useEffect(() => {
        let start = 0;
        const step = target / (duration / 16);
        const timer = setInterval(() => {
            start += step;
            if (start >= target) { setVal(target); clearInterval(timer); }
            else setVal(Math.floor(start));
        }, 16);
        return () => clearInterval(timer);
    }, [target, duration]);
    return val;
}

// ── CSV Export ────────────────────────────────────────────────────────────────
function exportToCSV(rows) {
    if (!rows.length) { toast.error('No data to export'); return; }
    const headers = ['ID', 'Patient ID', 'State/Village', 'Tobacco Type', 'Confidence', 'Status', 'Date'];
    const csvRows = [headers, ...rows.map(r => [
        r.id,
        r.patient_id,
        `${r.state || ''}/${r.village || ''}`,
        r.primary_tobacco_type || r.tobacco_usage ? 'Yes' : 'No',
        `${Math.round(r.confidence * 100)}%`,
        r.status,
        new Date(r.created_at).toLocaleDateString('en-IN'),
    ])];
    const csvContent = csvRows.map(row => row.map(String).map(v => `"${v.replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `oralvision_high_risk_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    toast.success('CSV exported!');
}

// ── Custom Tooltip ─────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-slate-900 border border-white/10 rounded-xl p-3 text-sm shadow-xl">
            <p className="text-slate-400 mb-1 font-medium">{label}</p>
            {payload.map((p, i) => (
                <p key={i} style={{ color: p.color }} className="font-semibold">{p.name}: {p.value}</p>
            ))}
        </div>
    );
};

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, cardClass = 'stat-card', icon, trend }) {
    const numeric = typeof value === 'number' ? value : null;
    const counted = useCountUp(numeric ?? 0);
    const displayVal = numeric !== null ? counted : value;
    return (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -3, scale: 1.02 }} transition={{ duration: 0.3 }} className={`${cardClass} flex flex-col gap-3`}>
            <div className="flex items-start justify-between">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center bg-white/8">{icon}</div>
                {trend !== undefined && (
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${trend >= 0 ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'}`}>
                        {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
                    </span>
                )}
            </div>
            <div>
                <p className="text-3xl font-black tracking-tight">{displayVal}</p>
                <p className="text-slate-400 text-sm mt-0.5">{label}</p>
                {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
            </div>
        </motion.div>
    );
}

// ── Heatmap Panel ─────────────────────────────────────────────────────────────
function HeatmapPanel({ data }) {
    if (!data?.length) return (
        <div className="glass-card p-6 flex flex-col items-center justify-center" style={{ minHeight: 320 }}>
            <MapPin className="w-12 h-12 text-slate-700 mb-3" />
            <p className="text-slate-500 text-sm font-medium">Geographic Heatmap</p>
            <p className="text-slate-600 text-xs mt-1 text-center">Village-level risk data will appear here as screenings are added across India.</p>
        </div>
    );
    const maxDensity = Math.max(...data.map(d => d.risk_density), 0.01);
    return (
        <div className="glass-card p-6">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-red-400" /> Geographic Risk Heatmap – Marathwada
            </h3>
            <div className="relative w-full bg-slate-900/80 rounded-xl overflow-hidden border border-white/5" style={{ height: 280 }}>
                <svg width="100%" height="100%" className="absolute inset-0 opacity-10">
                    {[...Array(8)].map((_, i) => <line key={`h${i}`} x1="0" y1={`${(i + 1) * 12.5}%`} x2="100%" y2={`${(i + 1) * 12.5}%`} stroke="white" strokeWidth="0.5" />)}
                    {[...Array(10)].map((_, i) => <line key={`v${i}`} x1={`${(i + 1) * 10}%`} y1="0" x2={`${(i + 1) * 10}%`} y2="100%" stroke="white" strokeWidth="0.5" />)}
                </svg>
                {data.map((v) => {
                    const latMin = 17.5, latMax = 20.0, lngMin = 74.5, lngMax = 78.0;
                    const x = ((v.lng - lngMin) / (lngMax - lngMin)) * 80 + 10;
                    const y = ((latMax - v.lat) / (latMax - latMin)) * 80 + 10;
                    const intensity = v.risk_density / maxDensity;
                    const r = 12 + intensity * 22;
                    const opacity = 0.3 + intensity * 0.6;
                    return (
                        <g key={v.village}>
                            <circle cx={`${x}%`} cy={`${y}%`} r={r + 10} fill={`rgba(239,68,68,${opacity * 0.15})`} className="animate-pulse-slow" />
                            <circle cx={`${x}%`} cy={`${y}%`} r={r} fill={`rgba(239,68,68,${opacity})`} stroke="rgba(239,68,68,0.5)" strokeWidth="1.5" />
                            <text x={`${x}%`} y={`${y + 0.5}%`} textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="9" fontWeight="600" style={{ textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}>
                                {v.village.length > 8 ? v.village.substring(0, 7) + '.' : v.village}
                            </text>
                        </g>
                    );
                })}
                <div className="absolute bottom-3 left-3 flex items-center gap-3 text-xs text-slate-400">
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-red-900 opacity-50" /><span>Low</span></div>
                    <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-red-500" /><span>High Risk</span></div>
                </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
                {data.map(v => (
                    <div key={v.village} className="bg-white/5 rounded-lg px-3 py-2 flex items-center justify-between hover:bg-white/8 transition-colors">
                        <span className="text-xs text-slate-300 truncate">{v.village}</span>
                        <span className={`text-xs font-bold ml-1 ${v.risk_density > 0.5 ? 'text-red-400' : v.risk_density > 0.25 ? 'text-amber-400' : 'text-emerald-400'}`}>
                            {Math.round(v.risk_density * 100)}%
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── AI Explanation Modal ───────────────────────────────────────────────────────
function AIExplanationModal({ screening, onClose }) {
    const riskColors = { High: 'text-red-400 border-red-500/30 bg-red-500/10', Medium: 'text-amber-400 border-amber-500/30 bg-amber-500/10', Low: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' };
    const cfg = riskColors[screening.risk] || riskColors.Medium;
    return (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
            <motion.div
                initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.92 }}
                className="glass-card p-6 w-full max-w-md" onClick={e => e.stopPropagation()}
            >
                <div className="flex items-start justify-between mb-5">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <Brain className="w-5 h-5 text-violet-400" />
                            <h3 className="font-semibold">AI Clinical Explanation</h3>
                        </div>
                        <p className="text-xs text-slate-500">Patient: {screening.patient_id} · {screening.state || screening.village}</p>
                    </div>
                    <button onClick={onClose}><X className="w-5 h-5 text-slate-400 hover:text-white" /></button>
                </div>

                {/* Risk badge */}
                <div className={`border ${cfg} rounded-xl p-4 mb-4`}>
                    <p className={`text-lg font-black ${cfg.split(' ')[0]} mb-1`}>{screening.risk?.toUpperCase()} RISK</p>
                    <p className="text-xs text-slate-400">Confidence: {Math.round(screening.confidence * 100)}%</p>
                </div>

                {/* Clinical explanation */}
                <div className="bg-slate-900/80 border border-white/5 rounded-xl p-4 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-3.5 h-3.5 text-sky-400" />
                        <p className="text-xs font-bold text-sky-400 uppercase tracking-widest">Gemini AI Reasoning</p>
                    </div>
                    {screening.clinical_explanation ? (
                        <p className="text-sm text-slate-200 leading-relaxed italic">
                            &ldquo;{screening.clinical_explanation}&rdquo;
                        </p>
                    ) : (
                        <p className="text-sm text-slate-500 italic">No clinical explanation available for this record.</p>
                    )}
                </div>

                {/* Context grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-white/5 rounded-xl p-3">
                        <p className="text-xs text-slate-500 mb-0.5">Tobacco Habit</p>
                        <p className="text-sm font-semibold">{screening.primary_tobacco_type || (screening.tobacco_usage ? 'Yes' : 'None')}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                        <p className="text-xs text-slate-500 mb-0.5">State / District</p>
                        <p className="text-sm font-semibold truncate">{screening.state || screening.village || '—'}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                        <p className="text-xs text-slate-500 mb-0.5">Patient Age</p>
                        <p className="text-sm font-semibold">{screening.age || '—'}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                        <p className="text-xs text-slate-500 mb-0.5">Screened</p>
                        <p className="text-sm font-semibold">{new Date(screening.created_at).toLocaleDateString('en-IN')}</p>
                    </div>
                </div>

                <button onClick={onClose} className="btn-secondary w-full text-sm py-2.5">Close</button>
            </motion.div>
        </div>
    );
}

// ── Notes Modal ───────────────────────────────────────────────────────────────
function NotesModal({ screening, onClose, onSave }) {
    const [notes, setNotes] = useState(screening?.notes || '');
    const [saving, setSaving] = useState(false);
    const handleSave = async () => {
        setSaving(true);
        await onSave(screening.id, { notes, status: 'Reviewed' });
        setSaving(false); onClose();
    };
    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card p-6 w-full max-w-md">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="font-semibold">Clinical Notes</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Patient: {screening?.patient_id} · {screening?.state || screening?.village}</p>
                    </div>
                    <button onClick={onClose}><X className="w-5 h-5 text-slate-400 hover:text-white" /></button>
                </div>
                <div className="mb-4">
                    <textarea className="input-field h-32 resize-none" placeholder="Enter clinical notes, referral details, follow-up plan..."
                        value={notes} onChange={e => setNotes(e.target.value)} autoFocus />
                </div>
                <div className="flex gap-3">
                    <button onClick={onClose} className="btn-secondary flex-1 text-sm py-2.5">Cancel</button>
                    <button onClick={handleSave} disabled={saving} className="btn-primary flex-1 text-sm py-2.5 flex items-center justify-center gap-2">
                        {saving ? <><RefreshCw className="w-3 h-3 animate-spin" /> Saving...</> : <><CheckCircle className="w-3.5 h-3.5" /> Mark Reviewed</>}
                    </button>
                </div>
            </motion.div>
        </div>
    );
}

// ── Image Modal ───────────────────────────────────────────────────────────────
function ImageModal({ url, onClose }) {
    return (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4" onClick={onClose}>
            <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} onClick={e => e.stopPropagation()} className="relative max-w-lg w-full">
                <button onClick={onClose} className="absolute -top-10 right-0 text-white/60 hover:text-white"><X className="w-6 h-6" /></button>
                <img src={`http://localhost:8000${url}`} alt="Oral scan" className="w-full rounded-2xl border border-white/10 shadow-2xl"
                    onError={e => { e.target.src = ''; e.target.style.display = 'none'; }} />
            </motion.div>
        </div>
    );
}

// ── Activity Feed ─────────────────────────────────────────────────────────────
function ActivityFeed({ items }) {
    const riskDot = { High: 'bg-red-400', Medium: 'bg-amber-400', Low: 'bg-emerald-400' };
    return (
        <div className="glass-card p-6">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2"><Zap className="w-4 h-4 text-yellow-400" /> Recent Activity</h3>
            <div className="space-y-3">
                {!items?.length && <p className="text-slate-500 text-sm text-center py-4">No recent screenings.</p>}
                {items?.map((s, i) => (
                    <motion.div key={s.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                        className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${riskDot[s.risk] || 'bg-slate-500'}`} />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{s.patient_id}</p>
                            <p className="text-xs text-slate-500">{s.state || s.village} · {s.risk} Risk</p>
                        </div>
                        <div className="text-right flex-shrink-0">
                            <p className={`text-xs font-semibold ${s.risk === 'High' ? 'text-red-400' : s.risk === 'Medium' ? 'text-amber-400' : 'text-emerald-400'}`}>
                                {Math.round(s.confidence * 100)}%
                            </p>
                            <p className="text-xs text-slate-600">{timeAgo(s.created_at)}</p>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}

// ── Tobacco Chart ─────────────────────────────────────────────────────────────
function TobaccoRiskChart({ data }) {
    if (!data?.length) return null;
    return (
        <div className="glass-card p-6">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2"><Cigarette className="w-4 h-4 text-amber-400" /> Tobacco Risk Correlation</h3>
            <div className="space-y-4">
                {data.map(d => (
                    <div key={d.name}>
                        <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                            <span className="font-medium text-slate-300">{d.name}</span>
                            <span><span className="text-red-400 font-semibold">{d.high_risk}</span> high-risk / {d.total} total</span>
                        </div>
                        <div className="w-full bg-white/5 rounded-full h-3 overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: `${d.pct}%` }} transition={{ duration: 0.8, delay: 0.2 }}
                                className="h-3 rounded-full bg-gradient-to-r from-red-600 to-orange-400" />
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{d.pct}% high-risk rate</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [screenings, setScreenings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [notesModal, setNotesModal] = useState(null);
    const [imageModal, setImageModal] = useState(null);
    const [explanationModal, setExplanationModal] = useState(null);
    const [search, setSearch] = useState('');
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const autoRefreshRef = useRef(null);

    const fetchData = useCallback(async (silent = false) => {
        if (!silent) setLoading(true);
        else setRefreshing(true);
        try {
            const [statsRes, screenRes] = await Promise.all([
                client.get('/dashboard/stats'),
                client.get('/screenings?risk=High&limit=50'),
            ]);
            setStats(statsRes.data);
            setScreenings(screenRes.data);
        } catch {
            toast.error('Failed to load dashboard data');
        } finally {
            setLoading(false); setRefreshing(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        autoRefreshRef.current = setInterval(() => fetchData(true), 30000);
        return () => clearInterval(autoRefreshRef.current);
    }, [fetchData]);

    const handleUpdateScreening = async (id, update) => {
        try {
            await client.patch(`/screenings/${id}`, update);
            toast.success('Case updated'); fetchData(true);
        } catch { toast.error('Update failed'); }
    };

    const handleMarkReviewed = async (id) => {
        try {
            await client.patch(`/screenings/${id}`, { status: 'Reviewed' });
            toast.success('Marked as reviewed'); fetchData(true);
        } catch { toast.error('Update failed'); }
    };

    // ── Client-side filtering ───────────────────────────────────────────────────
    const filteredScreenings = screenings.filter(sc => {
        const q = search.toLowerCase();
        const matchesSearch = !q ||
            sc.patient_id?.toLowerCase().includes(q) ||
            sc.village?.toLowerCase().includes(q) ||
            sc.state?.toLowerCase().includes(q) ||
            (sc.primary_tobacco_type || '').toLowerCase().includes(q);
        const createdAt = new Date(sc.created_at);
        const matchesFrom = !dateFrom || createdAt >= new Date(dateFrom);
        const matchesTo = !dateTo || createdAt <= new Date(dateTo + 'T23:59:59');
        return matchesSearch && matchesFrom && matchesTo;
    });

    if (loading) return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center">
            <div className="text-center">
                <div className="w-16 h-16 mx-auto mb-4 relative">
                    <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
                    <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" />
                    <Activity className="w-7 h-7 text-blue-400 absolute inset-0 m-auto" />
                </div>
                <p className="text-slate-400 text-sm">Loading dashboard...</p>
            </div>
        </div>
    );

    const s = stats?.summary || {};
    const avgConfidence = s.total > 0 ? `${Math.round((s.avg_confidence || 0) * 100)}%` : '—';
    const pendingReferrals = s.pending_reviews ?? 0;

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            {/* Modals */}
            <AnimatePresence>
                {notesModal && <NotesModal screening={notesModal} onClose={() => setNotesModal(null)} onSave={handleUpdateScreening} />}
                {imageModal && <ImageModal url={imageModal} onClose={() => setImageModal(null)} />}
                {explanationModal && <AIExplanationModal screening={explanationModal} onClose={() => setExplanationModal(null)} />}
            </AnimatePresence>

            {/* Navbar */}
            <nav className="border-b border-white/5 backdrop-blur-md bg-slate-950/90 sticky top-0 z-40">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-teal-400 rounded-lg flex items-center justify-center shadow-lg">
                            <Activity className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-bold">OralVision</span>
                        <span className="hidden sm:flex items-center gap-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs px-2.5 py-1 rounded-full">
                            <Shield className="w-3 h-3" /> Admin
                        </span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5">
                            <div className={`w-2 h-2 rounded-full ${refreshing ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
                            <span className="text-xs text-slate-500 hidden sm:block">{refreshing ? 'Refreshing...' : 'Live'}</span>
                        </div>
                        <button onClick={() => fetchData(true)} disabled={refreshing}
                            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg px-3 py-1.5">
                            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} /> Refresh
                        </button>
                        <Link to="/screening" className="text-xs btn-primary py-1.5 px-3">New Screening</Link>
                        <button onClick={() => { logout(); navigate('/login'); }} className="text-slate-500 hover:text-white transition-colors">
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">

                {/* ── Dashboard Header with Search / Date / Export ─────────────────── */}
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
                    <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
                            <p className="text-slate-500 text-sm mt-1">
                                Welcome, <span className="text-slate-300 font-medium">{user?.name}</span> · Pan-India oral cancer screening insights
                            </p>
                        </div>

                        {/* Controls */}
                        <div className="flex flex-wrap items-center gap-3">
                            {/* Search */}
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                <input
                                    type="text" placeholder="Search patient, state, village..."
                                    value={search} onChange={e => setSearch(e.target.value)}
                                    className="input-field text-sm pl-9 pr-4 py-2 w-56"
                                />
                            </div>

                            {/* Date range */}
                            <div className="flex items-center gap-2">
                                <div className="relative">
                                    <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                                    <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                                        className="input-field text-xs pl-8 pr-2 py-2 w-40" />
                                </div>
                                <span className="text-slate-600 text-xs">to</span>
                                <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
                                    className="input-field text-xs px-2 py-2 w-40" />
                            </div>

                            {/* Export */}
                            <button
                                onClick={() => exportToCSV(filteredScreenings)}
                                className="flex items-center gap-2 text-xs font-semibold bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/20 hover:border-teal-500/40 text-teal-400 rounded-xl px-4 py-2 transition-colors"
                            >
                                <Download className="w-4 h-4" /> Export CSV
                            </button>
                        </div>
                    </div>
                </motion.div>

                {/* ── 4 KPI Cards ──────────────────────────────────────────────────── */}
                <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                    <StatCard
                        label="Total Rural Screenings"
                        value={s.total ?? 0}
                        sub="All-time"
                        cardClass="stat-card"
                        icon={<Database className="w-5 h-5 text-slate-400" />}
                    />
                    <StatCard
                        label="High-Risk Cases"
                        value={s.high ?? 0}
                        sub={`${s.high_pct ?? 0}% of total`}
                        cardClass="stat-card-high"
                        icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
                    />
                    <StatCard
                        label="Avg AI Confidence"
                        value={avgConfidence}
                        sub="Gemini 1.5 Flash"
                        cardClass="stat-card-blue"
                        icon={<Brain className="w-5 h-5 text-violet-400" />}
                    />
                    <StatCard
                        label="Pending Referrals"
                        value={pendingReferrals}
                        sub="Require clinician review"
                        cardClass="stat-card"
                        icon={<Clock className="w-5 h-5 text-amber-400" />}
                    />
                </div>

                {/* ── Charts Row: Donut + Heatmap ───────────────────────────────────── */}
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Donut */}
                    <div className="glass-card p-6">
                        <h3 className="text-base font-semibold mb-5">Risk Distribution</h3>
                        <ResponsiveContainer width="100%" height={180}>
                            <PieChart>
                                <Pie data={stats?.risk_distribution || []} cx="50%" cy="50%" innerRadius={55} outerRadius={82} paddingAngle={4} dataKey="value">
                                    {(stats?.risk_distribution || []).map((entry, i) => (
                                        <Cell key={i} fill={entry.color} strokeWidth={0} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="flex flex-col gap-2 mt-2">
                            {(stats?.risk_distribution || []).map(d => (
                                <div key={d.name} className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: d.color }} />
                                        <span className="text-slate-400">{d.name}</span>
                                    </div>
                                    <span className="font-semibold">{d.value}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Heatmap — 2 col span */}
                    <div className="lg:col-span-2">
                        <HeatmapPanel data={stats?.heatmap || []} />
                    </div>
                </div>

                {/* ── 7-Day Trend + Age Group ──────────────────────────────────────── */}
                <div className="grid lg:grid-cols-3 gap-6">
                    <div className="glass-card p-6 lg:col-span-2">
                        <h3 className="text-base font-semibold mb-5 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-blue-400" /> 7-Day Screening Trends
                        </h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <LineChart data={stats?.screenings_over_time || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="date" stroke="#475569" tick={{ fontSize: 11 }} />
                                <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend wrapperStyle={{ fontSize: 11 }} />
                                <Line type="monotone" dataKey="screenings" name="Total" stroke="#3b82f6" strokeWidth={2.5} dot={{ fill: '#3b82f6', r: 4 }} activeDot={{ r: 6 }} />
                                <Line type="monotone" dataKey="high_risk" name="High Risk" stroke="#ef4444" strokeWidth={2} dot={{ fill: '#ef4444', r: 3 }} strokeDasharray="4 2" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="flex flex-col gap-6">
                        <ActivityFeed items={stats?.recent_screenings} />
                    </div>
                </div>

                <div className="grid lg:grid-cols-2 gap-6">
                    <div className="glass-card p-6">
                        <h3 className="text-base font-semibold mb-5 flex items-center gap-2">
                            <MapPin className="w-4 h-4 text-red-400" /> Village-Wise High Risk
                        </h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={stats?.village_high_risk || []} barSize={28}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="village" stroke="#475569" tick={{ fontSize: 10 }} />
                                <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="high_risk" name="High Risk Cases" radius={[6, 6, 0, 0]}>
                                    {(stats?.village_high_risk || []).map((_, i) => <Cell key={i} fill={`rgba(239, 68, 68, ${0.5 + (i / 12)})`} />)}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <TobaccoRiskChart data={stats?.tobacco_risk} />
                </div>

                {/* ── Recent High-Risk Cases Table ────────────────────────────────── */}
                <div className="glass-card overflow-hidden">
                    <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                        <div>
                            <h3 className="text-base font-semibold flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4 text-red-400" /> Recent High-Risk Cases
                                <span className="ml-1 bg-red-500/20 text-red-400 text-xs px-2 py-0.5 rounded-full">{filteredScreenings.length}</span>
                            </h3>
                            {(search || dateFrom || dateTo) && (
                                <p className="text-xs text-slate-500 mt-1">
                                    Filtered from {screenings.length} total results
                                    {' · '}
                                    <button onClick={() => { setSearch(''); setDateFrom(''); setDateTo(''); }} className="text-teal-400 hover:underline">Clear filters</button>
                                </p>
                            )}
                        </div>
                        <button onClick={() => exportToCSV(filteredScreenings)}
                            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-teal-400 transition-colors bg-white/5 hover:bg-white/10 border border-white/10 hover:border-teal-500/20 rounded-lg px-3 py-1.5">
                            <Download className="w-3.5 h-3.5" /> Export filtered
                        </button>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full min-w-[800px]">
                            <thead>
                                <tr className="border-b border-white/5 text-xs text-slate-500 uppercase tracking-wider">
                                    <th className="text-left px-6 py-3">Masked Patient ID</th>
                                    <th className="text-left px-6 py-3">State / Village</th>
                                    <th className="text-left px-6 py-3">Tobacco Habit</th>
                                    <th className="text-left px-6 py-3">Confidence</th>
                                    <th className="text-left px-6 py-3">Date</th>
                                    <th className="text-left px-6 py-3">Status</th>
                                    <th className="text-left px-6 py-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <AnimatePresence>
                                    {filteredScreenings.length === 0 ? (
                                        <tr>
                                            <td colSpan={7} className="text-center py-12 text-slate-600">
                                                <AlertTriangle className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                                                {search || dateFrom || dateTo ? 'No results match your filters.' : 'No high-risk cases found.'}
                                            </td>
                                        </tr>
                                    ) : filteredScreenings.map((sc, i) => (
                                        <motion.tr
                                            key={sc.id}
                                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                                            className="border-b border-white/5 hover:bg-white/3 transition-colors group"
                                        >
                                            {/* Masked Patient ID */}
                                            <td className="px-6 py-4">
                                                <div className="font-semibold text-sm font-mono">{sc.patient_id}</div>
                                                <div className="text-xs text-slate-500">Age {sc.age}</div>
                                            </td>

                                            {/* State / Village */}
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-1.5 text-sm">
                                                    <MapPin className="w-3 h-3 text-slate-500" />
                                                    <div>
                                                        <div>{sc.state || '—'}</div>
                                                        {sc.village && sc.village !== sc.state && <div className="text-xs text-slate-500">{sc.village}</div>}
                                                    </div>
                                                </div>
                                            </td>

                                            {/* Tobacco Habit — from DimHabits star schema */}
                                            <td className="px-6 py-4">
                                                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${(sc.primary_tobacco_type && sc.primary_tobacco_type !== 'None') || sc.tobacco_usage
                                                        ? 'bg-amber-500/20 text-amber-400'
                                                        : 'bg-white/5 text-slate-500'
                                                    }`}>
                                                    {sc.primary_tobacco_type || (sc.tobacco_usage ? 'Yes' : 'None')}
                                                </span>
                                            </td>

                                            {/* Confidence */}
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-16 bg-white/5 rounded-full h-2 overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${sc.confidence * 100}%` }}
                                                            transition={{ delay: i * 0.03 + 0.3, duration: 0.5 }}
                                                            className="bg-gradient-to-r from-red-600 to-orange-500 h-2 rounded-full"
                                                        />
                                                    </div>
                                                    <span className="text-xs text-red-400 font-semibold">{Math.round(sc.confidence * 100)}%</span>
                                                </div>
                                            </td>

                                            {/* Date */}
                                            <td className="px-6 py-4 text-xs text-slate-500">
                                                {new Date(sc.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                            </td>

                                            {/* Status */}
                                            <td className="px-6 py-4">
                                                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${sc.status === 'Reviewed' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                                                    {sc.status}
                                                </span>
                                            </td>

                                            {/* Actions */}
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    {/* View AI Explanation — primary CTA */}
                                                    <button onClick={() => setExplanationModal(sc)}
                                                        className="text-xs flex items-center gap-1 text-violet-400 hover:text-violet-300 transition-colors font-medium">
                                                        <Brain className="w-3.5 h-3.5" /> View AI Explanation
                                                    </button>
                                                    {sc.image_url && (
                                                        <button onClick={() => setImageModal(sc.image_url)}
                                                            className="text-xs flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors">
                                                            <Image className="w-3.5 h-3.5" /> Image
                                                        </button>
                                                    )}
                                                    {sc.status !== 'Reviewed' && (
                                                        <button onClick={() => handleMarkReviewed(sc.id)}
                                                            className="text-xs flex items-center gap-1 text-emerald-400 hover:text-emerald-300 transition-colors">
                                                            <CheckCircle className="w-3.5 h-3.5" />
                                                        </button>
                                                    )}
                                                    <button onClick={() => setNotesModal(sc)}
                                                        className="text-xs flex items-center gap-1 text-slate-400 hover:text-white transition-colors">
                                                        <FileText className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </AnimatePresence>
                            </tbody>
                        </table>
                    </div>
                </div>

                <p className="text-center text-slate-700 text-xs pb-4">
                    OralVision · Gemini 1.5 Flash · Pan-India Star Schema · Auto-refresh every 30s
                </p>
            </div>
        </div>
    );
}
