/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { motion } from 'motion/react';
import { TrendingUp, Users, Network, Settings } from 'lucide-react';
import { MetricData } from '../types';

interface MetricCardsProps {
  metrics: MetricData;
}

export default function MetricCards({ metrics }: MetricCardsProps) {
  const containerVariants = {
    hidden: { opacity: 0, y: -10 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: -10 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } },
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6"
      id="metric-cards-container"
    >
      {/* Option 1 Metric */}
      <motion.div 
        variants={itemVariants}
        className="bg-white border border-brand-border rounded-xl p-5 shadow-sm hover:shadow-md transition-all flex justify-between items-center relative overflow-hidden group"
        id="metric-card-option1"
      >
        <div className="space-y-1">
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none">
            Option 1
          </span>
          <span className="font-display font-extrabold text-3xl text-brand-text">
            {metrics.option1.toLocaleString()}
          </span>
        </div>
        <div className="p-3 bg-cyan-100/50 rounded-xl text-cyan-500 group-hover:scale-110 transition-transform flex-shrink-0">
          <TrendingUp className="h-6 w-6 text-[#00ced1]" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-[#00ced1] opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.div>

      {/* Option 2 Metric */}
      <motion.div 
        variants={itemVariants}
        className="bg-white border border-brand-border rounded-xl p-5 shadow-sm hover:shadow-md transition-all flex justify-between items-center relative overflow-hidden group"
        id="metric-card-option2"
      >
        <div className="space-y-1">
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none">
            Option 2
          </span>
          <span className="font-display font-extrabold text-3xl text-brand-text">
            {metrics.option2.toLocaleString()}
          </span>
        </div>
        <div className="p-3 bg-indigo-100/50 rounded-xl text-indigo-500 group-hover:scale-110 transition-transform flex-shrink-0">
          <Users className="h-6 w-6 text-brand-primary" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-brand-primary opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.div>

      {/* Option 3 Metric */}
      <motion.div 
        variants={itemVariants}
        className="bg-white border border-brand-border rounded-xl p-5 shadow-sm hover:shadow-md transition-all flex justify-between items-center relative overflow-hidden group"
        id="metric-card-option3"
      >
        <div className="space-y-1">
          <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none">
            Option 3
          </span>
          <span className="font-display font-extrabold text-3xl text-brand-text">
            {metrics.option3.toLocaleString()}
          </span>
        </div>
        <div className="p-3 bg-teal-100/50 rounded-xl text-teal-500 group-hover:scale-110 transition-transform flex-shrink-0">
          <Network className="h-6 w-6 text-brand-secondary-light" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-brand-secondary opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.div>

      {/* Progress Bars Card */}
      <motion.div 
        variants={itemVariants}
        className="bg-white border border-brand-border rounded-xl p-5 shadow-sm flex flex-col justify-center space-y-3.5 select-none"
        id="metric-card-progress"
      >
        {/* Progress 1 */}
        <div className="space-y-1">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono font-bold text-slate-400 tracking-wider uppercase">
              Option 1
            </span>
            <span className="font-mono font-bold text-[#4d41df]">{metrics.option1Percent}%</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${metrics.option1Percent}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="bg-gradient-to-r from-brand-primary to-indigo-500 h-full rounded-full"
            />
          </div>
        </div>

        {/* Progress 2 */}
        <div className="space-y-1">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono font-bold text-slate-400 tracking-wider uppercase">
              Option 2
            </span>
            <span className="font-mono font-bold text-indigo-400">{metrics.option2Percent}%</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${metrics.option2Percent}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="bg-indigo-400 h-full rounded-full"
            />
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
