"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileUp, Loader2, RefreshCw, Download } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { ValidationResults } from "@/components/ValidationResults";
import { AgsEditor } from "@/components/AgsEditor";
import { StratigraphicColumn } from "@/components/StratigraphicColumn";

interface ValidationData {
  is_valid: boolean;
  file_hash: string;
  errors: string[];
  warnings: string[];
  metadata: {
    version?: string;
    producer?: string;
  };
}

interface StratigraphyData {
  holes: Array<{
    id: string;
    max_depth: number;
    geology: Array<{
      top: number;
      bottom: number;
      description: string;
      legend: string;
    }>;
  }>;
}

export default function LandingPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState<ValidationData | null>(null);
  const [parsedData, setParsedData] = useState<Record<string, Record<string, string | number | null>[]> | null>(null);
  const [stratigraphy, setStratigraphy] = useState<StratigraphyData | null>(null);
  const [activeTab, setActiveTab] = useState<'validate' | 'edit' | 'stratigraphy'>('validate');
  const [isExporting, setIsExporting] = useState(false);

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/octet-stream": [".ags"],
      "text/plain": [".ags"],
    },
    maxFiles: 1,
  });

  // In production (Vercel), NEXT_PUBLIC_API_URL is unset → API_BASE is '' → relative URLs
  // In local dev, set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
  const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

  const handleValidation = async () => {
    if (!file) return;
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const [valRes, parseRes] = await Promise.all([
        fetch(`${API_BASE}/api/validate`, {
          method: "POST",
          body: formData,
        }),
        fetch(`${API_BASE}/api/parse`, {
          method: "POST",
          body: formData,
        })
      ]);

      if (!valRes.ok) throw new Error(`Validation failed: ${valRes.status}`);
      if (!parseRes.ok) throw new Error(`Parse failed: ${parseRes.status}`);

      const data = await valRes.json();
      const parseData = await parseRes.json();

      setResults(data);
      setParsedData(parseData.parsed_data);
      setStratigraphy(parseData.stratigraphy);
    } catch (e) {
      console.error(e);
      setResults({
        is_valid: false,
        file_hash: "",
        errors: ["Failed to connect to validation engine."],
        warnings: [],
        metadata: {}
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleExportToExcel = async () => {
    if (!file) return;
    setIsExporting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/convert/to-excel`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Export failed");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name.replace(/\.ags$/i, ".xlsx");
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert("Failed to export to Excel.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <main className="relative min-h-screen w-full flex flex-col items-center justify-center p-4 py-20 overflow-hidden bg-black text-white">
      {/* Background ambient lighting */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 blur-[120px] rounded-full point-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-violet-600/20 blur-[120px] rounded-full point-events-none" />

      <div className="z-10 w-full max-w-4xl mx-auto flex flex-col items-center space-y-12">

        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-6"
        >
          <a
            href="https://quoresoftware.com/quore-geotechnical"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-full border border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20 px-4 py-1.5 text-sm font-medium text-blue-200 transition-all hover:scale-105 cursor-pointer shadow-[0_0_15px_rgba(59,130,246,0.2)]"
          >
            <span className="flex h-2 w-2 rounded-full bg-blue-500 mr-2 animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.8)]"></span>
            Powered by Quore Geotechnical
          </a>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight bg-gradient-to-br from-white to-white/40 bg-clip-text text-transparent">
            AGS Data Validator.
          </h1>
          <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto">
            Drop your AGS4 file to instantly validate formatting, identify structure errors, and ensure compatibility with enterprise endpoints.
          </p>
        </motion.div>

        {/* Upload Zone */}
        <AnimatePresence mode="wait">
          {!results && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-2xl"
            >
              <div
                {...getRootProps()}
                className={`
                  relative overflow-hidden group border-2 border-dashed rounded-3xl p-16 transition-all duration-500 ease-out cursor-pointer
                  ${isDragActive ? 'border-blue-500 bg-blue-500/5' : 'border-white/10 hover:border-white/30 bg-white/5 hover:bg-white/10'}
                `}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center justify-center space-y-6 text-center z-10 relative">
                  <div className="p-4 rounded-2xl bg-white/5 shadow-2xl backdrop-blur-sm border border-white/10">
                    <FileUp className={`w-10 h-10 text-zinc-300 transition-transform duration-500 ${isDragActive ? 'scale-110 text-blue-400' : ''}`} />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">
                      {isDragActive ? "Drop the file here." : file ? file.name : "Click or drag your AGS file"}
                    </h3>
                    <p className="text-sm text-zinc-500">
                      {file ? `${(file.size / 1024).toFixed(1)} KB • Ready to validate` : "Supports standard .ags formatting"}
                    </p>
                  </div>

                  {file && (
                    <motion.button
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      onClick={(e) => { e.stopPropagation(); handleValidation(); }}
                      disabled={isUploading}
                      className="mt-6 inline-flex items-center justify-center rounded-full bg-white text-black px-8 py-3 text-sm font-semibold transition-all hover:bg-zinc-200 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
                    >
                      {isUploading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : "Run Validation"}
                    </motion.button>
                  )}
                </div>

                {/* Hover gradient effect inside dropzone */}
                <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/0 via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
              </div>
            </motion.div>
          )}

          {results && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full flex flex-col items-center"
            >
              <div className="flex flex-wrap justify-center gap-4 mb-8 relative z-10 w-full">
                <button
                  onClick={() => setActiveTab('validate')}
                  className={`px-8 py-3 rounded-full font-medium transition-all duration-300 ${activeTab === 'validate'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                    : 'bg-white/5 text-zinc-300 hover:bg-white/10 hover:scale-105 border border-white/10'
                    }`}
                >
                  Validation Report
                </button>
                <button
                  onClick={() => setActiveTab('edit')}
                  className={`px-8 py-3 rounded-full font-medium transition-all duration-300 ${activeTab === 'edit'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                    : 'bg-white/5 text-zinc-300 hover:bg-white/10 hover:scale-105 border border-white/10'
                    }`}
                >
                  Edit & Save Datagrid
                </button>
                <button
                  onClick={() => setActiveTab('stratigraphy')}
                  className={`px-8 py-3 rounded-full font-medium transition-all duration-300 ${activeTab === 'stratigraphy'
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 scale-105'
                    : 'bg-white/5 text-zinc-300 hover:bg-white/10 hover:scale-105 border border-white/10'
                    }`}
                >
                  View Stratigraphic Column
                </button>
              </div>

              <div className="w-full relative min-h-[400px]">
                {activeTab === 'validate' && <ValidationResults results={results} />}
                {activeTab === 'edit' && parsedData && file && <AgsEditor initialData={parsedData} filename={file.name} />}
                {activeTab === 'stratigraphy' && stratigraphy && <StratigraphicColumn data={stratigraphy} />}
              </div>

              <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mt-12 mb-20 relative z-10 w-full">
                <button
                  onClick={() => { setResults(null); setFile(null); setParsedData(null); setStratigraphy(null); setActiveTab('validate'); }}
                  className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-8 py-4 text-sm font-medium text-white transition-all hover:bg-white/10 hover:scale-105 active:scale-95 shadow-xl w-full sm:w-auto"
                >
                  <RefreshCw className="w-5 h-5 mr-3" />
                  Validate Another File
                </button>
                <button
                  onClick={handleExportToExcel}
                  disabled={isExporting}
                  className="inline-flex items-center justify-center rounded-full px-8 py-4 text-sm font-bold text-white transition-all hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(59,130,246,0.5)] bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 hover:shadow-[0_0_30px_rgba(59,130,246,0.8)] disabled:opacity-50 disabled:pointer-events-none border border-blue-400/30 w-full sm:w-auto"
                >
                  {isExporting ? <Loader2 className="w-5 h-5 mr-3 animate-spin" /> : <Download className="w-5 h-5 mr-3" />}
                  Export to Excel
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </main>
  );
}
