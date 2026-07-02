/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { PenSquare, Eye, FileText, CheckCircle2, History, AlertCircle } from 'lucide-react';

interface SavedPost {
  id: string;
  title: string;
  category: string;
  author: string;
  date: string;
  content: string;
}

export default function PostsView() {
  const [posts, setPosts] = useState<SavedPost[]>([
    {
      id: 'p1',
      title: 'Emergency Consensus Guideline for Asia South Region (Mumbai)',
      category: 'Protocol Alert',
      author: 'Emily Rose',
      date: 'July 01, 2026',
      content: 'Under peak CPU congestion exceeding 92% on the Asia South sensor nodes, we must transiently scale back telemetry packet submission frequency. Adjust the local sensor polling timer block from 100ms to 250ms in the environment configuration settings to mitigate message queue lockups and prevent frame drops on the centralized visualization hub.'
    },
    {
      id: 'p2',
      title: 'Consensus Migration Spec: Graduation 2024 to Production Mesh',
      category: 'Design Blueprint',
      author: 'Emily Rose',
      date: 'June 28, 2026',
      content: 'This documents our planned transition from Paxos-lite to multi-raft cluster topology for the high-availability global gateway rings. Initial simulations indicate a 14% improvement in average query resolution speed and full recovery from single-region partitions.'
    }
  ]);

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Protocol Alert');
  const [content, setContent] = useState('');
  const [viewMode, setViewMode] = useState<'edit' | 'preview'>('edit');
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    const newPost: SavedPost = {
      id: `p-${Date.now()}`,
      title,
      category,
      author: 'Emily Rose',
      date: new Date().toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }),
      content,
    };

    setPosts([newPost, ...posts]);
    setTitle('');
    setContent('');
    setViewMode('edit');
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6" id="posts-editor-panel">
      {/* Header Info */}
      <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5 select-none">
        <span className="font-mono text-xs font-bold text-slate-400 tracking-wider uppercase block">
          Write & Publish Guidelines
        </span>
        <h3 className="font-display font-extrabold text-xl text-brand-text block mt-0.5">
          System Maintenance & Protocol Log Publisher
        </h3>
        <p className="text-xs text-slate-500 mt-1.5 font-medium leading-relaxed">
          Document real-time topology amendments, incident logs, or network parameter modifications. All updates are compiled into global ledger logs automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Form Editor (takes 2 cols) */}
        <div className="lg:col-span-2 bg-white border border-brand-border rounded-2xl shadow-sm p-5 flex flex-col justify-between">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-2">
              <div className="flex items-center gap-2">
                <PenSquare size={16} className="text-brand-primary animate-pulse" />
                <span className="font-display font-bold text-sm text-slate-800">Draft New Log Entry</span>
              </div>

              {/* View/Edit Toggle */}
              <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200 select-none">
                <button
                  type="button"
                  onClick={() => setViewMode('edit')}
                  className={`px-3 py-1 text-[11px] font-mono font-bold uppercase rounded-md transition-all ${
                    viewMode === 'edit' ? 'bg-white text-brand-primary shadow-xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('preview')}
                  className={`px-3 py-1 text-[11px] font-mono font-bold uppercase rounded-md transition-all ${
                    viewMode === 'preview' ? 'bg-white text-brand-primary shadow-xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  Preview
                </button>
              </div>
            </div>

            {viewMode === 'edit' ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="font-mono text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Log Header Title</label>
                    <input
                      type="text"
                      required
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. EU Region Load Balancer Recalibration..."
                      className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary focus:ring-2 focus:ring-indigo-100 transition-all"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-mono text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Log Category Type</label>
                    <select
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-brand-border rounded-lg text-xs font-semibold text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary focus:ring-2 focus:ring-indigo-100 transition-all cursor-pointer"
                    >
                      <option value="Protocol Alert">Protocol Alert</option>
                      <option value="Design Blueprint">Design Blueprint</option>
                      <option value="Incident Remediation">Incident Remediation</option>
                      <option value="Cluster Metric Report">Cluster Metric Report</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-mono text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Body Content (Markdown Supported)</label>
                  <textarea
                    rows={8}
                    required
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Provide technical descriptions, root-cause investigations, topology changes, or mitigation steps..."
                    className="w-full px-4 py-3 bg-slate-50 border border-brand-border rounded-lg text-xs font-mono font-medium text-slate-800 focus:outline-hidden focus:bg-white focus:border-brand-primary focus:ring-2 focus:ring-indigo-100 transition-all leading-relaxed"
                  />
                </div>
              </div>
            ) : (
              // Live Preview Mode
              <div className="border border-slate-100 rounded-xl p-4 bg-slate-50/50 min-h-[220px] select-none">
                <span className="font-mono text-[9px] text-[#006e70] bg-[#e0fbfc] px-2 py-0.5 rounded-full font-bold uppercase">
                  {category}
                </span>
                <h4 className="font-display font-extrabold text-lg text-slate-800 mt-2">
                  {title || 'Untitled Draft Entry'}
                </h4>
                <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400 mt-1 mb-4">
                  <span>Author: Emily Rose</span>
                  <span>|</span>
                  <span>Date: Published Live on Submit</span>
                </div>
                <div className="prose prose-sm max-w-none text-xs text-slate-600 font-sans leading-relaxed whitespace-pre-wrap">
                  {content || '*No content written yet. Switch back to Edit to begin.*'}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between border-t border-brand-border pt-4 mt-6">
              {success ? (
                <span className="flex items-center gap-1 text-green-600 text-xs font-bold animate-fade-in">
                  <CheckCircle2 size={14} /> Log Published Successfully!
                </span>
              ) : (
                <span className="text-[10px] text-slate-400 font-mono font-semibold flex items-center gap-1">
                  <AlertCircle size={12} /> Standard cryptographic signatures appended on submission
                </span>
              )}

              <button
                type="submit"
                className="px-5 py-2.5 bg-[#4d41df] hover:bg-indigo-600 text-white rounded-lg text-xs font-bold uppercase tracking-wider shadow-sm hover:scale-[1.01] transition-all cursor-pointer"
                id="btn-posts-submit"
              >
                Publish Entry
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Previously Published Logs Feed */}
        <div className="bg-white border border-brand-border rounded-2xl shadow-sm p-5 flex flex-col">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4 select-none">
            <History size={16} className="text-slate-400" />
            <span className="font-display font-bold text-sm text-slate-800">Published Log Archive</span>
          </div>

          <div className="space-y-4 overflow-y-auto max-h-[460px] pr-1">
            {posts.map((post) => {
              const isAlert = post.category === 'Protocol Alert';
              return (
                <div
                  key={post.id}
                  className="p-3.5 border border-slate-100 rounded-xl hover:border-slate-200 bg-slate-50/20 transition-all group"
                  id={`saved-post-item-${post.id}`}
                >
                  <div className="flex items-center justify-between select-none">
                    <span className={`font-mono text-[8px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      isAlert ? 'bg-amber-50 text-amber-600 border border-amber-100' : 'bg-indigo-50 text-indigo-600 border border-indigo-100'
                    }`}>
                      {post.category}
                    </span>
                    <span className="font-mono text-[9px] text-slate-400">{post.date}</span>
                  </div>
                  
                  <h5 className="font-display font-bold text-xs text-slate-800 mt-2 group-hover:text-[#4d41df] transition-colors leading-snug">
                    {post.title}
                  </h5>
                  
                  <p className="text-[11px] text-slate-500 font-medium font-sans leading-relaxed mt-2 line-clamp-3">
                    {post.content}
                  </p>
                  
                  <div className="border-t border-slate-100/50 pt-2 mt-2 flex justify-between select-none font-mono text-[9px] text-slate-400">
                    <span>Sig: SHA-256</span>
                    <span>Operator: {post.author}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
