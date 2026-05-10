import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Chart from 'react-apexcharts';
import { Play, Pause, Activity, TrendingUp, Layers, Box, Database, Clock, Calendar, Truck } from 'lucide-react';

const ChartSummaryMetrics = ({ actual, plan, avgRate, unit, themeColor }) => {
  const gap = actual - plan;
  const perc = plan > 0 ? (gap / plan) * 100 : 0;
  const isOver = gap >= 0;
  
  const formatNum = (val) => {
    if (typeof val !== 'number') return val;
    return val.toLocaleString('id-ID', { maximumFractionDigits: 0 });
  };
  
  // Determine color based on gap and theme
  const gapColor = isOver ? 'text-emerald-500' : 'text-red-500';
  const themeTextClass = themeColor === 'blue' ? 'text-blue-600' : 'text-emerald-600';
  
  return (
    <div className="flex items-center gap-6 md:gap-8 lg:gap-12 ml-auto shrink-0 mr-4">
      <div className="flex flex-col items-center">
        <span className="text-[9px] font-black tracking-widest text-slate-500 uppercase">Actual</span>
        <span className={`text-base md:text-lg font-black tracking-tight ${themeTextClass}`}>{formatNum(actual)}</span>
        <span className="text-[8px] md:text-[9px] font-semibold text-slate-400 mt-0.5">{unit} Hari Ini</span>
      </div>
      
      <div className="flex flex-col items-center">
        <span className="text-[9px] font-black tracking-widest text-slate-500 uppercase">Plan</span>
        <span className="text-base md:text-lg font-black tracking-tight text-slate-800">{formatNum(plan)}</span>
        <span className="text-[8px] md:text-[9px] font-semibold text-slate-400 mt-0.5">{unit} Target</span>
      </div>
      
      <div className="flex flex-col items-center">
        <span className="text-[9px] font-black tracking-widest text-slate-500 uppercase">Gap</span>
        <span className={`text-base md:text-lg font-black tracking-tight ${gapColor}`}>
          {gap > 0 ? '+' : ''}{formatNum(gap)}
        </span>
        <span className="text-[8px] md:text-[9px] font-semibold text-slate-400 mt-0.5">
          {isOver ? `+${perc.toFixed(1)}% over` : `${perc.toFixed(1)}% miss`}
        </span>
      </div>

      <div className="flex flex-col items-center">
        <span className="text-[9px] font-black tracking-widest text-slate-500 uppercase">Avg Rate</span>
        <span className="text-base md:text-lg font-black tracking-tight text-slate-800">{formatNum(avgRate)}</span>
        <span className="text-[8px] md:text-[9px] font-semibold text-slate-400 mt-0.5">{unit} / hr</span>
      </div>
    </div>
  );
};

const KpiCard = ({ title, actualValue, targetValue, unit, delayClass, isRatio = false, customSubtitle = null }) => {
  // If actualValue and targetValue are provided, we show progress
  const hasTarget = typeof targetValue === 'number' && targetValue > 0;

  // Calculate percentage
  let percentage = 0;
  if (hasTarget) {
    percentage = (actualValue / targetValue) * 100;
  }

  // Clamp progress bar to 100%
  const progressWidth = Math.min(percentage, 100);

  // Determine color based on percentage
  let colorClass = "bg-blue-500";
  let textClass = "text-blue-600";
  let bgClass = "bg-blue-50";

  if (hasTarget) {
    if (percentage >= 100) {
      colorClass = "bg-emerald-500";
      textClass = "text-emerald-600";
      bgClass = "bg-emerald-100";
    } else if (percentage >= 80) {
      colorClass = "bg-amber-500";
      textClass = "text-amber-600";
      bgClass = "bg-amber-100";
    } else {
      colorClass = "bg-red-500";
      textClass = "text-red-600";
      bgClass = "bg-red-100";
    }
  }

  const formatNumber = (num) => {
    if (typeof num !== 'number') return num;
    if (isRatio) {
      return num.toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    return num.toLocaleString('id-ID', { maximumFractionDigits: 0 });
  };

  return (
    <div className={`relative bg-white/80 backdrop-blur-md border border-slate-200/80 p-5 rounded-xl flex flex-col justify-between shadow-sm hover:shadow-md transition-all duration-300 animate-fade-in-up overflow-hidden ${delayClass}`}>
      {/* Decorative Background Watermark for No-Target Cards */}
      {!hasTarget && (
        <div className="absolute -right-4 -bottom-4 text-slate-200 opacity-40 pointer-events-none transform -rotate-12 z-0">
          {title.includes('Stock') ? <Database size={120} strokeWidth={1} /> : <Activity size={120} strokeWidth={1} />}
        </div>
      )}

      <div className="flex flex-col h-full relative z-10">
        {/* Title Row with Top Right Icon or Percentage */}
        <div className="flex justify-between items-start mb-2 gap-2">
          <div className="flex items-baseline gap-1.5 flex-wrap">
            <p className="text-slate-800 text-[1.05rem] xl:text-[1.15rem] leading-tight font-black tracking-tight">{title}</p>
            {unit && <span className="text-[10px] font-bold text-slate-400 uppercase">{unit}</span>}
          </div>
          {hasTarget ? (
            <div className={`flex items-center px-2 py-0.5 rounded-lg shadow-sm border border-white/50 shrink-0 ${bgClass} ${textClass} text-sm md:text-[15px] font-black`}>
              <span>{percentage.toFixed(1)}%</span>
            </div>
          ) : (
            <div className="text-slate-300 shrink-0">
              {title.includes('Ratio') ? <TrendingUp size={20} strokeWidth={2.5} /> : <Layers size={20} strokeWidth={2.5} />}
            </div>
          )}
        </div>

        {/* Value */}
        <div className="mb-3">
          <h2 className="text-[clamp(2.2rem,3.2vw,4rem)] leading-[1.1] font-black tracking-tighter text-slate-900 font-outfit break-words">
            {formatNumber(actualValue)}
          </h2>
        </div>

        {/* Footer */}
        <div className="mt-auto">
          {hasTarget ? (
            <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden mb-3 shadow-inner border border-slate-100">
              <div
                className={`h-full ${colorClass} rounded-full transition-all duration-1000 ease-out`}
                style={{ width: `${progressWidth}%` }}
              />
            </div>
          ) : (
            /* Subtle striped placeholder bar */
            <div className="h-3 w-full bg-slate-50 rounded-full overflow-hidden mb-3 relative border border-slate-100">
              <div className="absolute inset-0 bg-[repeating-linear-gradient(45deg,transparent,transparent_4px,rgba(0,0,0,0.03)_4px,rgba(0,0,0,0.03)_8px)]"></div>
            </div>
          )}

          <div className="flex justify-between items-center text-sm font-bold">
            {hasTarget ? (
              <>
                <span className={textClass}>In Progress</span>
                <span className="text-slate-500">Target: <span className={`${textClass} font-black text-base`}>{formatNumber(targetValue)}</span></span>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2 text-emerald-500">
                  <span className="relative flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                  </span>
                  <span className="uppercase tracking-wider font-black">Live</span>
                </div>
                <span className="text-slate-500 bg-slate-100/50 px-2.5 py-1 rounded-md border border-slate-200/50 text-xs">
                  {customSubtitle || "UPDATED"}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const PITS = ["North JO IC", "North JO GAM", "South JO IC", "South JO GAM"];

function App() {
  const [pit, setPit] = useState(PITS[0]);
  const [kpi, setKpi] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [autoPlay, setAutoPlay] = useState(true);
  const [isFetching, setIsFetching] = useState(false);

  const pitIndexRef = useRef(0);

  // Auto-rotate logic (Slider)
  useEffect(() => {
    if (!autoPlay) return;
    const rotateTimer = setInterval(() => {
      pitIndexRef.current = (pitIndexRef.current + 1) % PITS.length;
      setPit(PITS[pitIndexRef.current]);
    }, 20000); // 20 seconds for comfortable reading
    return () => clearInterval(rotateTimer);
  }, [autoPlay]);

  // Sync index when selected manually
  useEffect(() => {
    const idx = PITS.indexOf(pit);
    if (idx !== -1) pitIndexRef.current = idx;
  }, [pit]);

  // Fetch Data
  useEffect(() => {
    setIsFetching(true);
    
    Promise.all([
      axios.get(`/api/kpi?pit=${pit}`),
      axios.get(`/api/charts/hourly?pit=${pit}`)
    ]).then(([kpiRes, chartRes]) => {
      setKpi(kpiRes.data);
      setChartData(chartRes.data);
    }).catch(err => console.error("Error fetching data:", err))
      .finally(() => {
        setIsFetching(false);
      });
  }, [pit]);

  const baseChartOptions = {
    chart: {
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif',
      background: 'transparent',
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 1000,
        animateGradually: { enabled: true, delay: 0 },
        dynamicAnimation: { enabled: true, speed: 300 }
      }
    },
    theme: { mode: 'light' },
    dataLabels: { enabled: false },
    stroke: { curve: 'smooth' },
    xaxis: {
      type: 'category',
      categories: chartData ? chartData.data.map(d => d.hour) : [],
      labels: { style: { colors: '#1e293b', fontWeight: 800, fontSize: '16px' }, offsetY: 0 },
      axisBorder: { show: true, color: '#cbd5e1', height: 2 },
      axisTicks: { show: false }
    },
    grid: {
      borderColor: 'rgba(0,0,0,0.06)',
      strokeDashArray: 4,
      xaxis: { lines: { show: true } },
      yaxis: { lines: { show: true } },
      padding: { top: 15, bottom: 0, left: 10, right: 20 }
    },
    legend: { show: false }
  };

  const getObOptions = () => {
    if (!chartData || !kpi) return {};
    const planOb = kpi.kpi.plans.plan_ob || 0;
    return {
      ...baseChartOptions,
      chart: { ...baseChartOptions.chart, type: 'line', height: '100%' },
      stroke: { width: [3, 0, 2], curve: 'straight', dashArray: [0, 0, 5] },
      colors: ['#3b82f6', '#0ea5e9', '#64748b'],
      markers: { size: [5, 0, 0], colors: ['#fff'], strokeColors: '#3b82f6', strokeWidth: 2, hover: { size: 7 } },
      plotOptions: { bar: { columnWidth: '20%', borderRadius: 2 } },
      dataLabels: {
        enabled: true,
        formatter: (val, opts) => {
          if (opts.seriesIndex === 0) return val === null ? '' : (val / 1000).toFixed(1);
          if (opts.seriesIndex === 1) return val > 0 ? val.toFixed(1) + 'h' : '';
          return ''; // Hide labels for Plan line
        },
        offsetY: -15,
        style: {
          colors: [
            function ({ seriesIndex, dataPointIndex, w }) {
              if (seriesIndex === 1) return '#0ea5e9';
              const val = w.globals.series[seriesIndex][dataPointIndex];
              return val >= planOb ? '#10b981' : '#ef4444';
            }
          ],
          fontSize: '18px',
          fontWeight: 900
        },
        background: {
          enabled: true,
          foreColor: '#ffffff',
          padding: 6,
          borderRadius: 4,
          borderWidth: 1,
          borderColor: '#ffffff',
          opacity: 0.9,
          dropShadow: { enabled: true, top: 2, left: 2, blur: 3, opacity: 0.2 }
        }
      },
      fill: { type: ['solid', 'solid'], opacity: [1, 0.4] },
      yaxis: [
        {
          min: -planOb * 0.15,
          title: { text: 'Cumm Volume OB (BCM)', style: { color: '#475569', fontWeight: 700, fontSize: '13px' } },
          labels: {
            formatter: (val) => val < 0 ? '' : (val / 1000).toFixed(0) + 'k',
            style: { colors: '#475569', fontWeight: 700, fontSize: '14px' }
          },
          max: (max) => Math.max(max, planOb * 1.25)
        },
        {
          opposite: true,
          title: { text: 'Rainfall (hrs)', style: { color: '#0ea5e9', fontWeight: 600, fontSize: '11px' } },
          labels: { formatter: (val) => val ? val.toFixed(1) : '', style: { colors: '#0ea5e9', fontSize: '11px' } },
          max: 4,
          min: 0,
          show: false // Optional: hide the second axis to keep UI clean, but keep the scaling
        }
      ],
      annotations: {
        position: 'back',
        yaxis: [{
          y: planOb,
          borderColor: '#3b82f6',
          strokeDashArray: 5,
          borderWidth: 2,
          label: {
            text: `Plan: ${planOb.toLocaleString('id-ID', { maximumFractionDigits: 0 })}`,
            position: 'left',
            textAnchor: 'start',
            borderColor: 'transparent',
            offsetX: 50,
            offsetY: -12,
            style: { color: '#3b82f6', background: 'transparent', fontWeight: 900, fontSize: '16px' }
          }
        }]
      }
    };
  };

  const getChOptions = () => {
    if (!chartData || !kpi) return {};
    const planCh = kpi.kpi.plans.plan_ch || 0;
    return {
      ...baseChartOptions,
      chart: { ...baseChartOptions.chart, type: 'line', height: '100%' },
      stroke: { width: [3, 0, 2], curve: 'straight', dashArray: [0, 0, 5] },
      colors: ['#10b981', '#0ea5e9', '#64748b'],
      markers: { size: [5, 0, 0], colors: ['#fff'], strokeColors: '#10b981', strokeWidth: 2, hover: { size: 7 } },
      plotOptions: { bar: { columnWidth: '20%', borderRadius: 2 } },
      dataLabels: {
        enabled: true,
        formatter: (val, opts) => {
          if (opts.seriesIndex === 0) return val === null ? '' : (val / 1000).toFixed(1);
          if (opts.seriesIndex === 1) return val > 0 ? val.toFixed(1) + 'h' : '';
          return '';
        },
        offsetY: -15,
        style: {
          colors: [
            function ({ seriesIndex, dataPointIndex, w }) {
              if (seriesIndex === 1) return '#0ea5e9';
              const val = w.globals.series[seriesIndex][dataPointIndex];
              return val >= planCh ? '#10b981' : '#ef4444';
            }
          ],
          fontSize: '18px',
          fontWeight: 900
        },
        background: {
          enabled: true,
          foreColor: '#ffffff',
          padding: 6,
          borderRadius: 4,
          borderWidth: 1,
          borderColor: '#ffffff',
          opacity: 0.9,
          dropShadow: { enabled: true, top: 2, left: 2, blur: 3, opacity: 0.2 }
        }
      },
      fill: { type: ['solid', 'solid'], opacity: [1, 0.4] },
      yaxis: [
        {
          min: -planCh * 0.15,
          title: { text: 'Cumm Volume CH (MT)', style: { color: '#475569', fontWeight: 700, fontSize: '13px' } },
          labels: {
            formatter: (val) => val < 0 ? '' : (val / 1000).toFixed(0) + 'k',
            style: { colors: '#475569', fontWeight: 700, fontSize: '14px' }
          },
          max: (max) => Math.max(max, planCh * 1.25)
        },
        {
          opposite: true,
          title: { text: 'Rainfall (hrs)', style: { color: '#0ea5e9', fontWeight: 600, fontSize: '11px' } },
          labels: { formatter: (val) => val ? val.toFixed(1) : '', style: { colors: '#0ea5e9', fontSize: '11px' } },
          max: 4,
          min: 0,
          show: false // Optional: hide the second axis to keep UI clean, but keep the scaling
        }
      ],
      annotations: {
        position: 'back',
        yaxis: [{
          y: planCh,
          borderColor: '#10b981',
          strokeDashArray: 5,
          borderWidth: 2,
          label: {
            text: `Plan: ${planCh.toLocaleString('id-ID', { maximumFractionDigits: 0 })}`,
            position: 'left',
            textAnchor: 'start',
            borderColor: 'transparent',
            offsetX: 50,
            offsetY: -12,
            style: { color: '#10b981', background: 'transparent', fontWeight: 900, fontSize: '16px' }
          }
        }]
      }
    };
  };

  const getCumulativeSeries = (key, name) => {
    if (!chartData) return [];
    let sum = 0;
    // Use global active point count so both OB and CH charts extend to the same last hour
    // This ensures cumulative values still appear even if one metric has no new volume in the latest hour
    const lastValidIdx = getActivePointCount() - 1;
    const data = chartData.data.map((d, i) => {
      if (i > lastValidIdx) return null;
      sum += d[key];
      return sum;
    });
    return [{ name, data }];
  };

  const formatDate = (dateRange) => {
    if (!dateRange || !dateRange[0]) return "Loading date...";
    return new Date(dateRange[0]).toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  const getActivePointCount = () => {
    if (!chartData) return 1;
    // Find last index where EITHER OB or CH has data
    let lastObIdx = -1;
    let lastChIdx = -1;
    for (let i = 0; i < chartData.data.length; i++) {
      if (chartData.data[i].ob > 0) lastObIdx = i;
      if (chartData.data[i].ch > 0) lastChIdx = i;
    }
    // Return maximum of both (to ensure animation covers all active data)
    const maxIdx = Math.max(lastObIdx, lastChIdx);
    return maxIdx + 1 || chartData.data.length; // Fallback to full length if no data
  };

  const getLastUpdateHour = () => {
    if (!chartData) return "N/A";
    let lastObIdx = -1;
    let lastChIdx = -1;
    for (let i = 0; i < chartData.data.length; i++) {
      if (chartData.data[i].ob > 0) lastObIdx = i;
      if (chartData.data[i].ch > 0) lastChIdx = i;
    }
    const maxIdx = Math.max(lastObIdx, lastChIdx);
    if (maxIdx === -1) return "N/A";
    return chartData.data[maxIdx]?.hour || "N/A";
  };

  const getHoursElapsed = () => {
    if (!chartData || !chartData.data) return 1;
    let count = 0;
    for (let i = 0; i < chartData.data.length; i++) {
      if (chartData.data[i].ob > 0 || chartData.data[i].ch > 0) {
        count = i + 1;
      }
    }
    return Math.max(1, count);
  };

  const hoursElapsed = getHoursElapsed();
  const actualOb = kpi?.kpi?.actuals?.actual_ob || 0;
  const planOb = kpi?.kpi?.plans?.plan_ob || 0;
  const avgOb = actualOb / hoursElapsed;

  const actualCh = kpi?.kpi?.actuals?.actual_ch || 0;
  const planCh = kpi?.kpi?.plans?.plan_ch || 0;
  const avgCh = actualCh / hoursElapsed;

  const delayPerPoint = 1.0 / Math.max(getActivePointCount(), 1);
  const staggeredDelays = Array.from({ length: 30 }).map((_, i) => `
    .apexcharts-datalabel:nth-child(${i + 1}), 
    .apexcharts-series-markers .apexcharts-marker:nth-child(${i + 1}) { 
      animation-delay: ${(i * delayPerPoint).toFixed(2)}s !important; 
    }
  `).join('');

  return (
    <div className="h-screen overflow-y-auto p-3 md:p-4 w-full flex flex-col gap-4">
      <style>{staggeredDelays}</style>
      {/* Top Navigation & Header - Static across slides */}
      <header className="relative flex justify-between items-center gap-6 animate-fade-in-up shrink-0 z-10 pb-2 h-16">
        {/* Left: Logo */}
        <div className="flex items-center gap-4 z-10">
          <img src="/logo_mge.png" alt="MGE Logo" className="h-[60px] object-contain drop-shadow-sm shrink-0" />
        </div>

        {/* Center: Segmented Control (Absolutely centered) */}
        <div className="hidden xl:flex absolute left-1/2 -translate-x-1/2 items-center p-1.5 bg-white/70 rounded-2xl shadow-lg border border-slate-200/80 backdrop-blur-2xl h-[68px] z-0">
          {PITS.map((p) => (
            <button
              key={p}
              onClick={() => { setPit(p); setAutoPlay(false); }}
              className={`px-8 h-full whitespace-nowrap rounded-xl text-[19px] transition-all duration-300 font-black tracking-wide ${pit === p
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 scale-[1.02]'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
            >
              {p}
            </button>
          ))}
        </div>

        {/* Right: Info & Auto Play */}
        <div className="flex justify-end items-center gap-3 shrink-0 h-14 z-10">
          <div className="flex items-center gap-2 px-4 h-full bg-white/70 rounded-xl shadow-sm border border-slate-200/80 text-slate-700 font-bold text-sm whitespace-nowrap backdrop-blur-2xl">
            <Calendar size={16} className="text-emerald-600" />
            {kpi ? formatDate(kpi.date_range) : 'Loading...'}
          </div>
          <button
            onClick={() => setAutoPlay(!autoPlay)}
            className={`flex items-center gap-2 px-5 h-full rounded-xl font-bold text-sm transition-all shadow-sm border whitespace-nowrap backdrop-blur-2xl ${autoPlay
                ? 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                : 'bg-white/70 text-slate-600 border-slate-200/80 hover:bg-slate-100'
              }`}
          >
            {autoPlay ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
            {autoPlay ? 'Auto ON' : 'Paused'}
          </button>
        </div>
      </header>

      {/* KPI & Charts Wrapper */}
      <main className={`flex flex-col gap-4 flex-grow min-h-0 transition-all duration-500 ease-out ${isFetching ? 'opacity-40 blur-[2px] scale-[0.99] pointer-events-none' : 'opacity-100 blur-0 scale-100'}`}>

        {/* KPI Section */}
        <div className="shrink-0">
          {kpi ? (
            <div className={`grid grid-cols-2 lg:grid-cols-3 ${(kpi.kpi.actuals.actual_ct > 0 || kpi.kpi.plans.plan_ct > 0) ? 'xl:grid-cols-6' : 'xl:grid-cols-5'} gap-4`}>
              <KpiCard
                title="Overburden"
                actualValue={kpi.kpi.actuals.actual_ob}
                targetValue={kpi.kpi.plans.plan_ob}
                unit="BCM"
                delayClass=""
              />
              <KpiCard
                title="Coal Hauling"
                actualValue={kpi.kpi.actuals.actual_ch}
                targetValue={kpi.kpi.plans.plan_ch}
                unit="MT"
                delayClass="delay-100"
              />
              {(kpi.kpi.actuals.actual_ct > 0 || kpi.kpi.plans.plan_ct > 0) ? (
                <KpiCard
                  title="Coal Transit"
                  actualValue={kpi.kpi.actuals.actual_ct}
                  targetValue={kpi.kpi.plans.plan_ct}
                  unit="MT"
                  delayClass="delay-[150ms]"
                />
              ) : null}
              <KpiCard
                title="Stripping Ratio"
                actualValue={kpi.kpi.sr}
                isRatio={true}
                unit="Ratio"
                customSubtitle={`Global SR: ${kpi.kpi.global_sr.toLocaleString('id-ID', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
                delayClass="delay-200"
              />
              <KpiCard
                title="Stock ROM"
                actualValue={kpi.kpi.stock.coal_stock_rom}
                unit="MT"
                delayClass="delay-300"
              />
              <KpiCard
                title="Stock Port"
                actualValue={kpi.kpi.stock.coal_stock_port}
                unit="MT"
                delayClass="delay-400"
              />
            </div>
          ) : (
            <div className="h-28 flex flex-col items-center justify-center text-slate-400 glass-card rounded-xl animate-pulse-slow">
              <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-3"></div>
              <p className="font-semibold tracking-widest uppercase text-xs">Synchronizing Data...</p>
            </div>
          )}
        </div>

        {/* Main Charts Section - Stacked Vertically & Flex Grow to Fit Screen */}
        <div className="flex flex-col gap-3 animate-fade-in-up delay-200 flex-grow min-h-0">

          {/* OB Chart */}
          <div className="glass-card px-4 pt-4 pb-0 rounded-xl flex flex-col flex-grow min-h-[220px]">
            <div className="flex flex-wrap justify-between items-start md:items-center mb-2 shrink-0 gap-4">
              <div className="flex items-center flex-wrap gap-4">
                <h3 className="text-[17px] font-black text-slate-800 font-outfit tracking-wide flex items-center gap-2">
                  Cumulative OB Production
                  <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"></div>
                </h3>
                {chartData && (
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded border border-blue-200">
                      Last Update: {getLastUpdateHour()}:00
                    </span>
                    <div className="flex items-center gap-3 text-[10px] font-semibold text-slate-500">
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded bg-blue-500"></div> Cumm OB</span>
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded bg-sky-400"></div> Rainfall (hrs)</span>
                    </div>
                  </div>
                )}
              </div>
              <ChartSummaryMetrics actual={actualOb} plan={planOb} avgRate={avgOb} unit="BCM" themeColor="blue" />
            </div>
            <div className="flex-grow w-full min-h-0 relative -ml-2 -mb-3">
              {chartData ? (
                <Chart
                  options={getObOptions()}
                  series={[
                    ...getCumulativeSeries('ob', 'Cumm Actual OB'),
                    { name: 'Rainfall', type: 'column', data: chartData.data.map(d => d.rain) },
                    { name: 'Plan', type: 'line', data: chartData.targets?.ob_plan_line || [] }
                  ]}
                  type="line" height="100%" width="100%"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center text-slate-500 font-medium text-xs">Awaiting telemetry...</div>
              )}
            </div>
          </div>

          {/* CH Chart */}
          <div className="glass-card px-4 pt-4 pb-0 rounded-xl flex flex-col flex-grow min-h-[220px]">
            <div className="flex flex-wrap justify-between items-start md:items-center mb-2 shrink-0 gap-4">
              <div className="flex items-center flex-wrap gap-4">
                <h3 className="text-[17px] font-black text-slate-800 font-outfit tracking-wide flex items-center gap-2">
                  Cumulative Coal Hauling
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                </h3>
                {chartData && (
                  <div className="flex items-center gap-4">
                    <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                      Last Update: {getLastUpdateHour()}:00
                    </span>
                    <div className="flex items-center gap-3 text-[10px] font-semibold text-slate-500">
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded bg-emerald-500"></div> Cumm CH</span>
                      <span className="flex items-center gap-1"><div className="w-2 h-2 rounded bg-sky-400"></div> Rainfall (hrs)</span>
                    </div>
                  </div>
                )}
              </div>
              <ChartSummaryMetrics actual={actualCh} plan={planCh} avgRate={avgCh} unit="MT" themeColor="emerald" />
            </div>
            <div className="flex-grow w-full min-h-0 relative -ml-2 -mb-3">
              {chartData ? (
                <Chart
                  options={getChOptions()}
                  series={[
                    ...getCumulativeSeries('ch', 'Cumm Actual CH'),
                    { name: 'Rainfall', type: 'column', data: chartData.data.map(d => d.rain) },
                    { name: 'Plan', type: 'line', data: chartData.targets?.ch_plan_line || [] }
                  ]}
                  type="line" height="100%" width="100%"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center text-slate-500 font-medium text-xs">Awaiting telemetry...</div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
