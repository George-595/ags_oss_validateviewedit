import React from 'react';
import { Layout, Globe, Users, Calendar, HardDrive } from 'lucide-react';

interface ProjectDashboardProps {
    project: {
        name: string;
        client: string;
        contractor: string;
        date: string;
        ags_version: string;
    };
    summary: {
        total_holes: number;
        total_depth: number;
    };
}

export function ProjectDashboard({ project, summary }: ProjectDashboardProps) {
    return (
        <div className="w-full grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {/* Project Header */}
            <div className="md:col-span-2 bg-gradient-to-br from-blue-600/20 to-indigo-600/20 border border-blue-500/20 rounded-3xl p-6 backdrop-blur-md flex flex-col justify-between">
                <div>
                    <div className="flex items-center gap-2 text-blue-400 mb-2">
                        <Layout size={18} />
                        <span className="text-xs font-bold uppercase tracking-widest">Project Name</span>
                    </div>
                    <h2 className="text-3xl font-black text-white leading-tight mb-4">
                        {project.name || "Untitled Project"}
                    </h2>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="flex flex-col">
                        <span className="text-[10px] text-zinc-500 uppercase font-bold mb-1">Client</span>
                        <span className="text-sm text-zinc-300 flex items-center gap-1.5">
                            <Users size={14} className="text-zinc-500" />
                            {project.client}
                        </span>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-[10px] text-zinc-500 uppercase font-bold mb-1">Contractor</span>
                        <span className="text-sm text-zinc-300 flex items-center gap-1.5">
                            <Globe size={14} className="text-zinc-500" />
                            {project.contractor}
                        </span>
                    </div>
                </div>
            </div>

            {/* Stats 1: Inventory */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col justify-between hover:bg-white/10 transition-colors group">
                <div className="flex justify-between items-start">
                    <div className="p-3 bg-blue-500/10 rounded-2xl group-hover:scale-110 transition-transform">
                        <HardDrive className="text-blue-400" size={24} />
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] text-zinc-500 uppercase font-bold mb-1">AGS Version</div>
                        <div className="text-xs font-mono text-blue-300">{project.ags_version}</div>
                    </div>
                </div>
                <div>
                    <div className="text-4xl font-black text-white mb-1">{summary.total_holes}</div>
                    <div className="text-xs text-zinc-400 font-medium">Active Boreholes</div>
                </div>
            </div>

            {/* Stats 2: Metrics */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col justify-between hover:bg-white/10 transition-colors group">
                <div className="flex justify-between items-start">
                    <div className="p-3 bg-emerald-500/10 rounded-2xl group-hover:scale-110 transition-transform">
                        <Calendar className="text-emerald-400" size={24} />
                    </div>
                    <div className="text-right">
                        <div className="text-[10px] text-zinc-500 uppercase font-bold mb-1">Report Date</div>
                        <div className="text-xs font-mono text-emerald-300">{project.date || 'N/A'}</div>
                    </div>
                </div>
                <div>
                    <div className="text-4xl font-black text-white mb-1">{summary.total_depth.toFixed(1)}m</div>
                    <div className="text-xs text-zinc-400 font-medium">Total Drilled Depth</div>
                </div>
            </div>
        </div>
    );
}
