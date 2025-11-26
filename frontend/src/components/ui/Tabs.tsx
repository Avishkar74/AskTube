import React from 'react';

interface TabsProps {
    value: string;
    onValueChange: (value: string) => void;
    children: React.ReactNode;
    className?: string;
}

export const Tabs: React.FC<TabsProps> = ({ value, onValueChange, children, className = '' }) => {
    // Clone children to pass selectedValue and onValueChange to them
    const childrenWithProps = React.Children.map(children, child => {
        if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<any>, { selectedValue: value, onValueChange });
        }
        return child;
    });

    return <div className={`w-full flex flex-col h-full ${className}`}>{childrenWithProps}</div>;
};

export const TabsList: React.FC<{ children: React.ReactNode; className?: string; selectedValue?: string; onValueChange?: (value: string) => void }> = ({ children, className = '', selectedValue, onValueChange }) => {
    const childrenWithProps = React.Children.map(children, child => {
        if (React.isValidElement(child)) {
            return React.cloneElement(child as React.ReactElement<any>, { selectedValue, onClick: onValueChange });
        }
        return child;
    });
    return <div className={`flex border-b border-white/10 ${className}`}>{childrenWithProps}</div>;
};

interface TabsTriggerProps {
    value: string;
    selectedValue?: string;
    onClick?: (value: string) => void;
    children: React.ReactNode;
    className?: string;
}

export const TabsTrigger: React.FC<TabsTriggerProps> = ({ value, selectedValue, onClick, children, className = '' }) => {
    const isSelected = value === selectedValue;
    return (
        <button
            onClick={() => onClick && onClick(value)}
            className={`px-6 py-3 font-medium text-sm transition-all relative ${isSelected ? 'text-primary' : 'text-zinc-400 hover:text-white'
                } ${className}`}
        >
            {children}
            {isSelected && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary shadow-[0_0_10px_rgba(0,178,255,0.5)]" />
            )}
        </button>
    );
};

export const TabsContent: React.FC<{ value: string; selectedValue?: string; children: React.ReactNode; className?: string }> = ({ value, selectedValue, children, className = '' }) => {
    if (value !== selectedValue) return null;
    return <div className={`flex-1 overflow-hidden ${className}`}>{children}</div>;
};
