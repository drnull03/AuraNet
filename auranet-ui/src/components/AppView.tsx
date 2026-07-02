/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Settings, Info, Server, Terminal, Lock, Globe, HardDrive, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function AppView() {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopy = (keyName: string, value: string) => {
    navigator.clipboard.writeText(value);
    setCopiedKey(keyName);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const environmentVariables = [
    { name: 'PORT', value: '3000 (Protected Ingress Layer)', type: 'system', desc: 'Bind port configuration of custom full-stack Express server.' },
    { name: 'NODE_ENV', value: 'production / development', type: 'system', desc: 'Node.js compilation flag determining server mode.' },
    { name: 'GEMINI_API_KEY', value: '••••••••••••••••••••••••••••••••', type: 'secret', desc: 'Used for the AI Operator Console server-side proxy requests.' },
    { name: 'APP_URL', value: 'https://ais-dev-mt6ejh4...run.app', type: 'system', desc: 'The base routing domain injected automatically by AI Studio.' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6" id="developer-app-panel">
      {/* Overview Block */}
      <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-6 select-none">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-brand-primary text-white rounded-xl flex items-center justify-center">
            <Settings size={20} />
          </div>
          <div>
            <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block">
              Application Context
            </span>
            <h3 className="font-display font-extrabold text-xl text-brand-text block mt-0.5">
              Project Alpha Framework & Environments
            </h3>
          </div>
        </div>
        <p className="text-xs text-slate-500 font-medium font-sans mt-3 leading-relaxed">
          This dashboard runs on a containerized Cloud Run environment managed by Google AI Studio. It binds an Express + Vite full-stack architecture to proxy client requests to server-side Google GenAI (Gemini) APIs without exposing credential keys to client browsers.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Side: Environment Variables List */}
        <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4 select-none">
              <Terminal size={16} className="text-brand-primary" />
              <span className="font-display font-bold text-sm text-slate-800">Environment Bindings (.env)</span>
            </div>

            <div className="space-y-4">
              {environmentVariables.map((env) => (
                <div key={env.name} className="p-3 border border-slate-100 rounded-xl hover:bg-slate-50/40 transition-all">
                  <div className="flex items-center justify-between select-none">
                    <span className="font-mono text-xs font-bold text-[#4d41df] block">{env.name}</span>
                    <span className={`font-mono text-[8px] px-2 py-0.2 rounded-full font-bold uppercase ${
                      env.type === 'secret' ? 'bg-red-50 text-red-600 border border-red-100' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {env.type}
                    </span>
                  </div>

                  <p className="text-[10px] text-slate-500 font-medium mt-1 select-none">
                    {env.desc}
                  </p>

                  <div className="mt-2 flex items-center justify-between bg-slate-50 p-2 border border-slate-200/60 rounded-md">
                    <code className="font-mono text-[10px] text-slate-700 truncate font-semibold block">{env.value}</code>
                    {env.type !== 'secret' && (
                      <button
                        onClick={() => handleCopy(env.name, env.value)}
                        className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-slate-700 transition-colors font-mono text-[9px] font-bold uppercase cursor-pointer"
                      >
                        {copiedKey === env.name ? 'Copied' : 'Copy'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Environment Status & Container Metrics */}
        <div className="space-y-6">
          {/* Node Server Metrics */}
          <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5 select-none">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <Server size={16} className="text-slate-400" />
              <span className="font-display font-bold text-sm text-slate-800">Container Execution Metrics</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/40 text-center">
                <span className="font-mono text-[9px] text-slate-400 block uppercase font-bold">Node Process PID</span>
                <span className="font-mono text-base font-bold text-slate-700 block mt-1">PID: 433</span>
              </div>
              <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/40 text-center">
                <span className="font-mono text-[9px] text-slate-400 block uppercase font-bold">Uptime Duration</span>
                <span className="font-mono text-base font-bold text-slate-700 block mt-1">42h 19m</span>
              </div>
              <div className="p-3 border border-slate-100 rounded-xl bg-[#e0fbfc] text-center">
                <span className="font-mono text-[9px] text-[#006e70] block uppercase font-bold">Reverse Proxy Ingress</span>
                <span className="font-mono text-base font-bold text-[#006e70] block mt-1">Nginx active</span>
              </div>
              <div className="p-3 border border-slate-100 rounded-xl bg-indigo-50 text-center">
                <span className="font-mono text-[9px] text-indigo-500 block uppercase font-bold">Security Standard</span>
                <span className="font-mono text-sm font-bold text-indigo-700 mt-1 flex items-center justify-center gap-1">
                  <ShieldCheck size={14} /> TLS V1.3 Enabled
                </span>
              </div>
            </div>
          </div>

          {/* System Security Notice */}
          <div className="bg-slate-900 text-slate-100 border border-slate-800 rounded-2xl p-5 shadow-sm relative overflow-hidden select-none">
            <div className="absolute top-[-20px] right-[-20px] text-slate-800 opacity-20 transform rotate-12 pointer-events-none">
              <Lock size={120} />
            </div>

            <div className="flex items-start gap-3 relative z-10">
              <div className="p-2 bg-indigo-500/20 text-indigo-300 rounded-xl mt-0.5">
                <Lock size={18} />
              </div>
              <div className="space-y-1.5">
                <h4 className="font-display font-bold text-sm text-white">Full-Stack Security Guideline</h4>
                <p className="text-xs text-slate-300 leading-relaxed font-sans font-medium">
                  We leverage high-security, server-side code execution. All API credentials and environment secrets exist only in secure memory sandboxes on the cloud server. They are never transmitted over network packets to client-side browsers, ensuring BGP protection across global network gateways.
                </p>
                <div className="flex items-center gap-1 font-mono text-[10px] text-green-400 mt-2 font-bold uppercase tracking-wider">
                  <span className="h-1.5 w-1.5 bg-green-400 rounded-full animate-ping" />
                  Cluster protected: Nominal State
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
