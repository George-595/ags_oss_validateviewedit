import { useState } from 'react';
import { Download, Save } from 'lucide-react';

interface AgsEditorProps {
    initialData: Record<string, Record<string, string | number | null>[]>;
    filename: string;
}

export function AgsEditor({ initialData, filename }: AgsEditorProps) {
    const [data, setData] = useState(initialData);
    const [selectedGroup, setSelectedGroup] = useState<string>(Object.keys(initialData)[0] || "");
    const [isSaving, setIsSaving] = useState(false);

    const handleCellChange = (group: string, rowIndex: number, column: string, value: string) => {
        const newData = { ...data };
        newData[group][rowIndex][column] = value;
        setData(newData);
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/save`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename, tables: data })
            });

            if (!res.ok) throw new Error("Failed to save");

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error(err);
            alert("Error saving file.");
        } finally {
            setIsSaving(false);
        }
    };

    if (!selectedGroup) return <div className="text-zinc-400 p-8 text-center border border-white/10 rounded-2xl bg-white/5">No data available to edit.</div>;

    const currentTable = data[selectedGroup] || [];
    const columns = currentTable.length > 0 ? Object.keys(currentTable[0]) : [];

    return (
        <div className="w-full flex flex-col space-y-4 bg-white/5 border border-white/10 rounded-2xl p-6 relative z-10 backdrop-blur-md">
            <div className="flex justify-between items-center">
                <div className="flex space-x-2 overflow-x-auto pb-2 custom-scrollbar">
                    {Object.keys(data).map((group) => (
                        <button
                            key={group}
                            onClick={() => setSelectedGroup(group)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${selectedGroup === group ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'bg-white/5 text-zinc-300 hover:bg-white/10'
                                }`}
                        >
                            {group} ({data[group].length})
                        </button>
                    ))}
                </div>
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="ml-4 inline-flex items-center px-6 py-2 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-white rounded-lg font-medium transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:pointer-events-none"
                >
                    {isSaving ? <Save className="w-4 h-4 mr-2 animate-pulse" /> : <Download className="w-4 h-4 mr-2" />}
                    Save & Download
                </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-white/10 bg-black/50 custom-scrollbar relative max-h-[600px]">
                <table className="w-full text-sm text-left">
                    <thead className="bg-white/5 text-zinc-300 uppercase font-semibold sticky top-0 z-10">
                        <tr>
                            <th className="px-4 py-3 border-b border-r border-white/10 w-16 text-center bg-zinc-900/90 backdrop-blur-md">#</th>
                            {columns.map((col) => (
                                <th key={col} className="px-4 py-3 border-b border-white/10 whitespace-nowrap bg-zinc-900/90 backdrop-blur-md">
                                    {col}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {currentTable.length === 0 ? (
                            <tr>
                                <td colSpan={columns.length + 1} className="px-4 py-16 text-center text-zinc-500">
                                    No records found in table <span className="font-mono text-zinc-400">{selectedGroup}</span>
                                </td>
                            </tr>
                        ) : (
                            currentTable.map((row, rowIndex) => (
                                <tr key={rowIndex} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="px-4 py-2 border-r border-white/10 text-center text-zinc-500 font-mono text-xs">{rowIndex + 1}</td>
                                    {columns.map((col) => (
                                        <td key={col} className="px-0 py-0 min-w-[200px]">
                                            <input
                                                type="text"
                                                value={row[col] === null ? "" : row[col]}
                                                onChange={(e) => handleCellChange(selectedGroup, rowIndex, col, e.target.value)}
                                                className="w-full h-full px-4 py-3 bg-transparent border-none focus:ring-2 focus:ring-blue-500 focus:outline-none focus:bg-blue-500/10 text-zinc-100 transition-colors"
                                            />
                                        </td>
                                    ))}
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
