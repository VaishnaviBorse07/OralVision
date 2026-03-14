import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Camera, Upload, User, Activity, LogOut, ChevronRight, Loader,
    AlertTriangle, CheckCircle, AlertCircle, X, FlipHorizontal, Aperture,
    Printer, RefreshCw, MapPin, Cigarette, Clock, Zap, Eye, Brain,
    Calendar, Phone, Hospital, Cpu
} from 'lucide-react';
import toast from 'react-hot-toast';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

// ── Reference data — aligned with DimGeography & DimHabits star schema ────────

const INDIA_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa',
    'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala',
    'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland',
    'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
    'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Jammu & Kashmir',
];

const TOBACCO_TYPES = [
    { value: 'None', label: 'None — Non-tobacco user' },
    { value: 'Gutka', label: 'Gutka (smokeless)' },
    { value: 'Khaini', label: 'Khaini (smokeless)' },
    { value: 'Mawa', label: 'Mawa (smokeless)' },
    { value: 'Pan Masala', label: 'Pan Masala' },
    { value: 'Bidi', label: 'Bidi (smoked)' },
    { value: 'Cigarette', label: 'Cigarette (smoked)' },
    { value: 'Other', label: 'Other' },
];

const GENDERS = [
    { value: 'Not Disclosed', label: 'Prefer not to say' },
    { value: 'Male', label: 'Male' },
    { value: 'Female', label: 'Female' },
    { value: 'Other', label: 'Other' },
];

// ── SVG Ring Gauge ─────────────────────────────────────────────────────────────
function RingGauge({ value, color, size = 120 }) {
    const r = (size - 16) / 2;
    const circ = 2 * Math.PI * r;
    const strokeDash = (value / 100) * circ;
    return (
        <div className="relative" style={{ width: size, height: size }}>
            <svg width={size} height={size} className="-rotate-90">
                <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.05)" strokeWidth="8" fill="none" />
                <motion.circle
                    cx={size / 2} cy={size / 2} r={r}
                    stroke={color} strokeWidth="8" fill="none" strokeLinecap="round"
                    strokeDasharray={`${circ}`}
                    initial={{ strokeDashoffset: circ }}
                    animate={{ strokeDashoffset: circ - strokeDash }}
                    transition={{ duration: 1.2, delay: 0.3, ease: 'easeOut' }}
                    style={{ filter: `drop-shadow(0 0 6px ${color})` }}
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <motion.span
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
                    className="text-2xl font-black" style={{ color }}
                >{value}%</motion.span>
                <span className="text-xs text-slate-500">confidence</span>
            </div>
        </div>
    );
}

// ── Camera Modal ───────────────────────────────────────────────────────────────
function CameraModal({ onCapture, onClose }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const [ready, setReady] = useState(false);
    const [facingMode, setFacingMode] = useState('environment');
    const [error, setCameraError] = useState(null);
    const [countdown, setCountdown] = useState(null);
    const [flash, setFlash] = useState(false);
    const [captured, setCaptured] = useState(null);

    const startCamera = useCallback(async (mode) => {
        if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: { ideal: mode }, width: { ideal: 1280 }, height: { ideal: 720 } },
            });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.onloadedmetadata = () => { videoRef.current.play(); setReady(true); };
            }
            setCameraError(null);
        } catch {
            setCameraError('Camera access denied. Please allow camera permissions or use file upload.');
            setReady(false);
        }
    }, []);

    useEffect(() => {
        startCamera(facingMode);
        return () => { if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop()); };
    }, [facingMode, startCamera]);

    const doSnap = () => {
        if (!videoRef.current || !canvasRef.current) return;
        const video = videoRef.current;
        const canvas = canvasRef.current;
        canvas.width = video.videoWidth; canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        canvas.toBlob(blob => {
            if (blob) {
                setCaptured({ file: new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' }), url: URL.createObjectURL(blob) });
                setFlash(true); setTimeout(() => setFlash(false), 400);
                if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
            }
        }, 'image/jpeg', 0.92);
    };

    const startCountdown = () => {
        if (!ready || countdown !== null) return;
        let count = 3; setCountdown(count);
        const interval = setInterval(() => {
            count--;
            if (count <= 0) { clearInterval(interval); setCountdown(null); doSnap(); }
            else setCountdown(count);
        }, 1000);
    };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
                    className="relative bg-slate-900 rounded-2xl overflow-hidden w-full max-w-lg shadow-2xl border border-white/10"
                    onClick={e => e.stopPropagation()}
                >
                    <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
                        <div className="flex items-center gap-2">
                            <Camera className="w-5 h-5 text-teal-400" />
                            <span className="font-semibold text-sm">Oral Cavity Scanner</span>
                            {ready && !captured && <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse ml-1" />}
                        </div>
                        <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
                    </div>

                    <div className="relative bg-black" style={{ aspectRatio: '4/3' }}>
                        {error ? (
                            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6 text-center">
                                <AlertCircle className="w-8 h-8 text-amber-400" />
                                <p className="text-sm text-slate-300">{error}</p>
                                <button onClick={onClose} className="btn-primary px-5 py-2 text-sm">Use File Upload</button>
                            </div>
                        ) : captured ? (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <img src={captured.url} alt="Captured" className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                                <div className="absolute bottom-4 left-0 right-0 flex items-center justify-center gap-4">
                                    <button onClick={() => { URL.revokeObjectURL(captured.url); setCaptured(null); setReady(false); startCamera(facingMode); }}
                                        className="flex items-center gap-2 bg-white/20 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-2.5 text-sm font-medium hover:bg-white/30 transition-colors">
                                        <RefreshCw className="w-4 h-4" /> Retake
                                    </button>
                                    <button onClick={() => { onCapture(captured.file); URL.revokeObjectURL(captured.url); }}
                                        className="flex items-center gap-2 btn-primary px-5 py-2.5 text-sm">
                                        <CheckCircle className="w-4 h-4" /> Use Photo
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <video ref={videoRef} autoPlay playsInline muted className={`w-full h-full object-cover ${facingMode === 'user' ? 'scale-x-[-1]' : ''}`} />
                                {ready && <div className="camera-scanner" />}
                                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                    <div className="w-52 h-52 rounded-full border-2 border-teal-400/50" style={{ boxShadow: '0 0 0 2000px rgba(0,0,0,0.25)' }}>
                                        <div className="w-full h-full rounded-full border border-teal-400/20" />
                                    </div>
                                </div>
                                <AnimatePresence>
                                    {countdown !== null && (
                                        <motion.div key={countdown} initial={{ scale: 1.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.5, opacity: 0 }}
                                            className="absolute inset-0 flex items-center justify-center">
                                            <div className="w-24 h-24 rounded-full bg-black/60 border-4 border-teal-400 flex items-center justify-center">
                                                <span className="text-5xl font-black text-white">{countdown}</span>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                                {flash && <div className="flash-overlay" />}
                                <p className="absolute bottom-3 left-0 right-0 text-center text-xs text-white/50 pointer-events-none">
                                    Position oral cavity inside the circle
                                </p>
                                {!ready && <div className="absolute inset-0 flex items-center justify-center bg-black/60"><Loader className="w-8 h-8 animate-spin text-teal-400" /></div>}
                            </>
                        )}
                        <canvas ref={canvasRef} className="hidden" />
                    </div>

                    {!error && !captured && (
                        <div className="flex items-center justify-between px-6 py-5 bg-slate-900">
                            <button onClick={() => { setReady(false); setFacingMode(p => p === 'environment' ? 'user' : 'environment'); }}
                                className="w-11 h-11 rounded-full bg-white/10 flex items-center justify-center hover:bg-white/20 transition-colors">
                                <FlipHorizontal className="w-5 h-5 text-slate-300" />
                            </button>
                            <button onClick={startCountdown} disabled={!ready || countdown !== null}
                                className="relative flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed transition-transform hover:scale-105 active:scale-95"
                                style={{ width: 70, height: 70 }}>
                                <div className="absolute inset-0 rounded-full border-4 border-teal-400" />
                                <div className="w-14 h-14 rounded-full bg-white flex items-center justify-center shadow-lg">
                                    <Aperture className="w-7 h-7 text-slate-900" />
                                </div>
                            </button>
                            <div className="flex flex-col items-end gap-1">
                                <span className="text-xs text-slate-500">3s timer</span>
                                {ready && <span className="text-xs text-teal-400 flex items-center gap-1"><Zap className="w-3 h-3" />Ready</span>}
                            </div>
                        </div>
                    )}
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}

// ── Risk Result Panel ──────────────────────────────────────────────────────────
function RiskResult({ result, onReset, capturedImage }) {
    const riskConfig = {
        High: { color: '#ef4444', bgClass: 'bg-red-500/10 border-red-500/30', textClass: 'text-red-400', icon: <AlertTriangle className="w-8 h-8 text-red-400" />, label: 'HIGH RISK', glowClass: 'glow-red' },
        Medium: { color: '#f59e0b', bgClass: 'bg-amber-500/10 border-amber-500/30', textClass: 'text-amber-400', icon: <AlertCircle className="w-8 h-8 text-amber-400" />, label: 'MEDIUM RISK', glowClass: 'glow-amber' },
        Low: { color: '#10b981', bgClass: 'bg-emerald-500/10 border-emerald-500/30', textClass: 'text-emerald-400', icon: <CheckCircle className="w-8 h-8 text-emerald-400" />, label: 'LOW RISK', glowClass: 'glow-teal' },
    };
    const urgencyColors = { URGENT: 'bg-red-600 text-white', FOLLOW_UP: 'bg-amber-500 text-black', ROUTINE: 'bg-emerald-600 text-white' };
    const cfg = riskConfig[result.risk] || riskConfig.Medium;
    const confidencePct = Math.round(result.confidence * 100);
    const urgencyKey = result.urgency?.toUpperCase();

    const engineLabels = {
        local_densenet:  '🧠 DenseNet121 CNN (Local)',
        gemini_enhanced: '🔮 DenseNet121 + Gemini 1.5 Flash',
        gemini:          '🔮 Gemini 1.5 Flash Multimodal',
        heuristic:       '📊 Clinical Risk Heuristic',
    };
    const engineLabel = engineLabels[result.engine] || '📊 Clinical Heuristic';

    return (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
            <div className={`glass-card border ${cfg.bgClass} p-6`}>
                {/* Risk header */}
                <div className="flex items-center justify-between mb-5">
                    <div className="flex items-center gap-3">
                        <div className={`w-12 h-12 rounded-xl ${cfg.bgClass} flex items-center justify-center border`}>
                            {cfg.icon}
                        </div>
                        <div>
                            <h2 className={`text-2xl font-black ${cfg.textClass}`}>{cfg.label}</h2>
                            <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                                <Cpu className="w-3 h-3 text-violet-400" />
                                {engineLabel}
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                        {urgencyKey && urgencyColors[urgencyKey] && (
                            <span className={`text-xs font-bold px-3 py-1.5 rounded-full ${urgencyColors[urgencyKey]}`}>
                                {result.urgency}
                            </span>
                        )}
                        <button onClick={() => window.print()} className="no-print flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg px-3 py-1.5">
                            <Printer className="w-3.5 h-3.5" /> Print
                        </button>
                    </div>
                </div>

                {/* Ring gauge + clinical explanation */}
                <div className="flex items-start gap-4 mb-5">
                    <div className="flex-shrink-0">
                        <RingGauge value={confidencePct} color={cfg.color} size={110} />
                    </div>
                    <div className="flex-1">
                        {result.clinical_explanation && (
                            <div className={`rounded-xl p-3.5 border ${cfg.bgClass}`}>
                                <div className="flex items-center gap-2 mb-2">
                                    <Activity className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                                    <p className="text-xs font-bold text-sky-400 uppercase tracking-widest">AI Clinical Explanation</p>
                                </div>
                                <p className="text-sm text-slate-200 leading-relaxed italic">
                                    &ldquo;{result.clinical_explanation}&rdquo;
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Captured image */}
                {capturedImage && (
                    <div className="mb-4">
                        <p className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5"><Eye className="w-3.5 h-3.5" />Analyzed Image</p>
                        <img src={capturedImage} alt="Analyzed oral scan" className={`w-full h-40 object-cover rounded-xl border ${cfg.bgClass}`} />
                    </div>
                )}

                {/* Recommendation */}
                {result.recommendation && (
                    <div className={`rounded-xl p-4 mb-4 border ${cfg.bgClass} text-sm`}>
                        <p className="text-xs font-semibold text-slate-400 mb-1.5 flex items-center gap-1.5">
                            <CheckCircle className="w-3.5 h-3.5 text-slate-400" /> Clinical Recommendation
                        </p>
                        <p className="text-slate-200 leading-relaxed">{result.recommendation}</p>
                    </div>
                )}

                {/* Alerts */}
                {result.alerts?.length > 0 && (
                    <div className="mb-4 space-y-2">
                        <p className="text-xs font-semibold text-slate-400 mb-2">⚠️ Clinical Alerts</p>
                        {result.alerts.map((alert, i) => (
                            <div key={i} className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-xs text-red-300 flex items-start gap-2">
                                <AlertTriangle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />{alert}
                            </div>
                        ))}
                    </div>
                )}

                {/* Hygiene tips */}
                {result.hygiene_tips?.length > 0 && (
                    <div className="mb-4">
                        <p className="text-xs font-semibold text-slate-400 mb-2">Patient Advice</p>
                        <ul className="space-y-1.5">
                            {result.hygiene_tips.map((tip, i) => (
                                <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                                    <span className="text-teal-400 mt-0.5">•</span>{tip}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Follow-up & Center cards */}
                {(result.next_followup_date || result.nearest_center) && (
                    <div className="grid grid-cols-1 gap-3 mb-4">
                        {result.next_followup_date && (
                            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-3 flex items-start gap-3">
                                <Calendar className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="text-xs font-semibold text-blue-400 mb-0.5">Next Follow-Up Date</p>
                                    <p className="text-sm text-white font-mono">{result.next_followup_date}</p>
                                    <p className="text-xs text-slate-500 mt-0.5">{result.urgency === 'URGENT' ? 'Within 48 hours — do not delay' : result.urgency === 'FOLLOW_UP' ? 'Schedule within 2 weeks' : 'Annual routine screening'}</p>
                                </div>
                            </div>
                        )}
                        {result.nearest_center && (
                            <div className="bg-teal-500/10 border border-teal-500/20 rounded-xl p-3 flex items-start gap-3">
                                <MapPin className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="text-xs font-semibold text-teal-400 mb-0.5">Nearest Cancer Centre</p>
                                    <p className="text-sm text-white">{result.nearest_center}</p>
                                </div>
                            </div>
                        )}
                        {result.cessation_helpline && result.urgency !== 'ROUTINE' && (
                            <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-3 flex items-start gap-3">
                                <Phone className="w-4 h-4 text-orange-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="text-xs font-semibold text-orange-400 mb-0.5">Tobacco Cessation Helpline</p>
                                    <p className="text-sm text-white">{result.cessation_helpline}</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Patient meta grid */}
                <div className="grid grid-cols-2 gap-3 mb-5">
                    <div className="bg-white/5 rounded-xl p-3">
                        <p className="text-xs text-slate-500 mb-0.5 flex items-center gap-1"><User className="w-3 h-3" />Patient ID</p>
                        <p className="text-sm font-semibold">{result.patient_id}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                        <p className="text-xs text-slate-500 mb-0.5">Screening ID</p>
                        <p className="text-sm font-semibold">#{result.screening_id}</p>
                    </div>
                    {result.referral_required && (
                        <div className="col-span-2 bg-red-500/15 border border-red-500/40 rounded-xl p-3 text-center">
                            <p className="text-sm text-red-400 font-bold">🚨 SPECIALIST REFERRAL REQUIRED</p>
                        </div>
                    )}
                </div>

                <button onClick={onReset} className="btn-primary w-full py-3 flex items-center justify-center gap-2 no-print">
                    <RefreshCw className="w-4 h-4" /> Screen Another Patient
                </button>
            </div>
        </motion.div>
    );
}

// ── Main Screening Page ────────────────────────────────────────────────────────
export default function ScreeningPage() {
    const [form, setForm] = useState({
        patient_id: '',
        age: '',
        gender: 'Not Disclosed',
        state: '',
        district: '',
        tobacco_type: 'None',
    });
    const [image, setImage] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [showCamera, setShowCamera] = useState(false);
    const fileRef = useRef();      // native camera (capture="environment")
    const galleryRef = useRef();   // gallery / file picker (no capture)
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        return () => { if (preview) URL.revokeObjectURL(preview); };
    }, [preview]);

    const applyFile = (f) => {
        if (!f) return;
        if (preview) URL.revokeObjectURL(preview);
        setImage(f);
        setPreview(URL.createObjectURL(f));
    };

    const handleCameraCapture = (file) => { applyFile(file); setShowCamera(false); toast.success('📸 Photo captured!'); };
    const handleDrop = (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f?.type.startsWith('image/')) applyFile(f); };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.patient_id || !form.age || !form.state) {
            toast.error('Please fill in Patient ID, Age, and State.');
            return;
        }
        setLoading(true);
        try {
            const fd = new FormData();
            fd.append('patient_id', form.patient_id);
            fd.append('age', form.age);
            fd.append('gender', form.gender);
            fd.append('state', form.state);
            fd.append('district', form.district);
            fd.append('tobacco_type', form.tobacco_type);
            // Backward-compat: also send tobacco_usage bool for old backend
            fd.append('tobacco_usage', form.tobacco_type !== 'None' ? 'true' : 'false');
            fd.append('village', form.district || form.state);
            if (image) fd.append('image', image);

            const { data } = await client.post('/predict', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            setResult(data);

            if (data.risk === 'High') toast.error('🚨 HIGH RISK! Specialist alert triggered.', { duration: 6000 });
            else if (data.risk === 'Medium') toast('⚠️ Medium risk. Follow-up recommended.', { duration: 4000 });
            else toast.success('✅ Low risk. Patient clear.', { duration: 3000 });
        } catch (err) {
            toast.error(err.response?.data?.detail || err.message || 'Prediction failed.');
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        if (preview) URL.revokeObjectURL(preview);
        setResult(null);
        setForm({ patient_id: '', age: '', gender: 'Not Disclosed', state: '', district: '', tobacco_type: 'None' });
        setImage(null); setPreview(null);
        if (fileRef.current) fileRef.current.value = '';
        if (galleryRef.current) galleryRef.current.value = '';
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            {showCamera && <CameraModal onCapture={handleCameraCapture} onClose={() => setShowCamera(false)} />}

            {/* Navbar */}
            <nav className="border-b border-white/5 backdrop-blur-md bg-slate-950/80 sticky top-0 z-40 no-print">
                <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2">
                        <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-teal-400 rounded-lg flex items-center justify-center">
                            <Activity className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-sm">OralVision</span>
                    </Link>
                    <div className="flex items-center gap-3">
                        <Link to="/dashboard" className="text-xs text-slate-500 hover:text-slate-300 transition-colors hidden sm:block">Dashboard</Link>
                        <span className="text-xs text-slate-500 hidden sm:block">{user?.name}</span>
                        <button onClick={() => { logout(); navigate('/login'); }} className="text-slate-500 hover:text-white transition-colors">
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </nav>

            <div className="max-w-2xl mx-auto px-4 py-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                    {!result ? (
                        <>
                            {/* Page header */}
                            <div className="mb-7">
                                <div className="flex items-center gap-3 mb-2">
                                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500/20 to-teal-500/20 border border-blue-500/20 rounded-xl flex items-center justify-center">
                                        <Activity className="w-5 h-5 text-blue-400" />
                                    </div>
                                    <div>
                                        <h1 className="text-2xl font-bold">New Patient Screening</h1>
                                        <p className="text-slate-500 text-sm flex items-center gap-1.5">
                                            <Brain className="w-3.5 h-3.5 text-violet-400" />
                                            Gemini 1.5 Flash Multimodal · Oral Cancer AI Triage
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <form onSubmit={handleSubmit} className="space-y-4">

                                {/* ── Patient Identity ── */}
                                <div className="glass-card p-5">
                                    <label className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-4">
                                        <User className="w-4 h-4 text-blue-400" /> Patient Identity
                                    </label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs text-slate-500 mb-1.5">Patient ID *</label>
                                            <input
                                                className="input-field text-sm"
                                                placeholder="e.g. OV-2024-001"
                                                value={form.patient_id}
                                                onChange={e => setForm({ ...form, patient_id: e.target.value })}
                                                required
                                            />
                                            <p className="text-xs text-slate-600 mt-1">Masked before AI analysis (DPDP)</p>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-slate-500 mb-1.5">Age *</label>
                                            <input
                                                type="number" className="input-field text-sm" placeholder="e.g. 45"
                                                min="1" max="120" value={form.age}
                                                onChange={e => setForm({ ...form, age: e.target.value })}
                                                required
                                            />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-xs text-slate-500 mb-1.5">Gender</label>
                                            <select className="input-field text-sm" value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}>
                                                {GENDERS.map(g => <option key={g.value} value={g.value}>{g.label}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                {/* ── Geography & Habits ── */}
                                <div className="glass-card p-5">
                                    <label className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-4">
                                        <MapPin className="w-4 h-4 text-teal-400" /> Geography & Risk Factors
                                    </label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-xs text-slate-500 mb-1.5">State *</label>
                                            <select className="input-field text-sm" value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} required>
                                                <option value="">Select state</option>
                                                {INDIA_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-slate-500 mb-1.5">District / Village</label>
                                            <input
                                                className="input-field text-sm" placeholder="e.g. Nanded"
                                                value={form.district}
                                                onChange={e => setForm({ ...form, district: e.target.value })}
                                            />
                                        </div>
                                        <div className="col-span-2">
                                            <label className="block text-xs text-slate-500 mb-1.5 flex items-center gap-1"><Cigarette className="w-3 h-3" /> Primary Tobacco Habit</label>
                                            <select className="input-field text-sm" value={form.tobacco_type} onChange={e => setForm({ ...form, tobacco_type: e.target.value })}>
                                                {TOBACCO_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                            </select>
                                            {form.tobacco_type !== 'None' && (
                                                <div className="mt-2 flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                                                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                                                    Tobacco use elevates oral cancer risk 6–10×. AI model will factor this into its assessment.
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* ── Image Capture ── */}
                                <div className="glass-card p-5">
                                    <label className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-4">
                                        <Camera className="w-4 h-4 text-teal-400" /> Oral Cavity Image
                                        <span className="ml-1 text-xs text-slate-600">(optional — strongly recommended)</span>
                                    </label>

                                    {/* Hidden native camera input — mobile-first */}
                                    <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={e => applyFile(e.target.files[0])} />
                                    {/* Hidden gallery-only input — no capture attribute */}
                                    <input ref={galleryRef} type="file" accept="image/*" className="hidden" onChange={e => applyFile(e.target.files[0])} />

                                    {preview ? (
                                        <div className="relative" onDrop={handleDrop} onDragOver={e => e.preventDefault()}>
                                            <img src={preview} alt="Preview" className="w-full h-52 object-cover rounded-xl border border-white/10" />
                                            <div className="absolute inset-0 rounded-xl bg-gradient-to-t from-black/50 to-transparent" />
                                            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
                                                <span className="text-xs text-white/70 bg-black/50 backdrop-blur-sm rounded-lg px-2 py-1">✅ Image ready for Gemini analysis</span>
                                                <button type="button" onClick={() => { if (preview) URL.revokeObjectURL(preview); setImage(null); setPreview(null); if (fileRef.current) fileRef.current.value = ''; }}
                                                    className="bg-red-500/80 backdrop-blur-sm text-white rounded-lg px-3 py-1 text-xs flex items-center gap-1 hover:bg-red-500 transition-colors">
                                                    <X className="w-3 h-3" /> Remove
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="border-2 border-dashed border-white/10 rounded-xl p-2 hover:border-white/20 transition-colors" onDrop={handleDrop} onDragOver={e => e.preventDefault()}>
                                            <div className="grid grid-cols-2 gap-3">
                                                {/* Primary: Open Live Camera — opens webcam modal */}
                                                <motion.button
                                                    type="button" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                                                    onClick={() => setShowCamera(true)}
                                                    className="h-36 border-2 border-dashed border-teal-500/40 rounded-xl flex flex-col items-center justify-center gap-2 hover:border-teal-400/80 hover:bg-teal-500/5 transition-all duration-300 group"
                                                >
                                                    <div className="w-12 h-12 bg-teal-500/10 rounded-xl flex items-center justify-center group-hover:bg-teal-500/20 transition-colors">
                                                        <Camera className="w-6 h-6 text-teal-400" />
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm font-semibold text-teal-400">Open Camera</p>
                                                        <p className="text-xs text-slate-600 mt-0.5">Live webcam capture</p>
                                                    </div>
                                                </motion.button>

                                                {/* Secondary: Upload from gallery / file system */}
                                                <motion.button
                                                    type="button" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                                                    onClick={() => galleryRef.current?.click()}
                                                    className="h-36 border-2 border-dashed border-white/10 rounded-xl flex flex-col items-center justify-center gap-2 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all duration-300 group"
                                                >
                                                    <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center group-hover:bg-blue-500/10 transition-colors">
                                                        <Upload className="w-6 h-6 text-slate-400 group-hover:text-blue-400 transition-colors" />
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-sm font-semibold text-slate-400 group-hover:text-blue-400 transition-colors">Upload / Gallery</p>
                                                        <p className="text-xs text-slate-600 mt-0.5">JPG, PNG · drag &amp; drop</p>
                                                    </div>
                                                </motion.button>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Submit */}
                                <motion.button
                                    whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
                                    type="submit" disabled={loading}
                                    className="btn-primary w-full py-5 text-base flex items-center justify-center gap-3 shadow-xl"
                                    style={{ boxShadow: loading ? undefined : '0 4px 30px rgba(59,130,246,0.3)' }}
                                >
                                    {loading ? (
                                        <><Loader className="w-5 h-5 animate-spin" /> Analyzing with Gemini 1.5 Flash...</>
                                    ) : (
                                        <><Brain className="w-5 h-5" /> Run AI Screening <ChevronRight className="w-5 h-5" /></>
                                    )}
                                </motion.button>

                                {!image && (
                                    <p className="text-center text-xs text-slate-600">
                                        Without an image, Gemini will use clinical heuristics (age + tobacco type) for risk estimation.
                                    </p>
                                )}
                            </form>
                        </>
                    ) : (
                        <>
                            <div className="mb-6 no-print">
                                <h1 className="text-2xl font-bold mb-1">Screening Result</h1>
                                <p className="text-slate-500 text-sm flex items-center gap-1.5">
                                    <Brain className="w-3.5 h-3.5 text-violet-400" />
                                    Gemini 1.5 Flash AI analysis complete · {new Date().toLocaleString('en-IN')}
                                </p>
                            </div>
                            <RiskResult result={result} onReset={handleReset} capturedImage={preview} />
                        </>
                    )}
                </motion.div>
            </div>
        </div>
    );
}