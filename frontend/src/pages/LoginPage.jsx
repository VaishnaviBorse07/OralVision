import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, Mail, Lock, Eye, EyeOff, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const [email, setEmail] = useState('admin@oralvision.ai');
    const [password, setPassword] = useState('admin123');
    const [showPass, setShowPass] = useState(false);
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const { data } = await client.post('/auth/login', { email, password });
            login(data.access_token, { email, name: data.name, role: data.role });
            toast.success(`Welcome back, ${data.name}!`);
            navigate(data.role === 'admin' ? '/dashboard' : '/screening');
        } catch (err) {
            console.error(err);
            const msg = typeof err.response?.data?.detail === 'string'
                ? err.response.data.detail
                : err.message || 'Network Error or Invalid credentials';
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/3 right-1/4 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md relative z-10"
            >
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link to="/" className="inline-flex items-center gap-2.5 mb-6">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-teal-400 rounded-xl flex items-center justify-center">
                            <Activity className="w-6 h-6 text-white" />
                        </div>
                        <span className="font-bold text-xl">Oral<span className="text-gradient">Vision</span></span>
                    </Link>
                    <h1 className="text-2xl font-bold">Welcome back</h1>
                    <p className="text-slate-400 text-sm mt-1">Sign in to your OralVision account</p>
                </div>

                {/* Form */}
                <div className="glass-card p-8">
                    <form onSubmit={handleLogin} className="space-y-5">
                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
                                <input
                                    type="email"
                                    className="input-field pl-10"
                                    placeholder="admin@oralvision.ai"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
                                <input
                                    type={showPass ? 'text' : 'password'}
                                    className="input-field pl-10 pr-10"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPass(!showPass)}
                                    className="absolute right-3 top-3.5 text-slate-500 hover:text-slate-300"
                                >
                                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        <motion.button
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.98 }}
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full flex items-center justify-center gap-2 py-3.5"
                        >
                            {loading ? (
                                <><Loader className="w-4 h-4 animate-spin" /> Signing in...</>
                            ) : 'Sign In'}
                        </motion.button>
                    </form>

                    {/* Demo credentials hint */}
                    <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                        <p className="text-xs text-blue-400 font-semibold mb-2">Demo Credentials</p>
                        <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                            <div>
                                <p className="text-slate-500">Admin</p>
                                <p>admin@oralvision.ai</p>
                                <p>admin123</p>
                            </div>
                            <div>
                                <p className="text-slate-500">Clinic Worker</p>
                                <p>worker@oralvision.ai</p>
                                <p>worker123</p>
                            </div>
                        </div>
                    </div>
                </div>

                <p className="text-center text-slate-600 text-xs mt-6">
                    <Link to="/" className="text-slate-400 hover:text-white transition-colors">← Back to home</Link>
                </p>
            </motion.div>
        </div>
    );
}
