import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Activity, Brain, Bell, BarChart2, Shield, Cpu, Map, Menu, X,
    Camera, Zap, GitBranch, Lock, Eye, Wifi, ChevronRight, Check
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

// ── Data ─────────────────────────────────────────────────────────────────────

const howItWorks = [
    {
        step: '01',
        icon: <Camera className="w-7 h-7 text-blue-400" />,
        title: 'Capture & Context',
        desc: 'ASHA workers snap an oral cavity photo using their phone camera. Patient age, state, and tobacco habit are entered as clinical context. No specialist required.',
        color: 'from-blue-500/20 to-blue-600/5',
        border: 'border-blue-500/25',
        accent: 'text-blue-400',
    },
    {
        step: '02',
        icon: <Brain className="w-7 h-7 text-violet-400" />,
        title: 'Gemini AI Analysis',
        desc: 'Google Gemini 1.5 Flash multimodal model analyzes the image alongside clinical metadata. It returns a precise risk level, confidence score, and a clinical explanation in seconds.',
        color: 'from-violet-500/20 to-violet-600/5',
        border: 'border-violet-500/25',
        accent: 'text-violet-400',
    },
    {
        step: '03',
        icon: <GitBranch className="w-7 h-7 text-teal-400" />,
        title: 'Automated Triaging',
        desc: 'High-risk cases instantly trigger n8n workflows — SMS alerts, specialist referrals, and dashboard flags. Clinicians review flagged cases in the analytics portal.',
        color: 'from-teal-500/20 to-teal-600/5',
        border: 'border-teal-500/25',
        accent: 'text-teal-400',
    },
];

const trustBadges = [
    {
        icon: <Lock className="w-5 h-5 text-emerald-400" />,
        label: 'DPDP / HIPAA Compliant',
        desc: 'Patient IDs masked before storage. PII never reaches AI APIs.',
        bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
        icon: <Eye className="w-5 h-5 text-blue-400" />,
        label: 'Explainable AI',
        desc: 'Every prediction includes a clinical_explanation — keeping the clinician in the loop.',
        bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
        icon: <Wifi className="w-5 h-5 text-amber-400" />,
        label: 'Low-Bandwidth Optimized',
        desc: 'Mobile-first PWA design. Works reliably on 3G rural networks.',
        bg: 'bg-amber-500/10 border-amber-500/20',
    },
];

const features = [
    {
        icon: <Brain className="w-7 h-7 text-blue-400" />,
        title: 'Gemini 1.5 Flash Multimodal',
        desc: 'Google\'s state-of-the-art multimodal AI analyzes oral cavity images with clinical context for expert-grade triage.',
        color: 'from-blue-500/20 to-blue-600/5',
        border: 'border-blue-500/20',
    },
    {
        icon: <Bell className="w-7 h-7 text-red-400" />,
        title: 'Automated Specialist Alerts',
        desc: 'High-risk patients automatically trigger oncologist SMS + email via n8n. Zero manual follow-up needed.',
        color: 'from-red-500/20 to-red-600/5',
        border: 'border-red-500/20',
    },
    {
        icon: <BarChart2 className="w-7 h-7 text-teal-400" />,
        title: 'Pan-India Analytics Dashboard',
        desc: 'State, district, and village-level risk heatmaps. Recharts-powered insights for NPCDCS reporting.',
        color: 'from-teal-500/20 to-teal-600/5',
        border: 'border-teal-500/20',
    },
    {
        icon: <Map className="w-7 h-7 text-purple-400" />,
        title: 'Star Schema Data Warehouse',
        desc: 'Enterprise-grade PostgreSQL star schema with Power BI-compatible dimensions: patient, geography, habits, risk.',
        color: 'from-purple-500/20 to-purple-600/5',
        border: 'border-purple-500/20',
    },
];

const stats = [
    { value: '1.5 Flash', label: 'Gemini Model' },
    { value: '< 3s', label: 'Avg. Triage Time' },
    { value: '28+', label: 'Indian States' },
    { value: '600M+', label: 'Rural Addressable' },
];

// ── Animation variants ────────────────────────────────────────────────────────
const fadeUp = { hidden: { opacity: 0, y: 30 }, visible: (i = 0) => ({ opacity: 1, y: 0, transition: { delay: i * 0.12, duration: 0.6, ease: 'easeOut' } }) };

export default function LandingPage() {
    const [menuOpen, setMenuOpen] = useState(false);
    const { isAuthenticated, isAdmin } = useAuth();

    return (
        <div className="min-h-screen bg-slate-950 text-white overflow-x-hidden">

            {/* ── Ambient background ─────────────────────────────────────────────── */}
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                <div className="absolute -top-32 left-1/4 w-[600px] h-[600px] bg-blue-600/8 rounded-full blur-[120px] animate-pulse-slow" />
                <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-teal-500/8 rounded-full blur-[100px] animate-pulse-slow" style={{ animationDelay: '2s' }} />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-violet-600/5 rounded-full blur-[80px]" />
            </div>

            {/* ── Navbar ─────────────────────────────────────────────────────────── */}
            <nav className="relative z-50 border-b border-white/5 backdrop-blur-md bg-slate-950/80 sticky top-0">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
                    <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-teal-400 rounded-lg flex items-center justify-center shadow-lg">
                            <Activity className="w-5 h-5 text-white" />
                        </div>
                        <span className="font-bold text-lg tracking-tight">
                            Oral<span className="text-gradient">Vision</span>
                        </span>
                    </div>

                    <div className="hidden md:flex items-center gap-6 text-sm text-slate-400">
                        <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
                        <a href="#features" className="hover:text-white transition-colors">Features</a>
                        <a href="#trust" className="hover:text-white transition-colors">Security</a>
                    </div>

                    <div className="hidden md:flex items-center gap-3">
                        {isAuthenticated ? (
                            <Link to={isAdmin ? '/dashboard' : '/screening'} className="btn-primary text-sm py-2">
                                Go to {isAdmin ? 'Dashboard' : 'Screening'}
                            </Link>
                        ) : (
                            <>
                                <Link to="/login" className="btn-secondary text-sm py-2">Admin Login</Link>
                                <Link to="/login" className="btn-primary text-sm py-2 flex items-center gap-2">
                                    <Activity className="w-4 h-4" /> Start Screening
                                </Link>
                            </>
                        )}
                    </div>

                    <button className="md:hidden text-slate-400" onClick={() => setMenuOpen(!menuOpen)}>
                        {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                    </button>
                </div>
                {menuOpen && (
                    <div className="md:hidden border-t border-white/5 p-4 flex flex-col gap-3">
                        <Link to="/login" className="btn-secondary text-center text-sm">Admin Login</Link>
                        <Link to="/login" className="btn-primary text-center text-sm">Start Screening</Link>
                    </div>
                )}
            </nav>

            {/* ── Hero ──────────────────────────────────────────────────────────── */}
            <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-28 pb-24 text-center">
                <motion.div
                    variants={fadeUp}
                    initial="hidden"
                    animate="visible"
                >
                    {/* Badge */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5 }}
                        className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 text-xs text-blue-400 font-semibold mb-8"
                    >
                        <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
                        Powered by Gemini 1.5 Flash · Built for Bharat
                    </motion.div>

                    <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[1.1] mb-6 tracking-tight">
                        Empowering Rural Healthcare<br />
                        <span className="text-gradient">with Multimodal AI</span>
                    </h1>
                    <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                        Enabling ASHA workers and frontline clinicians to detect oral cancer risk at the village level —
                        no specialist required, results in under 3 seconds.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link to="/login">
                            <motion.button
                                whileHover={{ scale: 1.04 }}
                                whileTap={{ scale: 0.97 }}
                                className="btn-primary text-base px-8 py-4 flex items-center gap-2"
                            >
                                <Activity className="w-5 h-5" />
                                Start Screening
                                <ChevronRight className="w-4 h-4" />
                            </motion.button>
                        </Link>
                        <a href="#how-it-works">
                            <motion.button
                                whileHover={{ scale: 1.04 }}
                                whileTap={{ scale: 0.97 }}
                                className="btn-secondary text-base px-8 py-4 flex items-center gap-2"
                            >
                                <Eye className="w-5 h-5" />
                                See How It Works
                            </motion.button>
                        </a>
                    </div>
                </motion.div>

                {/* Hero mock UI */}
                <motion.div
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.9 }}
                    className="mt-20 relative"
                >
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-slate-950 z-10 pointer-events-none" style={{ top: '60%' }} />
                    <div className="glass-card p-8 max-w-3xl mx-auto glow-blue">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                                <div className="w-3 h-3 rounded-full bg-green-500" />
                            </div>
                            <div className="flex-1 bg-white/5 rounded-lg h-6 flex items-center px-3 text-xs text-slate-500">
                                oralvision.ai/screening
                            </div>
                            <span className="text-xs bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded-md px-2 py-0.5">Gemini AI</span>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div className="col-span-2 bg-white/5 rounded-xl p-4">
                                <p className="text-xs text-slate-500 mb-3">AI Triage Result</p>
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-12 h-12 bg-red-500/20 rounded-xl flex items-center justify-center">
                                        <span className="text-2xl">🔴</span>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-red-400">HIGH RISK</p>
                                        <p className="text-xs text-slate-400">Confidence: 91% · Gemini 1.5 Flash</p>
                                    </div>
                                </div>
                                <div className="bg-white/5 rounded-lg p-3 mt-3">
                                    <p className="text-xs text-sky-400 font-semibold mb-1">Clinical Explanation</p>
                                    <p className="text-xs text-slate-400 italic">"Erythroplastic lesion visible on lateral tongue border, 1.5cm. Heavy khaini use and age 62 strongly correlated with malignancy risk..."</p>
                                </div>
                            </div>
                            <div className="flex flex-col gap-3">
                                <div className="bg-white/5 rounded-xl p-3">
                                    <p className="text-xs text-slate-500">State</p>
                                    <p className="text-sm font-semibold">Maharashtra</p>
                                </div>
                                <div className="bg-white/5 rounded-xl p-3">
                                    <p className="text-xs text-slate-500">Tobacco</p>
                                    <p className="text-sm font-semibold">Khaini</p>
                                </div>
                                <div className="bg-red-500/20 border border-red-500/30 rounded-xl p-3 animate-pulse">
                                    <p className="text-xs text-red-400 font-semibold">⚠ Alert Sent</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </section>

            {/* ── Stats ─────────────────────────────────────────────────────────── */}
            <section className="relative z-10 border-y border-white/5 py-14 bg-white/[0.01]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {stats.map((s, i) => (
                            <motion.div
                                key={s.label}
                                variants={fadeUp}
                                initial="hidden"
                                whileInView="visible"
                                custom={i}
                                viewport={{ once: true }}
                                className="text-center"
                            >
                                <p className="text-4xl font-extrabold text-gradient mb-1">{s.value}</p>
                                <p className="text-slate-500 text-sm">{s.label}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── How It Works ──────────────────────────────────────────────────── */}
            <section id="how-it-works" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
                <motion.div
                    variants={fadeUp}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    className="text-center mb-16"
                >
                    <p className="text-xs font-semibold tracking-widest text-teal-400 uppercase mb-3">Workflow</p>
                    <h2 className="text-4xl font-bold mb-4">How OralVision Works</h2>
                    <p className="text-slate-400 max-w-xl mx-auto">
                        From village-level image capture to specialist alert — three automated steps, zero delays.
                    </p>
                </motion.div>

                <div className="relative">
                    {/* Connector line */}
                    <div className="hidden md:block absolute top-16 left-[calc(16.67%+2rem)] right-[calc(16.67%+2rem)] h-px bg-gradient-to-r from-blue-500/30 via-violet-500/30 to-teal-500/30" />

                    <div className="grid md:grid-cols-3 gap-8">
                        {howItWorks.map((step, i) => (
                            <motion.div
                                key={step.step}
                                variants={fadeUp}
                                initial="hidden"
                                whileInView="visible"
                                custom={i}
                                viewport={{ once: true }}
                                whileHover={{ y: -6 }}
                                className={`glass-card border ${step.border} p-8 bg-gradient-to-br ${step.color} relative`}
                            >
                                {/* Step number */}
                                <div className={`text-5xl font-black ${step.accent} opacity-20 absolute top-6 right-6`}>{step.step}</div>

                                <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-5">
                                    {step.icon}
                                </div>
                                <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                                <p className="text-slate-400 leading-relaxed text-sm">{step.desc}</p>

                                {i < howItWorks.length - 1 && (
                                    <div className="md:hidden mt-6 flex justify-center">
                                        <ChevronRight className="w-5 h-5 text-slate-600 rotate-90" />
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── Trust Badges ──────────────────────────────────────────────────── */}
            <section id="trust" className="relative z-10 border-y border-white/5 py-16 bg-white/[0.01]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div
                        variants={fadeUp}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        className="text-center mb-10"
                    >
                        <p className="text-xs font-semibold tracking-widest text-blue-400 uppercase mb-3">Compliance & Trust</p>
                        <h2 className="text-3xl font-bold">Built for Government Deployment</h2>
                    </motion.div>
                    <div className="grid md:grid-cols-3 gap-6">
                        {trustBadges.map((badge, i) => (
                            <motion.div
                                key={badge.label}
                                variants={fadeUp}
                                initial="hidden"
                                whileInView="visible"
                                custom={i}
                                viewport={{ once: true }}
                                whileHover={{ y: -4 }}
                                className={`border ${badge.bg} rounded-2xl p-6 flex gap-4 items-start`}
                            >
                                <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center flex-shrink-0">
                                    {badge.icon}
                                </div>
                                <div>
                                    <p className="font-semibold mb-1">{badge.label}</p>
                                    <p className="text-sm text-slate-400 leading-relaxed">{badge.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>

                    {/* Checklist */}
                    <motion.div
                        variants={fadeUp}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3"
                    >
                        {['NHM Compatible', 'NPCDCS Reporting Ready', 'Ayushman Bharat Aligned', 'ASHA Worker Optimized'].map(item => (
                            <div key={item} className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-3">
                                <Check className="w-4 h-4 text-teal-400 flex-shrink-0" />
                                <span className="text-xs text-slate-300">{item}</span>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* ── Features ──────────────────────────────────────────────────────── */}
            <section id="features" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
                <motion.div
                    variants={fadeUp}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    className="text-center mb-14"
                >
                    <p className="text-xs font-semibold tracking-widest text-violet-400 uppercase mb-3">Platform</p>
                    <h2 className="text-4xl font-bold mb-4">Built for the Last Mile</h2>
                    <p className="text-slate-400 max-w-xl mx-auto">
                        Every feature is designed for ASHA workers, ANMs, and rural clinics — no specialist visit required.
                    </p>
                </motion.div>
                <div className="grid md:grid-cols-2 gap-6">
                    {features.map((f, i) => (
                        <motion.div
                            key={f.title}
                            variants={fadeUp}
                            initial="hidden"
                            whileInView="visible"
                            custom={i}
                            viewport={{ once: true }}
                            whileHover={{ y: -4 }}
                            className={`glass-card border ${f.border} p-8 bg-gradient-to-br ${f.color}`}
                        >
                            <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-5">
                                {f.icon}
                            </div>
                            <h3 className="text-xl font-bold mb-3">{f.title}</h3>
                            <p className="text-slate-400 leading-relaxed">{f.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* ── CTA Banner ────────────────────────────────────────────────────── */}
            <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
                <motion.div
                    variants={fadeUp}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    className="glass-card border-blue-500/20 p-12 text-center bg-gradient-to-br from-blue-600/10 to-teal-500/5 relative overflow-hidden"
                >
                    <div className="absolute inset-0 pointer-events-none">
                        <div className="absolute -top-20 -right-20 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />
                    </div>
                    <Cpu className="w-12 h-12 text-blue-400 mx-auto mb-6" />
                    <h2 className="text-3xl font-bold mb-4">Ready for Government Pilot Deployment</h2>
                    <p className="text-slate-400 max-w-lg mx-auto mb-8">
                        Designed for NHM integration. ASHA-worker ready. Runs on a ₹10/screening model.
                        No specialist required at point of care.
                    </p>
                    <Link to="/login">
                        <motion.button
                            whileHover={{ scale: 1.04 }}
                            whileTap={{ scale: 0.97 }}
                            className="btn-primary px-10 py-4 text-base"
                        >
                            Request Pilot Access
                        </motion.button>
                    </Link>
                </motion.div>
            </section>

            {/* ── Footer ────────────────────────────────────────────────────────── */}
            <footer id="footer" className="relative z-10 border-t border-white/5 py-8">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-teal-400 rounded-md flex items-center justify-center">
                            <Activity className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-semibold text-sm">OralVision</span>
                    </div>
                    <p className="text-slate-600 text-xs">
                        AI · Gemini 1.5 Flash · Star Schema · n8n Automation · Rural India
                    </p>
                </div>
            </footer>
        </div>
    );
}
