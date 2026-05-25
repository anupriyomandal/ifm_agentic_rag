"use client";

import { ArrowRight } from "lucide-react";

const SUGGESTIONS = [
  { label: "CPKM by zone",         query: "What is the average CPKM by zone?" },
  { label: "Best mileage tyre",    query: "Which tyre size gives the best average projected mileage?" },
  { label: "Wear bracket split",   query: "What percentage of tyres are in the 80-100% wornout bracket?" },
  { label: "CEAT vs MRF — 11R20", query: "Compare CPKM of CEAT vs MRF vs Apollo for 11.00R20 tyres" },
  { label: "Radial vs Crossply",   query: "What is the split of radial vs crossply tyres by zone?" },
  { label: "West Bengal CPKM",     query: "What is the average CPKM of all tyres in West Bengal?" },
];

interface Props {
  onSelect: (query: string) => void;
}

export function SuggestedQueries({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-12 select-none">
      {/* Hero */}
      <div className="text-center mb-10">
        <div
          className="text-ceat-dark mb-2 leading-none tracking-wide"
          style={{ fontFamily: "var(--font-barlow)", fontSize: "2.2rem", fontWeight: 700 }}
        >
          IFM TYRE ADVISOR
        </div>
        <p className="text-slate-400 text-sm max-w-sm">
          Ask anything about your fleet's tyre performance, CPKM, mileage, and wear data.
        </p>
      </div>

      {/* Suggested queries grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.query}
            onClick={() => onSelect(s.query)}
            className="group flex items-center gap-3 text-left px-4 py-3.5 rounded-xl
              bg-white border border-slate-200 hover:border-ceat-blue/40
              hover:shadow-md shadow-sm transition-all duration-200"
          >
            <div className="flex-1">
              <div className="text-xs font-semibold text-ceat-blue uppercase tracking-wider mb-0.5">
                {s.label}
              </div>
              <div className="text-slate-500 text-xs leading-snug">{s.query}</div>
            </div>
            <ArrowRight
              size={14}
              className="text-slate-300 group-hover:text-ceat-orange flex-shrink-0
                group-hover:translate-x-0.5 transition-all duration-200"
            />
          </button>
        ))}
      </div>
    </div>
  );
}
