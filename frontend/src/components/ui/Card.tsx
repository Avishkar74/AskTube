import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
    onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ children, className = '', hover = false, onClick }) => {
    return (
        <div
            onClick={onClick}
            className={`bg-surface rounded-2xl border border-white/5 shadow-lg p-6 ${hover ? 'transition-all hover:border-primary/30 hover:shadow-glow cursor-pointer' : ''} ${className}`}
        >
            {children}
        </div>
    );
};

export default Card;
