import { useState } from 'react';

interface GeolRow {
    top: number;
    bottom: number;
    description: string;
    legend: string;
}

interface SampleRow {
    top: number;
    type: string;
    ref: string;
    id: string;
}

interface SptRow {
    top: number;
    n_value: string;
    n_numeric: number | null;
}

interface WaterRow {
    depth: number;
    time: string;
    remarks: string;
}

interface CasingRow {
    depth: number;
    diameter: number;
}

interface DiameterRow {
    depth: number;
    diameter: number;
}

interface Hole {
    id: string;
    max_depth: number;
    geology: GeolRow[];
    samples?: SampleRow[];
    spts?: SptRow[];
    water?: WaterRow[];
    casings?: CasingRow[];
    diameters?: DiameterRow[];
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

    const hasExtraData = (selectedHole.samples && selectedHole.samples.length > 0) ||
        (selectedHole.spts && selectedHole.spts.length > 0) ||
        (selectedHole.water && selectedHole.water.length > 0) ||
        (selectedHole.casings && selectedHole.casings.length > 0);

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

            <div className={`grid grid-cols-1 ${hasExtraData ? 'md:grid-cols-4' : 'md:grid-cols-3'} gap-8 pt-4`}>
                {/* Visual Log */}
                <div className="col-span-1 flex justify-center bg-black/40 rounded-2xl p-8 border border-white/5 relative overflow-y-auto custom-scrollbar" style={{ maxHeight: '800px' }}>

                    <div className="relative border-x border-white/20 w-[120px] sm:w-[150px] bg-[#1a1a1a] shadow-2xl rounded-sm" style={{ height: `${containerHeight}px` }}>
                        {/* Depth axis markers */}
                        <div className="absolute -left-10 top-0 bottom-0 w-10 border-r border-white/10 flex flex-col">
                            {Array.from({ length: Math.ceil(maxDepth) + 1 }).map((_, i) => (
                                <div key={i} className="absolute right-0 text-[10px] text-zinc-500 pr-2 -translate-y-1/2" style={{ top: `${i * scale}px` }}>
                                    {i}m
                                </div>
                            ))}
                        </div>

                        {/* Geology layers */}
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
                                    <span className="text-white/90 font-bold tracking-wider text-[10px] sm:text-xs pointer-events-none drop-shadow-md">
                                        {layer.legend}
                                    </span>
                                </div>
                            );
                        })}

                        {/* Casings Overlay */}
                        {selectedHole.casings?.map((casing, idx) => (
                            <div
                                key={`casing-${idx}`}
                                className="absolute left-1/2 -translate-x-1/2 border-x-2 border-zinc-400/50 z-20 pointer-events-none"
                                style={{
                                    top: 0,
                                    height: `${casing.depth * scale}px`,
                                    width: `${Math.min(100, (casing.diameter / 200) * 100)}%`
                                }}
                            />
                        ))}

                        {/* Samples Overlay */}
                        {selectedHole.samples?.map((samp, idx) => (
                            <div
                                key={`samp-${idx}`}
                                className="absolute -right-2 w-4 h-4 rounded-full bg-white border-2 border-blue-600 shadow-md flex items-center justify-center group/samp cursor-help z-30"
                                style={{ top: `${samp.top * scale}px`, transform: 'translateY(-50%)' }}
                            >
                                <div className="absolute left-6 bg-blue-900 border border-blue-400 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover/samp:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none">
                                    {samp.type} ({samp.ref})
                                </div>
                            </div>
                        ))}

                        {/* Water Strikes Overlay */}
                        {selectedHole.water?.map((strike, idx) => (
                            <div
                                key={`water-${idx}`}
                                className="absolute -left-6 text-blue-400 z-30 group/water cursor-help drop-shadow-[0_0_5px_rgba(59,130,246,0.5)]"
                                style={{ top: `${strike.depth * scale}px`, transform: 'translateY(-50%)' }}
                            >
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.5c-3.5 0-6.5-3-6.5-6.5 0-2 1-4.5 3-7.5l3.5-5.5 3.5 5.5c2 3 3 5.5 3 7.5 0 3.5-3 6.5-6.5 6.5z" /></svg>
                                <div className="absolute right-6 bg-blue-600 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover/water:opacity-100 transition-opacity whitespace-nowrap z-50 pointer-events-none border border-blue-300">
                                    Strike: {strike.depth}m {strike.time && `at ${strike.time}`}
                                </div>
                            </div>
                        ))}

                        {/* SPT Overlay */}
                        {selectedHole.spts?.map((spt, idx) => (
                            <div
                                key={`spt-${idx}`}
                                className="absolute -right-12 text-blue-400 font-bold text-[10px] flex items-center group/spt cursor-help z-30"
                                style={{ top: `${spt.top * scale}px`, transform: 'translateY(-50%)' }}
                            >
                                <div className="w-2 h-[1px] bg-blue-500/50 mr-1" />
                                N={spt.n_value}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Legend and Details */}
                <div className={`col-span-1 ${hasExtraData ? 'md:col-span-3' : 'md:col-span-2'} flex flex-col space-y-4`}>
                    <h3 className="text-2xl font-bold text-white mb-2">Detailed Log: <span className="text-blue-400">{selectedHole.id}</span></h3>

                    <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3" style={{ maxHeight: '700px' }}>
                        {/* Summary Stats */}
                        <div className="flex flex-wrap gap-4 mb-6">
                            <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex-1 min-w-[150px]">
                                <div className="text-zinc-500 text-xs uppercase tracking-wider mb-1">Depth</div>
                                <div className="text-xl font-bold text-white">{selectedHole.max_depth}m</div>
                            </div>
                            {selectedHole.samples && selectedHole.samples.length > 0 && (
                                <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex-1 min-w-[150px]">
                                    <div className="text-zinc-500 text-xs uppercase tracking-wider mb-1">Samples</div>
                                    <div className="text-xl font-bold text-blue-400">{selectedHole.samples.length}</div>
                                </div>
                            )}
                            {selectedHole.water && selectedHole.water.length > 0 && (
                                <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex-1 min-w-[150px]">
                                    <div className="text-zinc-500 text-xs uppercase tracking-wider mb-1">Water Strikes</div>
                                    <div className="text-xl font-bold text-blue-300">{selectedHole.water.length}</div>
                                </div>
                            )}
                        </div>

                        {/* Construction & Water Section */}
                        {((selectedHole.water && selectedHole.water.length > 0) || (selectedHole.casings && selectedHole.casings.length > 0)) && (
                            <>
                                <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-widest pt-4 mb-2">Construction & Water</h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                                    {selectedHole.water?.map((strike, idx) => (
                                        <div key={`wbtn-${idx}`} className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-3 flex gap-3 items-center">
                                            <div className="text-blue-400 shrink-0">
                                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 21.5c-3.5 0-6.5-3-6.5-6.5 0-2 1-4.5 3-7.5l3.5-5.5 3.5 5.5c2 3 3 5.5 3 7.5 0 3.5-3 6.5-6.5 6.5z" /></svg>
                                            </div>
                                            <div>
                                                <div className="text-xs text-blue-300 font-bold">Water Strike at {strike.depth.toFixed(2)}m</div>
                                                <div className="text-[10px] text-zinc-400">{strike.time} {strike.remarks}</div>
                                            </div>
                                        </div>
                                    ))}
                                    {selectedHole.casings?.map((casing, idx) => (
                                        <div key={`cbtn-${idx}`} className="bg-zinc-500/5 border border-zinc-500/20 rounded-xl p-3 flex gap-3 items-center">
                                            <div className="text-zinc-400 shrink-0">
                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                                            </div>
                                            <div>
                                                <div className="text-xs text-zinc-300 font-bold">Casing to {casing.depth.toFixed(2)}m</div>
                                                <div className="text-[10px] text-zinc-400">Dia: {casing.diameter}mm</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        )}

                        {/* Geology List */}
                        <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-widest pt-4 mb-2">Lithology</h4>
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

                        {/* Samples List */}
                        {selectedHole.samples && selectedHole.samples.length > 0 && (
                            <>
                                <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-widest pt-6 mb-2">Samples</h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {selectedHole.samples.map((samp, idx) => (
                                        <div key={idx} className="bg-white/5 border border-blue-500/10 rounded-xl p-3 flex justify-between items-center group hover:bg-blue-500/5 transition-colors">
                                            <div>
                                                <div className="text-[10px] text-blue-400 font-bold uppercase">{samp.type}</div>
                                                <div className="text-sm font-medium text-white">{samp.id || samp.ref || 'Unnamed'}</div>
                                            </div>
                                            <div className="text-xs text-zinc-500">{samp.top.toFixed(2)}m</div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
