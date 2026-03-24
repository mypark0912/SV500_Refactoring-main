import { useState } from "react";

// ══════════════════════════════════════════════
// PRIMITIVES
// ══════════════════════════════════════════════

const Card = ({ title, badge, children, className = "" }) => (
  <div className={`bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden ${className}`}>
    <div className="flex items-center justify-between px-5 pt-4 pb-1">
      <h3 className="text-sm font-bold text-slate-700">{title}</h3>
      {badge && <span className="text-xs text-slate-400">{badge}</span>}
    </div>
    <div className="px-5 pb-5">{children}</div>
  </div>
);

// ─── Big Number with status dot ───
const BigNum = ({ value, unit, status, label }) => {
  const dotColor = status === "good" ? "#22c55e" : status === "warn" ? "#f59e0b" : status === "danger" ? "#ef4444" : "#94a3b8";
  return (
    <div className="flex items-center gap-3">
      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: dotColor }} />
      <div>
        {label && <span className="text-xs text-slate-400 block">{label}</span>}
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-extrabold text-slate-800 tabular-nums">{value}</span>
          <span className="text-sm font-medium text-slate-400">{unit}</span>
        </div>
      </div>
    </div>
  );
};

// ─── Phase Horizontal Bar ───
const PhaseBar = ({ phase, value, min, max, unit, color, avg }) => {
  const range = max - min;
  const pct = Math.min(((value - min) / range) * 100, 100);
  const avgPct = avg ? ((avg - min) / range) * 100 : null;
  return (
    <div className="flex items-center gap-2.5 py-1">
      <span className="text-xs font-bold w-5 text-slate-400">{phase}</span>
      <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden relative">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color, opacity: 0.75 }} />
        {/* avg marker */}
        {avgPct && (
          <div className="absolute top-0 h-full w-0.5 bg-slate-400 opacity-40" style={{ left: `${avgPct}%` }} />
        )}
      </div>
      <span className="text-xs font-semibold text-slate-600 w-20 text-right tabular-nums">{value} <span className="text-slate-400">{unit}</span></span>
    </div>
  );
};

// ─── Semi-circle Gauge (역률 전용) ───
const SemiGauge = ({ value, size = 130 }) => {
  const clamp = Math.min(Math.max(value, 0), 100);
  const color = clamp >= 95 ? "#22c55e" : clamp >= 85 ? "#f59e0b" : "#ef4444";
  const r = size * 0.4;
  const circ = Math.PI * r; // half circle
  const offset = circ * (1 - clamp / 100);
  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size * 0.55} viewBox={`0 0 ${size} ${size * 0.55}`}>
        {/* background arc */}
        <path d={`M ${size*0.1} ${size*0.5} A ${r} ${r} 0 0 1 ${size*0.9} ${size*0.5}`}
          fill="none" stroke="#f1f5f9" strokeWidth={10} strokeLinecap="round" />
        {/* value arc */}
        <path d={`M ${size*0.1} ${size*0.5} A ${r} ${r} 0 0 1 ${size*0.9} ${size*0.5}`}
          fill="none" stroke={color} strokeWidth={10} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          className="transition-all duration-700" />
        {/* center text */}
        <text x={size/2} y={size*0.48} textAnchor="middle" className="text-2xl font-bold" style={{ fontSize: 22, fill: color, fontWeight: 800 }}>
          {value}%
        </text>
      </svg>
    </div>
  );
};

// ─── THD Vertical Bars ───
const THDBarChart = ({ items }) => {
  const maxVal = Math.max(...items.map(d => d.value), 10);
  return (
    <div className="flex items-end justify-center gap-4 h-24">
      {items.map((d) => {
        const h = Math.max((d.value / maxVal) * 80, 6);
        return (
          <div key={d.label} className="flex flex-col items-center gap-1">
            <span className="text-xs font-bold text-slate-600">{d.value}%</span>
            <div className="w-8 rounded-t-lg transition-all duration-500" style={{ height: h, backgroundColor: d.color }} />
            <span className="text-xs text-slate-400 whitespace-nowrap" style={{ fontSize: 10 }}>{d.label}</span>
          </div>
        );
      })}
    </div>
  );
};

// ─── Progress Bar (불평형률 전용) ───
const UnbalanceBar = ({ label, value, threshold = 3, color }) => {
  const pct = Math.min((value / threshold) * 100, 100);
  const statusColor = value < 1 ? "#22c55e" : value < 2 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-500 w-6">{label}</span>
      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden relative">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
        {/* threshold line */}
        <div className="absolute top-0 h-full w-0.5 bg-red-300 opacity-50" style={{ left: `${(threshold / 5) * 100}%` }} />
      </div>
      <div className="flex items-center gap-1.5 w-16 justify-end">
        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor }} />
        <span className="text-xs font-semibold text-slate-600 tabular-nums">{value}%</span>
      </div>
    </div>
  );
};

// ─── Area Sparkline ───
const AreaChart = ({ data, width, height, color = "#8b5cf6", id = "sp" }) => {
  if (!data || data.length < 2) return <div style={{ width, height }} className="bg-slate-50 rounded-lg" />;
  const pad = 2;
  const mx = Math.max(...data) * 1.12 || 1;
  const mn = Math.min(...data) * 0.88;
  const rng = mx - mn || 1;
  const pts = data.map((v, i) => [
    pad + (i / (data.length - 1)) * (width - pad * 2),
    pad + (height - pad * 2) - ((v - mn) / rng) * (height - pad * 2)
  ]);
  const line = pts.map(p => p.join(",")).join(" ");
  const area = `${pad},${height - pad} ${line} ${width - pad},${height - pad}`;
  const last = pts[pts.length - 1];
  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`g-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon points={area} fill={`url(#g-${id})`} />
      <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={last[0]} cy={last[1]} r="3.5" fill="white" stroke={color} strokeWidth="2" />
    </svg>
  );
};

// ─── Energy KPI ───
const EnergyKPI = ({ label, value, unit, delta, deltaLabel }) => {
  const isUp = delta > 0;
  const isZero = delta === 0;
  return (
    <div className="text-center flex-1 min-w-0">
      <span className="text-xs text-slate-400">{label}</span>
      <div className="flex items-baseline justify-center gap-0.5 mt-1">
        <span className="text-xl font-bold text-slate-800 tabular-nums">{value}</span>
        <span className="text-xs text-slate-400">{unit}</span>
      </div>
      <span className={`text-xs font-medium ${isZero ? "text-slate-300" : isUp ? "text-rose-400" : "text-emerald-500"}`}>
        {isZero ? "-" : `${isUp ? "+" : ""}${delta}%`} <span className="text-slate-300 font-normal">{deltaLabel}</span>
      </span>
    </div>
  );
};


// ══════════════════════════════════════════════
// MAIN DASHBOARD
// ══════════════════════════════════════════════
export default function MeasuringDashboard() {
  const hourlyData = [0.008, 0.01, 0.012, 0.015, 0.013, 0.018, 0.022, 0.025, 0.027, 0.029, 0.031, 0.028, 0.032, 0.03, 0.035, 0.033, 0.031];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 p-6" style={{ fontFamily: "'Inter', 'Pretendard', sans-serif" }}>

      {/* ═══════════ ROW 1 : 전압 / 전류 / 주파수 ═══════════ */}
      <div className="grid grid-cols-12 gap-4 mb-4">

        {/* ① 평균 전압 + 상별 전압 */}
        <Card title="전압" badge="채널 1" className="col-span-4">
          <BigNum value="221.4" unit="V" status="good" />
          <div className="mt-4 space-y-1.5">
            <PhaseBar phase="L1" value={221.60} min={210} max={240} unit="V" color="#8b5cf6" avg={221.4} />
            <PhaseBar phase="L2" value={221.75} min={210} max={240} unit="V" color="#a78bfa" avg={221.4} />
            <PhaseBar phase="L3" value={220.89} min={210} max={240} unit="V" color="#c4b5fd" avg={221.4} />
          </div>
          <div className="flex items-center gap-1.5 mt-3 text-xs text-slate-300">
            <div className="w-3 h-0.5 bg-slate-300 rounded" />
            <span>평균</span>
          </div>
        </Card>

        {/* ② 평균 전류 + 상별 전류 */}
        <Card title="전류" badge="채널 1" className="col-span-4">
          <BigNum value="0.64" unit="A" status="good" />
          <div className="mt-4 space-y-1.5">
            <PhaseBar phase="L1" value={0.65} min={0} max={5} unit="A" color="#3b82f6" avg={0.64} />
            <PhaseBar phase="L2" value={0.63} min={0} max={5} unit="A" color="#60a5fa" avg={0.64} />
            <PhaseBar phase="L3" value={0.63} min={0} max={5} unit="A" color="#93c5fd" avg={0.64} />
          </div>
          <div className="flex items-center gap-1.5 mt-3 text-xs text-slate-300">
            <div className="w-3 h-0.5 bg-slate-300 rounded" />
            <span>평균</span>
          </div>
        </Card>

        {/* ③ 주파수 — 단독 KPI + 미니 트렌드 */}
        <Card title="주파수" badge="채널 1" className="col-span-4">
          <BigNum value="60.00" unit="Hz" status="good" />
          <div className="mt-4 bg-slate-50 rounded-xl p-3">
            <span className="text-xs text-slate-400 block mb-2">최근 추이</span>
            <AreaChart
              data={[59.98, 60.01, 60.0, 59.99, 60.02, 60.0, 59.98, 60.01, 60.0, 60.01, 59.99, 60.0]}
              width={260} height={60} color="#22c55e" id="freq"
            />
            <div className="flex justify-between mt-1 text-xs text-slate-300">
              <span>-60min</span><span>now</span>
            </div>
          </div>
        </Card>
      </div>

      {/* ═══════════ ROW 2 : 역률·전력 / 불평형률·THD ═══════════ */}
      <div className="grid grid-cols-12 gap-4 mb-4">

        {/* ④ 역률 + 총 유효전력 */}
        <Card title="역률 · 유효전력" badge="채널 1" className="col-span-5">
          <div className="grid grid-cols-2 gap-4">
            {/* 역률 게이지 */}
            <div className="flex flex-col items-center bg-slate-50 rounded-xl py-4">
              <span className="text-xs text-slate-400 mb-1">역률 (PF)</span>
              <SemiGauge value={13.85} size={140} />
              <span className="text-xs text-red-400 font-medium mt-1">기준 미달</span>
            </div>
            {/* 유효전력 */}
            <div className="flex flex-col justify-center gap-4">
              <div className="bg-slate-50 rounded-xl px-4 py-3">
                <span className="text-xs text-slate-400">유효전력 (P)</span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold text-slate-800">0.14</span>
                  <span className="text-sm text-slate-400">kW</span>
                </div>
              </div>
              <div className="bg-slate-50 rounded-xl px-4 py-3">
                <span className="text-xs text-slate-400">무효전력 (Q)</span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold text-slate-800">0.09</span>
                  <span className="text-sm text-slate-400">kVar</span>
                </div>
              </div>
              <div className="bg-slate-50 rounded-xl px-4 py-3">
                <span className="text-xs text-slate-400">피상전력 (S)</span>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold text-slate-800">0.17</span>
                  <span className="text-sm text-slate-400">kVA</span>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* ⑤ 불평형률 + 고조파 왜곡률 */}
        <Card title="불평형률 · 고조파 왜곡률" badge="채널 1" className="col-span-7">
          <div className="grid grid-cols-2 gap-5">
            {/* 불평형률 */}
            <div>
              <span className="text-xs font-medium text-slate-500 mb-3 block">전압/전류 불평형률</span>
              <div className="space-y-3">
                <UnbalanceBar label="전압" value={0.2} threshold={3} color="#8b5cf6" />
                <UnbalanceBar label="전류" value={1.8} threshold={3} color="#38bdf8" />
              </div>
              <div className="flex items-center gap-1.5 mt-4 text-xs text-slate-300">
                <div className="w-0.5 h-2.5 bg-red-300 rounded opacity-60" />
                <span>허용 기준 (3%)</span>
              </div>
            </div>
            {/* THD */}
            <div>
              <span className="text-xs font-medium text-slate-500 mb-3 block">고조파 왜곡률</span>
              <THDBarChart items={[
                { label: "THD-U", value: 3.6, color: "#f87171" },
                { label: "THD-I", value: 6.8, color: "#60a5fa" },
                { label: "TDD-I", value: 32.1, color: "#2dd4bf" },
              ]} />
            </div>
          </div>
        </Card>
      </div>

      {/* ═══════════ ROW 3 : 전력량 현황 ═══════════ */}
      <Card title="전력량 현황" badge="채널 1" className="w-full">
        <div className="grid grid-cols-12 gap-5">
          {/* KPI row */}
          <div className="col-span-3 flex flex-col gap-2 justify-center">
            <div className="flex gap-2">
              <EnergyKPI label="오늘" value="0.15" unit="kWh" delta={36} deltaLabel="전일" />
              <EnergyKPI label="금주" value="0.27" unit="kWh" delta={-66} deltaLabel="전주" />
            </div>
            <div className="flex gap-2">
              <EnergyKPI label="금월" value="1.28" unit="kWh" delta={0} deltaLabel="전월" />
              <EnergyKPI label="연간" value="1.28" unit="kWh" delta={0} deltaLabel="전년" />
            </div>
          </div>
          {/* Chart area */}
          <div className="col-span-9 bg-slate-50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-500">금일 시간대별 사용량 (kWh)</span>
              <span className="text-xs text-slate-300">최근 갱신 14:00</span>
            </div>
            <AreaChart data={hourlyData} width={680} height={110} color="#8b5cf6" id="energy" />
            <div className="flex justify-between mt-2 text-xs text-slate-300">
              <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>24:00</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
