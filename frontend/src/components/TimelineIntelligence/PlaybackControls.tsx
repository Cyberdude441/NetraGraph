import React from "react";
import {
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  FastForward,
  Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PlaybackControlsProps {
  isPlaying: boolean;
  onTogglePlay: () => void;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  onReset: () => void;
  currentDateLabel: string;
  progressPercentage: number;
  onScrub: (pct: number) => void;
}

export function PlaybackControls({
  isPlaying,
  onTogglePlay,
  playbackSpeed,
  onSpeedChange,
  onReset,
  currentDateLabel,
  progressPercentage,
  onScrub,
}: PlaybackControlsProps) {
  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white p-4 select-none font-sans space-y-3 shadow-xl">
      {/* Top Scrubber Line */}
      <div className="flex items-center justify-between font-mono text-[10px] text-slate-400">
        <span className="flex items-center gap-1.5 text-emerald-400 font-bold uppercase">
          <Clock className="size-3" />
          Timeline Chronological Replay
        </span>
        <span className="text-slate-800 font-bold">{currentDateLabel}</span>
      </div>

      {/* Slider Scrubber Bar */}
      <div className="relative flex items-center">
        <input
          type="range"
          min="0"
          max="100"
          value={progressPercentage}
          onChange={(e) => onScrub(Number(e.target.value))}
          className="w-full accent-emerald-500 cursor-pointer h-2 bg-slate-100 rounded-lg appearance-none"
        />
      </div>

      {/* Control Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <button
            onClick={onTogglePlay}
            className={cn(
              "flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-mono font-bold transition-all cursor-pointer",
              isPlaying
                ? "bg-amber-600 hover:bg-amber-500 text-white shadow-md"
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-md"
            )}
          >
            {isPlaying ? <Pause className="size-3.5" /> : <Play className="size-3.5" />}
            <span>{isPlaying ? "Pause Replay" : "Play Timeline"}</span>
          </button>

          <button
            onClick={onReset}
            className="p-1.5 rounded border border-[#E2E8F0] bg-[#F8FAFC] text-slate-400 hover:text-slate-800 cursor-pointer"
            title="Reset to Origin"
          >
            <RotateCcw className="size-3.5" />
          </button>
        </div>

        {/* Speed Toggles */}
        <div className="flex items-center gap-1 font-mono text-[10px]">
          <span className="text-slate-500 mr-1">Speed:</span>
          {[1, 2, 5].map((spd) => {
            const active = playbackSpeed === spd;
            return (
              <button
                key={spd}
                onClick={() => onSpeedChange(spd)}
                className={cn(
                  "rounded px-2 py-0.5 font-bold transition-all cursor-pointer",
                  active
                    ? "bg-emerald-500/30 text-emerald-300 border border-emerald-500/50"
                    : "border border-[#E2E8F0] bg-[#F8FAFC] text-slate-400 hover:text-slate-800"
                )}
              >
                {spd}x
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
