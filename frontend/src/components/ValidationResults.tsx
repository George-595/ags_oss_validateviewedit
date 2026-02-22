"use client";

import { AlertCircle, CheckCircle2, AlertTriangle } from "lucide-react";

interface ValidationResultsProps {
    results: {
        is_valid: boolean;
        file_hash: string;
        errors: string[];
        warnings: string[];
        metadata: {
            version?: string;
            producer?: string;
        };
    };
}

export function ValidationResults({ results }: ValidationResultsProps) {
    return (
        <div className="w-full space-y-6">

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
                    <div className="flex items-center space-x-3 mb-2">
                        <div className={`p-2 rounded-lg ${results.is_valid ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-500'}`}>
                            {results.is_valid ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                        </div>
                        <h3 className="font-semibold text-lg text-white">Status</h3>
                    </div>
                    <p className="text-sm text-zinc-400">{results.is_valid ? "Ready for Production" : "Contains Format Errors"}</p>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
                    <div className="flex items-center space-x-3 mb-2">
                        <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                        <h3 className="font-semibold text-lg text-white">Issues Found</h3>
                    </div>
                    <div className="flex space-x-4 text-sm">
                        <span className="text-red-400 font-medium">{results.errors?.length || 0} Errors</span>
                        <span className="text-yellow-400 font-medium">{results.warnings?.length || 0} Warnings</span>
                    </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
                    <div className="flex items-center space-x-3 mb-2">
                        <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400">
                            <AlertTriangle className="w-5 h-5" />
                        </div>
                        <h3 className="font-semibold text-lg text-white">Metadata</h3>
                    </div>
                    <div className="text-xs text-zinc-400 space-y-1">
                        <p>Version: <span className="text-white">{results.metadata?.version || "Unknown"}</span></p>
                        <p>Producer: <span className="text-white truncate max-w-[150px] inline-block align-bottom">{results.metadata?.producer || "Unknown"}</span></p>
                        <p className="truncate">Hash: <span className="text-white font-mono">{results.file_hash?.substring(0, 8)}...</span></p>
                    </div>
                </div>
            </div>

            {/* Issues Table */}
            <div className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden backdrop-blur-md">
                <div className="px-6 py-4 border-b border-white/10 bg-white/5">
                    <h3 className="font-semibold text-white">Validation Report</h3>
                </div>

                <div className="max-h-[400px] overflow-y-auto">
                    {(!results.errors?.length && !results.warnings?.length) ? (
                        <div className="p-8 text-center text-zinc-500">
                            No errors or warnings found in this file.
                        </div>
                    ) : (
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-zinc-400 bg-white/5 sticky top-0">
                                <tr>
                                    <th className="px-6 py-3 font-medium">Type</th>
                                    <th className="px-6 py-3 font-medium">Description</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {results.errors?.map((err, i) => (
                                    <tr key={`err-${i}`} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-500/10 text-red-500">
                                                Error
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-zinc-300 font-mono text-xs break-words max-w-xl">
                                            {err}
                                        </td>
                                    </tr>
                                ))}
                                {results.warnings?.map((warn, i) => (
                                    <tr key={`warn-${i}`} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-500/10 text-yellow-500">
                                                Warning
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-zinc-300 font-mono text-xs break-words max-w-xl">
                                            {warn}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

        </div>
    );
}
