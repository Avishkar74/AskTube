import React from 'react';
import { Link } from 'react-router-dom';
import { Youtube, User, Moon, Sun } from 'lucide-react';
import Button from './ui/Button';

const Header: React.FC = () => {
    return (
        <header className="flex items-center justify-between py-6 mb-8">
            <Link to="/" className="flex items-center gap-3 group">
                <div className="p-2 bg-gradient-to-br from-primary to-secondary rounded-xl shadow-glow group-hover:scale-105 transition-transform">
                    <Youtube className="text-slate-900" size={24} fill="currentColor" />
                </div>
                <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                    AskTube
                </span>
            </Link>

            <div className="flex items-center gap-4">
                <Button variant="ghost" size="sm" className="hidden md:flex">
                    <Moon size={20} />
                </Button>
                <div className="w-10 h-10 rounded-full bg-surface border border-white/10 flex items-center justify-center cursor-pointer hover:border-primary/50 transition-colors">
                    <User size={20} className="text-zinc-400" />
                </div>
            </div>
        </header>
    );
};

export default Header;
