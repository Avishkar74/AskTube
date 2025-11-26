import React from 'react';

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'success' | 'warning' | 'error' | 'info' | 'default' | 'running';
}

const Badge: React.FC<BadgeProps> = ({ children, variant = 'default' }) => {
    const variants = {
        success: "bg-success/10 text-success border-success/20",
        warning: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
        error: "bg-error/10 text-error border-error/20",
        info: "bg-info/10 text-info border-info/20",
        default: "bg-white/10 text-white border-white/20",
        running: "bg-primary/10 text-primary border-primary/20 animate-pulse"
    };

    return (
        <span className={`px-2 py-1 rounded-md text-xs font-medium border ${variants[variant]} inline-flex items-center gap-1`}>
            {children}
        </span>
    );
};

export default Badge;
