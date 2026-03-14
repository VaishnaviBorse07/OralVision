import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        try {
            const s = localStorage.getItem('ov_user');
            return s ? JSON.parse(s) : null;
        } catch { return null; }
    });

    const login = (token, userData) => {
        localStorage.setItem('ov_token', token);
        localStorage.setItem('ov_user', JSON.stringify(userData));
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem('ov_token');
        localStorage.removeItem('ov_user');
        setUser(null);
    };

    const isAdmin = user?.role === 'admin';
    const isAuthenticated = !!user;

    return (
        <AuthContext.Provider value={{ user, login, logout, isAdmin, isAuthenticated }}>
            {children}
        </AuthContext.Provider>
    );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
};
