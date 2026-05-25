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

    </div>
  );
}
