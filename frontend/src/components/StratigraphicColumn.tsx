import { useState } from 'react';

interface GeolRow {
    top: number;
    bottom: number;
    description: string;
    legend: string;
}

interface Hole {
    id: string;
    max_depth: number;
    geology: GeolRow[];
}

interface StratigraphicColumnProps {
    data: { holes: Hole[] };
}

const getColorForLegend = (legend: string) => {
    const hash = legend.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const hue = hash % 360;
    return `hsl(${hue}, 60%, 40%)`;
};

export function StratigraphicColumn({ data }: StratigraphicColumnProps) {
    const { holes } = data;
    // Initial selection: prefer a hole that actually has geology data
    const [selectedHoleId, setSelectedHoleId] = useState<string>(() => {
        if (!holes || holes.length === 0) return "";
        const holeWithGeol = holes.find(h => h.geology && h.geology.length > 0);
        return holeWithGeol ? holeWithGeol.id : holes[0].id;
    });

    if (!holes || holes.length === 0) {
        return (
            <div className="text-zinc-400 p-12 text-center bg-white/5 rounded-3xl border border-white/10 backdrop-blur-sm">
                <h3 className="text-xl font-semibold mb-2 text-white">No Stratigraphy Data</h3>
                <p>This AGS file does not contain standard LOCA and GEOL tables required for rendering.</p>
            </div>
        );
    }

    const selectedHole = holes.find(h => h.id === selectedHoleId) || holes[0];
    const maxDepth = selectedHole.max_depth || (selectedHole.geology && selectedHole.geology.length > 0 ? selectedHole.geology.reduce((max, g) => Math.max(max, g.bottom), 0) : 10);

    // Pixels per meter scale for rendering
    const scale = 50;

    // Calculate total height needed
    const containerHeight = Math.max(600, maxDepth * scale);

    return (
        <div className="w-full flex flex-col space-y-6 bg-white/5 border border-white/10 rounded-3xl p-6 sm:p-8 relative z-10 backdrop-blur-md">

            {/* Tab selector for Boreholes */}
            <div className="flex flex-wrap gap-2 pb-4 border-b border-white/10">
                {holes.map((hole) => (
                    <button
                        key={hole.id}
                        onClick={() => setSelectedHoleId(hole.id)}
                        className={`px-4 py-2 rounded-xl text-left transition-all flex flex-col min-w-[120px] ${selectedHoleId === hole.id
                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20 scale-105'
                            : 'bg-white/5 text-zinc-300 hover:bg-white/10 hover:scale-105'
                            }`}
                    >
                        <span className="font-bold">{hole.id}</span>
                        <span className="text-xs opacity-70 mt-0.5">{hole.max_depth}m Depth ({hole.geology.length} Strata)</span>
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-4">
                {/* Visual Log */}
                <div className="col-span-1 flex justify-center bg-black/40 rounded-2xl p-8 border border-white/5 relative overflow-y-auto custom-scrollbar" style={{ maxHeight: '800px' }}>

                    <div className="relative border-x border-white/20 w-[180px] bg-[#1a1a1a] shadow-2xl rounded-sm" style={{ height: `${containerHeight}px` }}>
                        {/* Depth axis markers */}
                        <div className="absolute -left-12 top-0 bottom-0 w-10 border-r border-white/10 flex flex-col">
                            {Array.from({ length: Math.ceil(maxDepth) + 1 }).map((_, i) => (
                                <div key={i} className="absolute right-0 text-[10px] text-zinc-500 pr-2 -translate-y-1/2" style={{ top: `${i * scale}px` }}>
                                    {i}m
                                </div>
                            ))}
                        </div>

                        {selectedHole.geology.map((layer, idx) => {
                            const height = (layer.bottom - layer.top) * scale;
                            const topPos = layer.top * scale;
                            return (
                                <div
                                    key={idx}
                                    className="absolute left-0 w-full flex items-center justify-center overflow-hidden border-b border-white/10 group cursor-pointer transition-all hover:z-20 hover:scale-105 shadow-lg"
                                    style={{
                                        top: `${topPos}px`,
                                        height: `${height}px`,
                                        backgroundColor: getColorForLegend(layer.legend)
                                    }}
                                    title={layer.description}
                                >
                                    <span className="text-white/90 font-bold tracking-wider text-sm pointer-events-none drop-shadow-md">
                                        {layer.legend}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Legend and Details */}
                <div className="col-span-1 md:col-span-2 flex flex-col space-y-4">
                    <h3 className="text-2xl font-bold text-white mb-2">Detailed Log: <span className="text-blue-400">{selectedHole.id}</span></h3>

                    <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3" style={{ maxHeight: '700px' }}>
                        {selectedHole.geology.length === 0 ? (
                            <div className="text-zinc-500 italic">No geology layers defined.</div>
                        ) : (
                            selectedHole.geology.map((layer, idx) => (
                                <div key={idx} className="bg-white/5 border border-white/10 rounded-xl p-4 flex gap-4 hover:bg-white/10 transition-colors">
                                    <div
                                        className="w-12 h-12 rounded-lg flex-shrink-0 flex items-center justify-center border border-white/20 shadow-inner"
                                        style={{ backgroundColor: getColorForLegend(layer.legend) }}
                                    >
                                        <span className="text-white font-bold text-xs">{layer.legend}</span>
                                    </div>
                                    <div>
                                        <div className="text-sm font-semibold text-blue-300 mb-1">
                                            {layer.top.toFixed(2)}m - {layer.bottom.toFixed(2)}m
                                        </div>
                                        <p className="text-sm text-zinc-300 leading-relaxed">
                                            {layer.description || <span className="text-zinc-600 italic">No description provided</span>}
                                        </p>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

        </div>
    );
}
