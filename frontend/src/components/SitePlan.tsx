import React, { useMemo } from 'react';
import { Maximize2, Map as MapIcon } from 'lucide-react';

interface SitePlanProps {
    holes: Array<{
        id: string;
        east: number | null;
        north: number | null;
    }>;
    selectedHoleId: string;
    onSelectHole: (id: string) => void;
}

export function SitePlan({ holes, selectedHoleId, onSelectHole }: SitePlanProps) {
    // Filter holes that have coordinates
    const validHoles = useMemo(() => holes.filter(h => h.east !== null && h.north !== null), [holes]);

    if (validHoles.length === 0) {
        return (
            <div className="w-full aspect-square md:aspect-video bg-white/5 border border-white/10 rounded-3xl flex flex-col items-center justify-center text-zinc-500 p-8 text-center">
                <MapIcon size={48} className="mb-4 opacity-20" />
                <h4 className="text-lg font-bold text-white/50 mb-2">No Spatial Data</h4>
                <p className="text-sm max-w-xs">This AGS file does not contain Easting/Northing coordinates (LOCA_NATE/NATN) for any boreholes.</p>
            </div>
        );
    }

    // Calculate Bounds
    const bounds = useMemo(() => {
        let minE = Infinity, maxE = -Infinity, minN = Infinity, maxN = -Infinity;
        validHoles.forEach(h => {
            if (h.east! < minE) minE = h.east!;
            if (h.east! > maxE) maxE = h.east!;
            if (h.north! < minN) minN = h.north!;
            if (h.north! > maxN) maxN = h.north!;
        });

        // Add 10% padding
        const paddingE = (maxE - minE) * 0.1 || 10;
        const paddingN = (maxN - minN) * 0.1 || 10;

        return {
            minE: minE - paddingE,
            maxE: maxE + paddingE,
            minN: minN - paddingN,
            maxN: maxN + paddingN,
            width: (maxE - minE) + 2 * paddingE,
            height: (maxN - minN) + 2 * paddingN
        };
    }, [validHoles]);

    return (
        <div className="w-full bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md relative overflow-hidden group">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                        <MapIcon size={16} className="text-blue-400" />
                    </div>
                    <h3 className="text-lg font-bold text-white tracking-tight">Interactive Site Plan</h3>
                </div>
                <div className="flex gap-2">
                    <div className="px-3 py-1 bg-white/5 rounded-full text-[10px] text-zinc-400 font-mono border border-white/10">
                        {validHoles.length} Points Plotted
                    </div>
                </div>
            </div>

            <div className="relative aspect-video bg-black/40 rounded-2xl border border-white/5 overflow-hidden cursor-crosshair">
                {/* Grid Lines */}
                <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle, #3b82f6 1px, transparent 1px)', backgroundSize: '30px 30px' }} />

                <svg
                    viewBox={`${bounds.minE} ${-bounds.maxN} ${bounds.width} ${bounds.height}`}
                    className="w-full h-full p-8"
                    preserveAspectRatio="xMidYMid meet"
                >
                    {validHoles.map((hole) => (
                        <g
                            key={hole.id}
                            className={`cursor-pointer transition-all duration-300 hover:z-50 ${selectedHoleId === hole.id ? 'scale-150' : ''}`}
                            onClick={() => onSelectHole(hole.id)}
                        >
                            {/* Pulse effect for selected */}
                            {selectedHoleId === hole.id && (
                                <circle
                                    cx={hole.east!}
                                    cy={-hole.north!}
                                    r={bounds.width * 0.02}
                                    className="fill-blue-500/30 animate-ping"
                                />
                            )}

                            {/* Main Point */}
                            <circle
                                cx={hole.east!}
                                cy={-hole.north!}
                                r={bounds.width * 0.012}
                                className={`${selectedHoleId === hole.id ? 'fill-blue-400 stroke-blue-200' : 'fill-zinc-600 stroke-white/20'} stroke-2 transition-colors`}
                            />

                            {/* Tooltip background on hover */}
                            <text
                                x={hole.east!}
                                y={-hole.north! - bounds.height * 0.03}
                                className={`text-[12px] font-bold ${selectedHoleId === hole.id ? 'fill-white' : 'fill-zinc-500'} pointer-events-none transition-colors text-center`}
                                textAnchor="middle"
                                style={{ fontSize: `${bounds.width * 0.03}px` }}
                            >
                                {hole.id}
                            </text>
                        </g>
                    ))}
                </svg>

                {/* Relative Scale Indicator */}
                <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-md border border-white/10 rounded-lg px-3 py-1.5 text-[10px] font-mono text-zinc-400">
                    Relative Coordinates (m)
                </div>

                <button className="absolute bottom-4 right-4 p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-lg shadow-blue-500/20 transition-all opacity-0 group-hover:opacity-100">
                    <Maximize2 size={16} />
                </button>
            </div>
        </div>
    );
}
