/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { User, Mail, Shield, BookOpen, Key, CheckCircle, BellRing, Settings } from 'lucide-react';
import { USER_PROFILE } from '../data';

export default function AccountView() {
  const [profile, setProfile] = useState(USER_PROFILE);
  const [success, setSuccess] = useState(false);
  const [alerts, setAlerts] = useState({
    critical: true,
    warnings: true,
    stats: false,
    emailReport: true,
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-6 max-w-4xl mx-auto" id="account-profile-panel">
      <div className="border-b border-brand-border pb-4 mb-6">
        <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block select-none">
          User Settings & Security
        </span>
        <h3 className="font-display font-extrabold text-xl text-brand-text block mt-0.5">
          Emily Rose's Core Profile
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Side: Avatar Display Card */}
        <div className="md:col-span-1 flex flex-col items-center p-6 border border-slate-100 rounded-xl bg-slate-50/50 text-center">
          <div className="relative group select-none">
            <img 
              src={profile.avatar} 
              alt={profile.name} 
              className="h-28 w-28 rounded-full border-4 border-[#4d41df] object-cover shadow-md group-hover:scale-105 transition-transform"
              referrerPolicy="no-referrer"
            />
            <span className="absolute bottom-1 right-1 h-5 w-5 bg-green-500 rounded-full border-2 border-white" />
          </div>

          <h4 className="font-display font-bold text-base text-slate-800 mt-4 leading-none">{profile.name}</h4>
          <span className="font-mono text-[10px] text-brand-primary font-bold uppercase tracking-wider mt-2 bg-indigo-50 px-2.5 py-0.5 rounded-full">
            Senior Architect
          </span>

          <p className="text-xs text-slate-500 font-medium font-sans leading-relaxed mt-4 max-w-xs">
            {profile.bio}
          </p>

          {/* Core Credentials Badges */}
          <div className="mt-6 w-full space-y-2 border-t border-slate-200/60 pt-4 text-left">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-600">
              <Shield size={14} className="text-brand-primary" />
              <span>Auth Level: Superadmin (L1)</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-600">
              <Key size={14} className="text-brand-secondary-light" />
              <span>GPG Signing: Configured</span>
            </div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-600">
              <BookOpen size={14} className="text-indigo-400" />
              <span>Consensus Spec: Graduation '24</span>
            </div>
          </div>
        </div>

        {/* Right Side: Form Configuration */}
        <div className="md:col-span-2 space-y-6">
          <form onSubmit={handleSave} className="space-y-4">
            <h4 className="font-display font-bold text-sm text-brand-text flex items-center gap-2">
              <Settings size={16} className="text-brand-primary" />
              <span>Profile Settings</span>
            </h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Full Name</label>
                <input 
                  type="text" 
                  value={profile.name}
                  onChange={(e) => setProfile(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary transition-all"
                />
              </div>

              <div className="space-y-1">
                <label className="font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider block">System Role</label>
                <input 
                  type="text" 
                  value={profile.role}
                  onChange={(e) => setProfile(prev => ({ ...prev, role: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary transition-all"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Primary Contact Email</label>
              <div className="relative">
                <Mail size={14} className="absolute left-3 top-2.5 text-slate-400" />
                <input 
                  type="email" 
                  value={profile.email}
                  onChange={(e) => setProfile(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-brand-border rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary transition-all"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-mono text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Profile Biography</label>
              <textarea 
                rows={3}
                value={profile.bio}
                onChange={(e) => setProfile(prev => ({ ...prev, bio: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary transition-all"
              />
            </div>

            {/* Notification Preferences */}
            <div className="border-t border-brand-border pt-4 mt-6">
              <h4 className="font-display font-bold text-sm text-brand-text flex items-center gap-2 mb-4">
                <BellRing size={16} className="text-brand-primary" />
                <span>Simulated Node Alert Routing</span>
              </h4>

              <div className="space-y-2">
                <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={alerts.critical} 
                    onChange={(e) => setAlerts(prev => ({ ...prev, critical: e.target.checked }))}
                    className="rounded text-brand-primary focus:ring-brand-primary h-4 w-4"
                  />
                  <span>Dispatch telemetry alert immediately upon offline status (Ping Failure)</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={alerts.warnings} 
                    onChange={(e) => setAlerts(prev => ({ ...prev, warnings: e.target.checked }))}
                    className="rounded text-brand-primary focus:ring-brand-primary h-4 w-4"
                  />
                  <span>Warn on high CPU / Memory load (&gt;90% threshold spikes)</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={alerts.emailReport} 
                    onChange={(e) => setAlerts(prev => ({ ...prev, emailReport: e.target.checked }))}
                    className="rounded text-brand-primary focus:ring-brand-primary h-4 w-4"
                  />
                  <span>Send daily compiled consensus digest reports to {profile.email}</span>
                </label>
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-brand-border pt-4">
              {success && (
                <div className="flex items-center gap-1.5 text-green-600 text-xs font-semibold">
                  <CheckCircle size={14} />
                  <span>Profile updated and signed successfully!</span>
                </div>
              )}
              <div />
              <button 
                type="submit"
                className="px-5 py-2 bg-[#4d41df] hover:bg-indigo-600 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm hover:scale-[1.01] cursor-pointer"
                id="btn-account-save"
              >
                Save Settings
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
