import { motion } from 'framer-motion';
import React, { ReactNode } from 'react';

interface SlideProps {
  children: ReactNode;
  isActive: boolean;
  color?: string;
}

export const Slide: React.FC<SlideProps> = ({ children, isActive, color = 'bg-brand-dark' }) => {
  return (
    <motion.div 
      className={`absolute inset-0 flex flex-col items-center justify-center p-8 text-center ${color}`}
      initial={{ opacity: 0, x: 100 }}
      animate={{ 
        opacity: isActive ? 1 : 0, 
        x: isActive ? 0 : -100,
        pointerEvents: isActive ? 'auto' : 'none'
      }}
      transition={{ duration: 0.5, type: 'spring' }}
    >
      {children}
    </motion.div>
  );
};
