// import { useCallback, useEffect, useState } from "react";
// import {
//   Area,
//   AreaChart,
//   Bar,
//   BarChart,
//   Cell,
//   PolarAngleAxis,
//   PolarGrid,
//   Radar,
//   RadarChart,
//   ResponsiveContainer,
//   Tooltip,
//   XAxis, YAxis
// } from "recharts";

// const API = "http://127.0.0.1:8000";
// const POLL_MS = 1800;

// const T = {
//   bg:"#04080f", bg2:"#070d18", panel:"#080f1c", border:"#0b1e33", line:"#091828",
//   cyan:"#00d4f5", cyanDim:"#006d7e", green:"#00e5a0", orange:"#ff9a3c",
//   red:"#ff3060", yellow:"#f5d000", text:"#7fb0cc", bright:"#e0f4ff",
//   dim:"#1e3a52", dimText:"#3a6080",
// };

// const priority = p =>
//   p > 0.80 ? {label:"CRITICAL",color:T.red,   glow:"rgba(255,48,96,0.35)"} :
//   p > 0.60 ? {label:"HIGH",    color:T.orange, glow:"rgba(255,154,60,0.3)"} :
//   p > 0.40 ? {label:"MEDIUM",  color:T.yellow, glow:"rgba(245,208,0,0.28)"} :
//              {label:"LOW",     color:T.green,  glow:"rgba(0,229,160,0.25)"};

// const fmt = ts => new Date(ts*1000).toLocaleTimeString("en-GB",{hour12:false});

// // ── Global CSS ─────────────────────────────────────────────────────────────
// const CSS = `
// @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=IBM+Plex+Mono:wght@300;400;600&family=Barlow:wght@300;400;500;600;700&display=swap');
// *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
// html,body{height:100%;background:${T.bg};color:${T.text};font-family:'Barlow',sans-serif;font-size:13px;overflow-x:hidden;}
// ::-webkit-scrollbar{width:3px;}::-webkit-scrollbar-track{background:${T.bg};}::-webkit-scrollbar-thumb{background:${T.cyanDim};border-radius:2px;}
// .orb{font-family:'Orbitron',monospace;}.mono{font-family:'IBM Plex Mono',monospace;}
// #root::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
//   background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.045) 3px,rgba(0,0,0,0.045) 4px);}
// @keyframes pulse-ring{0%{transform:scale(.6);opacity:.8}100%{transform:scale(2.2);opacity:0}}
// @keyframes blink{0%,100%{opacity:1}50%{opacity:.1}}
// @keyframes slide-down{from{opacity:0;transform:translateY(-7px)}to{opacity:1;transform:translateY(0)}}
// @keyframes glow-pulse{0%,100%{opacity:.5}50%{opacity:1}}
// .blink{animation:blink 2.4s step-end infinite;}
// .slide-down{animation:slide-down .22s ease forwards;}
// .gp{animation:glow-pulse 2s ease-in-out infinite;}
// .bracket{position:relative;}
// .bracket::before,.bracket::after{content:'';position:absolute;width:9px;height:9px;}
// .bracket::before{top:0;left:0;border-top:1.5px solid ${T.cyan};border-left:1.5px solid ${T.cyan};}
// .bracket::after{top:0;right:0;border-top:1.5px solid ${T.cyan};border-right:1.5px solid ${T.cyan};}
// .panel{background:${T.panel};border:1px solid ${T.border};position:relative;}
// .phdr{display:flex;align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid ${T.border};
//   background:rgba(0,212,245,0.025);font-size:9px;font-weight:600;letter-spacing:.18em;
//   text-transform:uppercase;color:${T.cyan};font-family:'Orbitron',monospace;}
// .trow{display:grid;align-items:center;padding:0 14px;height:38px;
//   border-bottom:1px solid ${T.line};cursor:pointer;transition:background .12s;}
// .trow:hover{background:rgba(0,212,245,0.04);}
// .trow.sel{background:rgba(0,212,245,0.07);border-left:2px solid ${T.cyan};}
// .badge{display:inline-flex;align-items:center;padding:2px 7px;border-radius:2px;
//   font-size:9px;font-weight:700;letter-spacing:.12em;font-family:'IBM Plex Mono',monospace;}
// .btn{padding:5px 11px;border:1px solid ${T.border};background:transparent;
//   color:${T.text};font-family:'IBM Plex Mono',monospace;font-size:9px;
//   letter-spacing:.1em;cursor:pointer;transition:all .18s;}
// .btn:hover{border-color:${T.cyan};color:${T.cyan};background:rgba(0,212,245,.05);}
// .btn.danger:hover{border-color:${T.red};color:${T.red};background:rgba(255,48,96,.05);}
// .kpi{background:${T.panel};border:1px solid ${T.border};
//   border-top:2px solid var(--c,${T.cyan});padding:16px 18px;position:relative;overflow:hidden;}
// .kpi::before{content:'';position:absolute;bottom:0;left:0;right:0;height:45%;
//   background:linear-gradient(to top,var(--cd,rgba(0,212,245,.04)),transparent);}
// .bar-track{height:4px;border-radius:2px;background:${T.dim}50;overflow:hidden;}
// .bar-fill{height:100%;border-radius:2px;background:var(--c,${T.cyan});
//   box-shadow:0 0 6px var(--c,${T.cyan});transition:width .7s ease;}
// .tab{padding:6px 14px;font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
//   font-family:'Orbitron',monospace;cursor:pointer;border-bottom:2px solid transparent;
//   color:${T.dimText};transition:all .18s;}
// .tab.active{border-bottom-color:${T.cyan};color:${T.cyan};}
// .cdot{width:7px;height:7px;border-radius:50%;background:var(--c);position:relative;}
// .cdot::after{content:'';position:absolute;inset:0;border-radius:50%;background:var(--c);
//   animation:pulse-ring 1.8s ease-out infinite;}
// `;

// // ── Data hook ──────────────────────────────────────────────────────────────
// function useSOCData() {
//   const [events, setEvents] = useState([]);
//   const [stats,  setStats]  = useState(null);
//   const [conn,   setConn]   = useState("connecting");

//   const fetchAll = useCallback(async () => {
//     try {
//       const [evRes, stRes] = await Promise.all([
//         fetch(`${API}/events?limit=80`),
//         fetch(`${API}/stats`),
//       ]);
//       if (!evRes.ok || !stRes.ok) throw new Error("non-2xx");
//       setEvents(await evRes.json());
//       setStats(await stRes.json());
//       setConn("online");
//     } catch { setConn("error"); }
//   }, []);

//   useEffect(()=>{
//     fetchAll();
//     const t = setInterval(fetchAll, POLL_MS);
//     return ()=>clearInterval(t);
//   }, [fetchAll]);

//   return { events, stats, conn };
// }

// // ── Small atoms ────────────────────────────────────────────────────────────
// const ConnDot = ({status}) => {
//   const c = status==="online"?T.green:status==="error"?T.red:T.yellow;
//   return <div className="cdot" style={{"--c":c}} title={status.toUpperCase()}/>;
// };

// const Badge = ({prob}) => {
//   const p=priority(prob);
//   return <span className="badge" style={{background:`${p.color}18`,color:p.color,border:`1px solid ${p.color}40`}}>{p.label}</span>;
// };

// const MiniBar = ({v,c}) => (
//   <div className="bar-track"><div className="bar-fill" style={{width:`${v*100}%`,"--c":c}}/></div>
// );

// const LayerDot = ({pred}) => (
//   <span style={{display:"inline-block",width:6,height:6,borderRadius:"50%",marginRight:4,
//     background:pred==="attack"?T.red:T.green,boxShadow:`0 0 5px ${pred==="attack"?T.red:T.green}`}}/>
// );

// // ── Header ─────────────────────────────────────────────────────────────────
// function Header({conn,stats}) {
//   const [clock,setClock] = useState(new Date());
//   useEffect(()=>{ const t=setInterval(()=>setClock(new Date()),1000); return()=>clearInterval(t); },[]);
//   return (
//     <header style={{position:"sticky",top:0,zIndex:200,height:52,padding:"0 22px",
//       display:"flex",alignItems:"center",justifyContent:"space-between",
//       background:`linear-gradient(180deg,#050b15 0%,${T.bg} 100%)`,
//       borderBottom:`1px solid ${T.border}`}}>
//       <div style={{display:"flex",alignItems:"center",gap:12}}>
//         <div style={{width:32,height:32,borderRadius:3,
//           background:`linear-gradient(135deg,${T.cyan},#0052ff)`,
//           display:"flex",alignItems:"center",justifyContent:"center",
//           fontSize:14,fontWeight:900,color:"#fff",fontFamily:"Orbitron",
//           boxShadow:`0 0 16px rgba(0,212,245,.45)`}}>V</div>
//         <div>
//           <div className="orb" style={{fontSize:14,fontWeight:700,letterSpacing:".1em",
//             color:T.bright,lineHeight:1}}>VECTRA <span style={{color:T.cyan}}>SOC</span></div>
//           <div style={{fontSize:8,letterSpacing:".22em",color:T.dimText,marginTop:2}}>
//             AI THREAT DETECTION PLATFORM · 3-LAYER FUSION ENGINE
//           </div>
//         </div>
//       </div>
//       <div className="mono" style={{display:"flex",gap:20,fontSize:10,color:T.text,alignItems:"center"}}>
//         <span style={{display:"flex",alignItems:"center",gap:7}}>
//           <ConnDot status={conn}/>
//           <span style={{color:conn==="online"?T.green:conn==="error"?T.red:T.yellow}}>
//             {conn.toUpperCase()}
//           </span>
//         </span>
//         <span style={{color:T.dimText}}>|</span>
//         <span>EVENTS <span style={{color:T.cyan}}>{stats?.total??0}</span></span>
//         <span style={{color:T.dimText}}>|</span>
//         <span>ATTACKS <span style={{color:T.red}}>{stats?.attacks??0}</span></span>
//         <span style={{color:T.dimText}}>|</span>
//         <span>RATE <span style={{color:(stats?.attack_rate_pct??0)>50?T.red:T.cyan}}>{stats?.attack_rate_pct??0}%</span></span>
//         <span style={{color:T.dimText}}>|</span>
//         <span className="blink" style={{color:T.cyan,fontSize:11}}>
//           {clock.toLocaleTimeString("en-GB",{hour12:false})} UTC
//         </span>
//       </div>
//       <div style={{display:"flex",gap:8}}>
//         <button className="btn">⬇ EXPORT</button>
//         <button className="btn danger">⊗ ISOLATE</button>
//       </div>
//     </header>
//   );
// }

// // ── KPI row ────────────────────────────────────────────────────────────────
// function KpiRow({stats}) {
//   const cards = [
//     {label:"Total Events",    value:stats?.total??0,             c:T.cyan,  cd:"rgba(0,212,245,.04)",  icon:"⬡"},
//     {label:"Attacks Detected",value:stats?.attacks??0,           c:T.red,   cd:"rgba(255,48,96,.04)",  icon:"⚠"},
//     {label:"High Risk >0.8",  value:stats?.high_risk??0,         c:T.orange,cd:"rgba(255,154,60,.04)", icon:"◉"},
//     {label:"Avg Threat Score",value:stats?.avg_threat_score??0,  c:T.yellow,cd:"rgba(245,208,0,.04)",  icon:"≋"},
//   ];
//   return (
//     <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
//       {cards.map(({label,value,c,cd,icon})=>(
//         <div key={label} className="kpi bracket" style={{"--c":c,"--cd":cd}}>
//           <div style={{fontSize:8,letterSpacing:".2em",textTransform:"uppercase",color:T.dimText,marginBottom:8}}>
//             {icon} {label}
//           </div>
//           <div className="orb" style={{fontSize:28,color:c,lineHeight:1,marginBottom:4,
//             textShadow:`0 0 18px ${c}55`}}>
//             {typeof value==="number"&&value>0&&value<2?value.toFixed(3):value}
//           </div>
//           <div style={{position:"absolute",right:14,top:"50%",transform:"translateY(-50%)",
//             fontSize:26,opacity:.05,color:c,fontFamily:"Orbitron"}}>{icon}</div>
//         </div>
//       ))}
//     </div>
//   );
// }

// // ── Threat table ───────────────────────────────────────────────────────────
// const GCOLS = "100px 1fr 100px 80px 110px 72px 70px";
// const CHDR  = ["PRIORITY","SOURCE IP","TYPE","LAYERS","SCORE","VERDICT","TIME"];

// function ThreatTable({events,selected,onSelect,filter,setFilter}) {
//   const sorted   = [...events].sort((a,b)=>b.attack_probability-a.attack_probability);
//   const filtered = filter==="all"?sorted:filter==="attack"?sorted.filter(e=>e.label==="attack"):sorted.filter(e=>e.label==="normal");

//   return (
//     <div className="panel" style={{flex:1}}>
//       <div className="phdr">
//         <div className="cdot gp" style={{"--c":T.red,width:6,height:6}}/>
//         Active Detections
//         <div style={{marginLeft:"auto",display:"flex",gap:6}}>
//           {["all","attack","normal"].map(f=>(
//             <button key={f} className="btn" style={{
//               borderColor:filter===f?T.cyan:T.border,
//               color:filter===f?T.cyan:T.text,
//               background:filter===f?"rgba(0,212,245,.06)":"transparent"}}
//               onClick={()=>setFilter(f)}>{f.toUpperCase()}</button>
//           ))}
//         </div>
//         <span className="mono" style={{color:T.cyan,fontSize:10,marginLeft:8}}>
//           {filtered.length} EVENTS
//         </span>
//       </div>
//       {/* Header row */}
//       <div className="mono" style={{display:"grid",gridTemplateColumns:GCOLS,
//         padding:"0 14px",height:28,alignItems:"center",
//         borderBottom:`1px solid ${T.border}`,fontSize:8,letterSpacing:".16em",color:T.dimText}}>
//         {CHDR.map(c=><div key={c}>{c}</div>)}
//       </div>
//       <div style={{maxHeight:360,overflowY:"auto"}}>
//         {filtered.slice(0,25).map((ev,i)=>{
//           const p=priority(ev.attack_probability);
//           return (
//             <div key={ev.id??i}
//               className={`trow slide-down mono ${selected?.id===ev.id?"sel":""}`}
//               style={{gridTemplateColumns:GCOLS,"animationDelay":`${i*.025}s`}}
//               onClick={()=>onSelect(ev)}>
//               <Badge prob={ev.attack_probability}/>
//               <span style={{color:T.bright,fontSize:12}}>{ev.src_ip}</span>
//               <span style={{color:p.color,fontSize:10}}>{ev.attack_type??"-"}</span>
//               <span style={{display:"flex",alignItems:"center"}}>
//                 <LayerDot pred={ev.packet_label}/>
//                 <LayerDot pred={ev.flow_label}/>
//                 <LayerDot pred={ev.behaviour_label}/>
//               </span>
//               <div>
//                 <div style={{fontSize:11,color:p.color,marginBottom:2}}>
//                   {ev.attack_probability?.toFixed(3)}
//                 </div>
//                 <MiniBar v={ev.attack_probability} c={p.color}/>
//               </div>
//               <span style={{color:ev.label==="attack"?T.red:T.green,fontSize:10,fontWeight:700}}>
//                 {ev.label?.toUpperCase()}
//               </span>
//               <span style={{color:T.dimText,fontSize:10}}>{fmt(ev.timestamp)}</span>
//             </div>
//           );
//         })}
//       </div>
//     </div>
//   );
// }

// // ── Investigation panel ────────────────────────────────────────────────────
// function InvestPanel({ev}) {
//   if(!ev) return (
//     <div className="panel" style={{flex:1,display:"flex",alignItems:"center",justifyContent:"center"}}>
//       <div style={{textAlign:"center",color:T.dimText}}>
//         <div style={{fontSize:28,marginBottom:8}}>◎</div>
//         <div className="mono" style={{fontSize:9,letterSpacing:".14em"}}>SELECT AN EVENT</div>
//       </div>
//     </div>
//   );

//   const p=priority(ev.attack_probability);
//   const layers=[
//     {name:"PACKET",   label:ev.packet_label,   prob:ev.packet_prob,   model:"Autoencoder + Isolation Forest"},
//     {name:"FLOW",     label:ev.flow_label,     prob:ev.flow_prob,     model:"Flow Autoencoder"},
//     {name:"BEHAVIOUR",label:ev.behaviour_label,prob:ev.behaviour_prob,model:"LSTM Autoencoder"},
//   ];
//   const radar=layers.map(l=>({subject:l.name,score:+((l.prob??0)*100).toFixed(1)}));

//   return (
//     <div className="panel" style={{flex:1,display:"flex",flexDirection:"column"}}>
//       <div className="phdr">
//         <span>⊕</span> Investigation
//         <span className="mono" style={{marginLeft:"auto",color:T.dimText,fontSize:9}}>#{ev.id}</span>
//       </div>

//       {/* Verdict */}
//       <div style={{padding:"16px 18px",borderBottom:`1px solid ${T.border}`,
//         background:`linear-gradient(135deg,${p.color}0c,transparent 60%)`}}>
//         <div style={{fontSize:8,letterSpacing:".2em",color:T.dimText,marginBottom:5}}>
//           FUSION VERDICT · MAJORITY VOTE (2/3)
//         </div>
//         <div className="orb" style={{fontSize:20,fontWeight:700,color:p.color,
//           textShadow:`0 0 18px ${p.glow}`}}>{ev.label?.toUpperCase()}</div>
//         <div className="orb" style={{fontSize:26,color:T.bright,marginTop:3,lineHeight:1}}>
//           {ev.attack_probability?.toFixed(3)}
//           <span style={{fontFamily:"Barlow",fontSize:11,color:T.text,marginLeft:5,fontWeight:400}}>confidence</span>
//         </div>
//         <div className="mono" style={{marginTop:10,display:"flex",gap:14,fontSize:10,color:T.text,flexWrap:"wrap"}}>
//           <span>SRC: <span style={{color:T.bright}}>{ev.src_ip}</span></span>
//           <span>TYPE: <span style={{color:p.color}}>{ev.attack_type??"-"}</span></span>
//           <span>PKT: <span style={{color:T.bright}}>{ev.packet_size}B</span></span>
//           <span>T: <span style={{color:T.bright}}>{fmt(ev.timestamp)}</span></span>
//         </div>
//       </div>

//       {/* Radar */}
//       <div style={{padding:"8px 0 0",borderBottom:`1px solid ${T.border}`}}>
//         <ResponsiveContainer width="100%" height={100}>
//           <RadarChart data={radar} margin={{top:6,right:20,bottom:6,left:20}}>
//             <PolarGrid stroke={T.dim} strokeOpacity={0.5}/>
//             <PolarAngleAxis dataKey="subject" tick={{fill:T.text,fontSize:9,fontFamily:"IBM Plex Mono"}}/>
//             <Radar name="Score" dataKey="score" stroke={p.color}
//               fill={p.color} fillOpacity={0.18} strokeWidth={1.5}/>
//           </RadarChart>
//         </ResponsiveContainer>
//       </div>

//       {/* Layers */}
//       <div style={{padding:"14px 18px",flex:1,display:"flex",flexDirection:"column",gap:13}}>
//         <div style={{fontSize:8,letterSpacing:".2em",color:T.dimText}}>DETECTION LAYERS</div>
//         {layers.map(layer=>{
//           const lp=priority(layer.prob??0);
//           return (
//             <div key={layer.name}>
//               <div style={{display:"flex",justifyContent:"space-between",marginBottom:4,alignItems:"flex-end"}}>
//                 <div>
//                   <div className="mono" style={{fontSize:10,color:T.text,letterSpacing:".1em"}}>{layer.name}</div>
//                   <div style={{fontSize:8,color:T.dimText,marginTop:1}}>{layer.model}</div>
//                 </div>
//                 <div style={{display:"flex",gap:7,alignItems:"center"}}>
//                   <span className="mono" style={{fontSize:11,color:lp.color}}>{layer.prob?.toFixed(3)}</span>
//                   <span className="badge" style={{background:`${lp.color}18`,color:lp.color,
//                     border:`1px solid ${lp.color}30`}}>{layer.label?.toUpperCase()}</span>
//                 </div>
//               </div>
//               <div style={{background:`${T.dim}30`,borderRadius:2,height:5,overflow:"hidden"}}>
//                 <div style={{height:"100%",width:`${(layer.prob??0)*100}%`,borderRadius:2,
//                   background:`linear-gradient(90deg,${lp.color}66,${lp.color})`,
//                   transition:"width .9s ease",boxShadow:`0 0 8px ${lp.color}99`}}/>
//               </div>
//             </div>
//           );
//         })}
//       </div>

//       {/* Actions */}
//       <div style={{borderTop:`1px solid ${T.border}`,padding:"10px 14px",display:"flex",gap:6}}>
//         {["BLOCK IP","TRACE","QUARANTINE","RULE"].map(a=>(
//           <button key={a} className="btn" style={{flex:1,textAlign:"center"}}>{a}</button>
//         ))}
//       </div>
//     </div>
//   );
// }

// // ── Trend chart ────────────────────────────────────────────────────────────
// function TrendChart({events}) {
//   const data = events.sort((a,b)=>a.timestamp-b.timestamp)
//     .reduce((acc,ev)=>{
//       const b=Math.floor(ev.timestamp/8)*8;
//       const ex=acc.find(x=>x.t===b);
//       if(ex){ex.vals.push(ev.attack_probability);}else{acc.push({t:b,vals:[ev.attack_probability]});}
//       return acc;
//     },[])
//     .map(({t,vals})=>({time:fmt(t),
//       avg:+(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(3),
//       peak:+Math.max(...vals).toFixed(3)}));

//   const Tip=({active,payload})=>{
//     if(!active||!payload?.length) return null;
//     return <div style={{background:"#030b14",border:`1px solid #0a2840`,padding:"6px 10px",
//       fontFamily:"IBM Plex Mono",fontSize:10,color:T.bright}}>
//       <div style={{color:T.dimText,fontSize:8,marginBottom:3}}>{payload[0]?.payload?.time}</div>
//       <div>AVG <span style={{color:T.cyan}}>{payload[0]?.value}</span></div>
//       {payload[1]&&<div>PEAK <span style={{color:T.red}}>{payload[1]?.value}</span></div>}
//     </div>;
//   };

//   return (
//     <div className="panel">
//       <div className="phdr"><span>▲</span> Threat Score Trend</div>
//       <div style={{padding:"12px 8px 8px"}}>
//         <ResponsiveContainer width="100%" height={110}>
//           <AreaChart data={data} margin={{top:4,right:16,bottom:0,left:0}}>
//             <defs>
//               <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1">
//                 <stop offset="5%" stopColor={T.cyan} stopOpacity={.25}/><stop offset="95%" stopColor={T.cyan} stopOpacity={0}/>
//               </linearGradient>
//               <linearGradient id="gB" x1="0" y1="0" x2="0" y2="1">
//                 <stop offset="5%" stopColor={T.red} stopOpacity={.2}/><stop offset="95%" stopColor={T.red} stopOpacity={0}/>
//               </linearGradient>
//             </defs>
//             <XAxis dataKey="time" tick={{fill:T.dimText,fontSize:8,fontFamily:"IBM Plex Mono"}} axisLine={false} tickLine={false}/>
//             <YAxis domain={[0,1]} tick={{fill:T.dimText,fontSize:8}} axisLine={false} tickLine={false} width={28}/>
//             <Tooltip content={<Tip/>} cursor={{stroke:`${T.cyan}30`,strokeWidth:1}}/>
//             <Area type="monotone" dataKey="avg" stroke={T.cyan} strokeWidth={1.5}
//               fill="url(#gA)" dot={false} activeDot={{r:3,fill:T.cyan}}/>
//             <Area type="monotone" dataKey="peak" stroke={T.red} strokeWidth={1}
//               fill="url(#gB)" dot={false} activeDot={{r:3,fill:T.red}}/>
//           </AreaChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }

// // ── Attack type chart ──────────────────────────────────────────────────────
// function AttackChart({stats}) {
//   if(!stats?.attack_types) return null;
//   const data=Object.entries(stats.attack_types).map(([name,count])=>({name,count})).sort((a,b)=>b.count-a.count);
//   const COLS=[T.red,T.orange,T.yellow,T.cyan,T.green,"#a78bfa"];
//   return (
//     <div className="panel">
//       <div className="phdr"><span>▦</span> Attack Distribution</div>
//       <div style={{padding:"12px 8px 8px"}}>
//         <ResponsiveContainer width="100%" height={110}>
//           <BarChart data={data} margin={{top:4,right:16,bottom:0,left:0}}>
//             <XAxis dataKey="name" tick={{fill:T.dimText,fontSize:8,fontFamily:"IBM Plex Mono"}} axisLine={false} tickLine={false}/>
//             <YAxis tick={{fill:T.dimText,fontSize:8}} axisLine={false} tickLine={false} width={24}/>
//             <Bar dataKey="count" radius={[2,2,0,0]}>
//               {data.map((_,i)=><Cell key={i} fill={COLS[i%COLS.length]} opacity={0.85}/>)}
//             </Bar>
//           </BarChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }

// // ── Heatmap ────────────────────────────────────────────────────────────────
// function Heatmap({events,onSelect}) {
//   const last=[...events].slice(-60);
//   return (
//     <div className="panel">
//       <div className="phdr"><span>◈</span> Risk Heatmap · Last 60</div>
//       <div style={{padding:"10px 14px",display:"grid",gridTemplateColumns:"repeat(12,1fr)",gap:3}}>
//         {last.map((ev,i)=>{
//           const p=priority(ev.attack_probability);
//           return <div key={i} onClick={()=>onSelect(ev)}
//             title={`${ev.src_ip} | ${ev.attack_probability}`}
//             style={{height:14,borderRadius:2,cursor:"pointer",
//               background:p.color,opacity:0.35+ev.attack_probability*0.65,transition:"opacity .2s"}}
//             onMouseEnter={e=>e.target.style.opacity=1}
//             onMouseLeave={e=>e.target.style.opacity=0.35+ev.attack_probability*0.65}/>;
//         })}
//       </div>
//       <div className="mono" style={{padding:"2px 14px 10px",display:"flex",gap:14,fontSize:8,color:T.dimText}}>
//         <span style={{color:T.green}}>■ LOW</span>
//         <span style={{color:T.yellow}}>■ MEDIUM</span>
//         <span style={{color:T.orange}}>■ HIGH</span>
//         <span style={{color:T.red}}>■ CRITICAL</span>
//       </div>
//     </div>
//   );
// }

// // ── Geo matrix ─────────────────────────────────────────────────────────────
// function GeoMatrix({events}) {
//   const attacks=events.filter(e=>e.label==="attack").slice(-15);
//   return (
//     <div className="panel">
//       <div className="phdr"><span>◎</span> Origin Matrix</div>
//       <div style={{position:"relative",height:130,
//         background:`radial-gradient(ellipse at 50% 50%,#071525,${T.panel} 75%)`,overflow:"hidden"}}>
//         {[...Array(6)].map((_,i)=><div key={`h${i}`} style={{position:"absolute",left:0,right:0,
//           top:`${(i+1)*14.3}%`,borderTop:`1px solid ${T.line}`}}/>)}
//         {[...Array(11)].map((_,i)=><div key={`v${i}`} style={{position:"absolute",top:0,bottom:0,
//           left:`${(i+1)*8.33}%`,borderLeft:`1px solid ${T.line}`}}/>)}
//         {attacks.map((ev,i)=>{
//           const parts=ev.src_ip.split(".");
//           const x=((parseInt(parts[3]??50))%90)+5;
//           const y=((parseInt(parts[2]??30))%80)+10;
//           const p=priority(ev.attack_probability);
//           return <div key={ev.id??i} style={{position:"absolute",left:`${x}%`,top:`${y}%`,transform:"translate(-50%,-50%)"}}>
//             <div style={{width:7,height:7,borderRadius:"50%",background:p.color,
//               boxShadow:`0 0 8px ${p.color},0 0 16px ${p.glow}`,position:"relative"}}>
//               <div style={{position:"absolute",inset:-5,borderRadius:"50%",border:`1px solid ${p.color}`,
//                 opacity:.3,animation:"pulse-ring 2.2s ease-out infinite",animationDelay:`${i*.18}s`}}/>
//             </div>
//           </div>;
//         })}
//         <div className="mono" style={{position:"absolute",bottom:5,right:10,fontSize:7,color:T.dimText,letterSpacing:".12em"}}>
//           IP GEO-MATRIX
//         </div>
//       </div>
//     </div>
//   );
// }

// // ── Error screen ───────────────────────────────────────────────────────────
// function ErrorScreen() {
//   return (
//     <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",
//       flexDirection:"column",gap:16}}>
//       <div className="orb" style={{fontSize:48,color:T.red,textShadow:`0 0 30px ${T.red}`}}>⊗</div>
//       <div className="orb" style={{fontSize:16,color:T.red,letterSpacing:".12em"}}>BACKEND OFFLINE</div>
//       <div className="mono" style={{fontSize:11,color:T.text,maxWidth:380,textAlign:"center",lineHeight:1.7}}>
//         Cannot reach <span style={{color:T.cyan}}>{API}</span>
//         <br/>Make sure the backend is running:
//       </div>
//       <div style={{background:T.panel,border:`1px solid ${T.border}`,padding:"12px 20px",
//         fontFamily:"IBM Plex Mono",fontSize:11,color:T.cyan,borderLeft:`3px solid ${T.cyan}`}}>
//         python backend.py
//       </div>
//     </div>
//   );
// }

// // ── ROOT APP ───────────────────────────────────────────────────────────────
// export default function App() {
//   const {events,stats,conn} = useSOCData();
//   const [selected,setSelected] = useState(null);
//   const [filter,  setFilter]   = useState("all");
//   const [tab,     setTab]      = useState("threats");

//   useEffect(()=>{
//     if(!selected&&events.length){
//       const top=[...events].sort((a,b)=>b.attack_probability-a.attack_probability)[0];
//       setSelected(top);
//     }
//   },[events]);

//   return (
//     <div style={{minHeight:"100vh",background:T.bg}}>
//       <style>{CSS}</style>
//       {conn==="error"&&events.length===0
//         ? <ErrorScreen/>
//         : <>
//             <Header conn={conn} stats={stats}/>
//             <div style={{padding:"14px 18px",display:"flex",flexDirection:"column",gap:10}}>
//               <KpiRow stats={stats}/>

//               {/* Tab bar */}
//               <div style={{display:"flex",gap:0,borderBottom:`1px solid ${T.border}`}}>
//                 {[["threats","⚠ THREATS"],["logs","≡ EVENT LOG"]].map(([k,l])=>(
//                   <div key={k} className={`tab ${tab===k?"active":""}`} onClick={()=>setTab(k)}>{l}</div>
//                 ))}
//                 {conn==="error"&&(
//                   <div className="mono" style={{marginLeft:"auto",fontSize:9,color:T.orange,alignSelf:"center",padding:"0 8px"}}>
//                     ⚠ BACKEND UNREACHABLE – STALE DATA
//                   </div>
//                 )}
//               </div>

//               {tab==="threats"&&(
//                 <div style={{display:"grid",gridTemplateColumns:"1fr 290px",gap:10}}>
//                   <div style={{display:"flex",flexDirection:"column",gap:10}}>
//                     <ThreatTable events={events} selected={selected} onSelect={setSelected}
//                       filter={filter} setFilter={setFilter}/>
//                     <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
//                       <TrendChart events={events}/>
//                       <AttackChart stats={stats}/>
//                     </div>
//                     <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
//                       <Heatmap events={events} onSelect={setSelected}/>
//                       <GeoMatrix events={events}/>
//                     </div>
//                   </div>
//                   <InvestPanel ev={selected}/>
//                 </div>
//               )}

//               {tab==="logs"&&(
//                 <div className="panel">
//                   <div className="phdr">≡ Raw Event Log</div>
//                   <div style={{maxHeight:500,overflowY:"auto"}}>
//                     {[...events].reverse().map((ev,i)=>{
//                       const p=priority(ev.attack_probability);
//                       return (
//                         <div key={ev.id??i} className="mono" onClick={()=>{setSelected(ev);setTab("threats");}}
//                           style={{padding:"7px 14px",borderBottom:`1px solid ${T.line}`,
//                             fontSize:10,color:T.text,display:"flex",gap:16,cursor:"pointer"}}>
//                           <span style={{color:T.dimText,width:68,flexShrink:0}}>{fmt(ev.timestamp)}</span>
//                           <span style={{color:T.bright,width:120,flexShrink:0}}>{ev.src_ip}</span>
//                           <span style={{color:p.color,width:90,flexShrink:0}}>{ev.attack_type??"-"}</span>
//                           <span>
//                             P:<span style={{color:ev.packet_label==="attack"?T.red:T.green}}>{ev.packet_prob?.toFixed(2)}</span>{" "}
//                             F:<span style={{color:ev.flow_label==="attack"?T.red:T.green}}>{ev.flow_prob?.toFixed(2)}</span>{" "}
//                             B:<span style={{color:ev.behaviour_label==="attack"?T.red:T.green}}>{ev.behaviour_prob?.toFixed(2)}</span>
//                           </span>
//                           <span style={{marginLeft:"auto",color:p.color,fontWeight:700}}>
//                             {ev.label?.toUpperCase()} ({ev.attack_probability?.toFixed(3)})
//                           </span>
//                         </div>
//                       );
//                     })}
//                   </div>
//                 </div>
//               )}
//             </div>
//           </>
//       }
//     </div>
//   );
// }


// import { useCallback, useEffect, useRef, useState } from "react";
// import {
//   Area,
//   AreaChart,
//   Bar,
//   BarChart,
//   Cell,
//   PolarAngleAxis,
//   PolarGrid,
//   Radar,
//   RadarChart,
//   ResponsiveContainer,
//   Tooltip,
//   XAxis, YAxis
// } from "recharts";

// // ══════════════════════════════════════════════════════════════════════════════
// //  CONFIG
// // ══════════════════════════════════════════════════════════════════════════════
// const WS_URL  = "ws://127.0.0.1:8000/ws";
// const API_URL = "http://127.0.0.1:8000";
// const STATS_POLL_MS = 3000;

// // ══════════════════════════════════════════════════════════════════════════════
// //  DESIGN TOKENS
// // ══════════════════════════════════════════════════════════════════════════════
// const T = {
//   bg:"#030810",panel:"#06101e",border:"#0a1c30",line:"#07152a",
//   cyan:"#00d8ff",cyanDim:"#005a6b",cyanFaint:"rgba(0,216,255,0.06)",
//   green:"#00f0a0",orange:"#ff8c2f",red:"#ff2555",yellow:"#ffd000",
//   purple:"#b86fff",
//   text:"#6eacc8",bright:"#ddf4ff",dim:"#1a3448",dimText:"#304e65",
// };

// const PRI = p =>
//   p > 0.80 ? {l:"CRITICAL",c:T.red,   g:"rgba(255,37,85,0.35)"}  :
//   p > 0.60 ? {l:"HIGH",    c:T.orange, g:"rgba(255,140,47,0.3)"}  :
//   p > 0.40 ? {l:"MEDIUM",  c:T.yellow, g:"rgba(255,208,0,0.28)"}  :
//              {l:"LOW",     c:T.green,  g:"rgba(0,240,160,0.25)"};

// const fmtT  = ts => new Date(ts*1000).toLocaleTimeString("en-GB",{hour12:false});
// const fmtN  = n  => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"K" : String(n);

// // ══════════════════════════════════════════════════════════════════════════════
// //  GLOBAL CSS
// // ══════════════════════════════════════════════════════════════════════════════
// const CSS = `
// @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;500;700;900&display=swap');
// *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
// html,body,#root{height:100%;background:${T.bg};}
// body{color:${T.text};font-family:'Rajdhani',sans-serif;font-size:13px;overflow-x:hidden;}
// ::-webkit-scrollbar{width:3px;}::-webkit-scrollbar-track{background:${T.bg};}
// ::-webkit-scrollbar-thumb{background:${T.cyanDim};border-radius:2px;}
// .mono{font-family:'Share Tech Mono',monospace;}
// .raj{font-family:'Rajdhani',sans-serif;}
// .exo{font-family:'Exo 2',sans-serif;}

// /* scanlines */
// body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
//   background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.04) 2px,rgba(0,0,0,0.04) 4px);}

// /* animations */
// @keyframes pr{0%{transform:scale(.5);opacity:.9}100%{transform:scale(2.4);opacity:0}}
// @keyframes blink{0%,100%{opacity:1}50%{opacity:.08}}
// @keyframes sd{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
// @keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
// @keyframes sweep{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
// @keyframes flicker{0%,98%,100%{opacity:1}99%{opacity:.7}}
// @keyframes countup{from{opacity:0;transform:scale(.8)}to{opacity:1;transform:scale(1)}}

// .blink{animation:blink 2.8s step-end infinite;}
// .sd{animation:sd .2s ease forwards;}
// .pulse{animation:pulse 1.8s ease-in-out infinite;}
// .flicker{animation:flicker 6s ease infinite;}

// /* corner brackets */
// .brk{position:relative;}
// .brk::before,.brk::after{content:'';position:absolute;width:8px;height:8px;}
// .brk::before{top:0;left:0;border-top:1.5px solid ${T.cyan};border-left:1.5px solid ${T.cyan};}
// .brk::after{top:0;right:0;border-top:1.5px solid ${T.cyan};border-right:1.5px solid ${T.cyan};}

// /* panels */
// .panel{background:${T.panel};border:1px solid ${T.border};}
// .phdr{display:flex;align-items:center;gap:8px;padding:8px 14px;
//   border-bottom:1px solid ${T.border};background:rgba(0,216,255,0.02);
//   font-size:8px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
//   color:${T.cyan};font-family:'Share Tech Mono',monospace;}

// /* table rows */
// .tr{display:grid;align-items:center;padding:0 14px;height:36px;
//   border-bottom:1px solid ${T.line};cursor:pointer;transition:background .1s;}
// .tr:hover{background:rgba(0,216,255,0.035);}
// .tr.sel{background:rgba(0,216,255,0.06);border-left:2px solid ${T.cyan};}

// /* badge */
// .bdg{display:inline-flex;align-items:center;padding:1px 7px;border-radius:2px;
//   font-size:8px;font-weight:700;letter-spacing:.12em;font-family:'Share Tech Mono',monospace;}

// /* kpi */
// .kpi{background:${T.panel};border:1px solid ${T.border};
//   border-top:2.5px solid var(--c);padding:16px 18px;
//   position:relative;overflow:hidden;transition:border-color .3s;}
// .kpi::before{content:'';position:absolute;bottom:0;left:0;right:0;height:50%;
//   background:linear-gradient(to top,var(--cd,rgba(0,216,255,.03)),transparent);}

// /* sweep shimmer on kpi */
// .kpi::after{content:'';position:absolute;top:0;bottom:0;width:40%;
//   background:linear-gradient(90deg,transparent,rgba(255,255,255,.02),transparent);
//   animation:sweep 3s ease-in-out infinite;}

// /* buttons */
// .btn{padding:4px 11px;border:1px solid ${T.border};background:transparent;
//   color:${T.text};font-family:'Share Tech Mono',monospace;font-size:8px;
//   letter-spacing:.1em;cursor:pointer;transition:all .15s;}
// .btn:hover{border-color:${T.cyan};color:${T.cyan};background:${T.cyanFaint};}
// .btn.act{border-color:${T.cyan};color:${T.cyan};background:${T.cyanFaint};}
// .btn.red:hover{border-color:${T.red};color:${T.red};background:rgba(255,37,85,.05);}

// /* bar */
// .btr{height:4px;border-radius:2px;background:${T.dim}60;overflow:hidden;position:relative;}
// .bfill{height:100%;border-radius:2px;background:var(--c);
//   box-shadow:0 0 6px var(--c);transition:width .8s ease;}

// /* layer pill */
// .lpill{display:flex;align-items:center;gap:5px;padding:3px 8px;
//   border-radius:2px;font-size:9px;font-family:'Share Tech Mono',monospace;}

// /* connection line animation */
// @keyframes connLine{0%{opacity:.1;stroke-dashoffset:100}100%{opacity:.6;stroke-dashoffset:0}}
// `;

// // ══════════════════════════════════════════════════════════════════════════════
// //  WEBSOCKET HOOK
// // ══════════════════════════════════════════════════════════════════════════════
// function useWebSocket() {
//   const [events, setEvents]  = useState([]);
//   const [stats,  setStats]   = useState(null);
//   const [conn,   setConn]    = useState("connecting");
//   const [pkts,   setPkts]    = useState(0);
//   const [flows,  setFlows]   = useState(0);
//   const wsRef = useRef(null);

//   // Stats polling
//   const pollStats = useCallback(async () => {
//     try {
//       const r = await fetch(`${API_URL}/stats`);
//       if (!r.ok) throw new Error();
//       const s = await r.json();
//       setStats(s);
//       setPkts(s.packets_captured ?? 0);
//       setFlows(s.active_flows    ?? 0);
//     } catch {}
//   }, []);

//   // WebSocket connect
//   useEffect(() => {
//     const connect = () => {
//       try {
//         const ws = new WebSocket(WS_URL);
//         wsRef.current = ws;

//         ws.onopen    = () => { setConn("online"); pollStats(); };
//         ws.onclose   = () => {
//           setConn("reconnecting");
//           setTimeout(connect, 3000);
//         };
//         ws.onerror   = () => setConn("error");

//         ws.onmessage = (msg) => {
//           try {
//             const { type, data } = JSON.parse(msg.data);
//             if (type === "snapshot") {
//               setEvents(data || []);
//             } else if (type === "event") {
//               setEvents(prev => {
//                 const updated = [...prev, data];
//                 return updated.slice(-200);   // keep last 200
//               });
//             }
//           } catch {}
//         };
//       } catch {
//         setConn("error");
//         setTimeout(connect, 3000);
//       }
//     };
//     connect();
//     const pt = setInterval(pollStats, STATS_POLL_MS);
//     return () => {
//       clearInterval(pt);
//       wsRef.current?.close();
//     };
//   }, []);

//   return { events, stats, conn, pkts, flows };
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  ATOMS
// // ══════════════════════════════════════════════════════════════════════════════
// const ConnDot = ({s}) => {
//   const c = s==="online"?T.green : s==="error"?T.red : T.yellow;
//   return (
//     <div style={{position:"relative",width:8,height:8}}>
//       <div style={{width:8,height:8,borderRadius:"50%",background:c,
//         boxShadow:`0 0 6px ${c}`}}/>
//       <div className={s==="online"?"pulse":""} style={{
//         position:"absolute",inset:0,borderRadius:"50%",
//         border:`1px solid ${c}`,animation:s==="online"?"pr 1.6s ease-out infinite":undefined,
//       }}/>
//     </div>
//   );
// };

// const Badge = ({prob}) => {
//   const p=PRI(prob);
//   return <span className="bdg" style={{background:`${p.c}18`,color:p.c,border:`1px solid ${p.c}35`}}>{p.l}</span>;
// };

// const MiniBar = ({v,c}) => (
//   <div className="btr"><div className="bfill" style={{width:`${v*100}%`,"--c":c}}/></div>
// );

// const LayerPill = ({label, prob, model}) => {
//   const p = PRI(prob??0);
//   return (
//     <div className="lpill" style={{background:`${p.c}12`,border:`1px solid ${p.c}30`}}>
//       <div style={{width:5,height:5,borderRadius:"50%",background:p.c,
//         boxShadow:`0 0 5px ${p.c}`,flexShrink:0}}/>
//       <span style={{color:T.dimText,fontSize:8}}>{label}:</span>
//       <span style={{color:p.c}}>{prob?.toFixed(3)}</span>
//       <span className="bdg" style={{color:p.c,padding:"0 4px",fontSize:7}}>
//         {model?.split(" ")[0]}
//       </span>
//     </div>
//   );
// };

// // ══════════════════════════════════════════════════════════════════════════════
// //  HEADER
// // ══════════════════════════════════════════════════════════════════════════════
// function Header({conn, pkts, flows, stats}) {
//   const [clk, setClk] = useState(new Date());
//   useEffect(()=>{const t=setInterval(()=>setClk(new Date()),1000);return()=>clearInterval(t);},[]);

//   return (
//     <header style={{
//       position:"sticky",top:0,zIndex:300,height:50,padding:"0 20px",
//       display:"flex",alignItems:"center",justifyContent:"space-between",
//       background:`linear-gradient(180deg,#040c17 0%,${T.bg} 100%)`,
//       borderBottom:`1px solid ${T.border}`,
//     }}>
//       {/* logo */}
//       <div style={{display:"flex",alignItems:"center",gap:12}}>
//         <svg width="32" height="32" viewBox="0 0 32 32">
//           <defs>
//             <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
//               <stop offset="0%" stopColor={T.cyan}/>
//               <stop offset="100%" stopColor="#0044ff"/>
//             </linearGradient>
//           </defs>
//           <rect width="32" height="32" rx="4" fill="url(#lg)"/>
//           <text x="16" y="22" textAnchor="middle" fill="white"
//             style={{fontSize:16,fontFamily:"Exo 2",fontWeight:900}}>V</text>
//           <rect x="4" y="26" width="24" height="1" fill="white" opacity=".3"/>
//         </svg>
//         <div>
//           <div className="exo flicker" style={{fontSize:15,fontWeight:900,
//             letterSpacing:".08em",color:T.bright,lineHeight:1}}>
//             VECTRA <span style={{color:T.cyan}}>LIVE</span>
//           </div>
//           <div className="mono" style={{fontSize:7,letterSpacing:".22em",color:T.dimText,marginTop:1}}>
//             REAL-TIME AI THREAT DETECTION · 3-LAYER FUSION
//           </div>
//         </div>
//       </div>

//       {/* status row */}
//       <div className="mono" style={{display:"flex",gap:18,fontSize:10,color:T.text,alignItems:"center"}}>
//         <span style={{display:"flex",alignItems:"center",gap:7}}>
//           <ConnDot s={conn}/>
//           <span style={{color:conn==="online"?T.green:conn==="error"?T.red:T.yellow,fontSize:9,letterSpacing:".12em"}}>
//             {conn==="online"?"LIVE CAPTURE":conn==="reconnecting"?"RECONNECTING...":"OFFLINE"}
//           </span>
//         </span>
//         <span style={{color:T.dimText}}>│</span>
//         <span>PKTS <span style={{color:T.cyan}}>{fmtN(pkts)}</span></span>
//         <span style={{color:T.dimText}}>│</span>
//         <span>FLOWS <span style={{color:T.cyan}}>{flows}</span></span>
//         <span style={{color:T.dimText}}>│</span>
//         <span>ATTACKS <span style={{color:T.red}}>{stats?.attacks??0}</span></span>
//         <span style={{color:T.dimText}}>│</span>
//         <span>RATE <span style={{color:(stats?.attack_rate_pct??0)>50?T.red:T.cyan}}>{stats?.attack_rate_pct??0}%</span></span>
//         <span style={{color:T.dimText}}>│</span>
//         <span className="blink" style={{color:T.cyan}}>{clk.toLocaleTimeString("en-GB",{hour12:false})}</span>
//       </div>

//       <div style={{display:"flex",gap:8}}>
//         <button className="btn red" onClick={()=>fetch(`${API_URL}/events`,{method:"DELETE"})}>
//           ⊘ CLEAR
//         </button>
//         <button className="btn" onClick={()=>window.open(`${API_URL}/docs`,'_blank')}>
//           API DOCS
//         </button>
//       </div>
//     </header>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  LIVE PACKET COUNTER (animated)
// // ══════════════════════════════════════════════════════════════════════════════
// function LiveCounter({pkts, flows, stats}) {
//   const cards = [
//     {label:"Packets Captured", value:fmtN(pkts),       c:T.cyan,   icon:"◈", sub:"from WiFi interface"},
//     {label:"Active Flows",     value:flows,             c:T.purple, icon:"⇌", sub:`30s expiry window`},
//     {label:"Attacks Detected", value:stats?.attacks??0, c:T.red,    icon:"⚠", sub:`${stats?.attack_rate_pct??0}% of traffic`},
//     {label:"High Risk Events", value:stats?.high_risk??0,c:T.orange,icon:"◉", sub:"probability > 0.80"},
//   ];
//   return (
//     <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
//       {cards.map(({label,value,c,icon,sub})=>(
//         <div key={label} className="kpi brk" style={{"--c":c,"--cd":`${c}08`}}>
//           <div className="mono" style={{fontSize:7,letterSpacing:".2em",color:T.dimText,marginBottom:7}}>
//             {icon} {label.toUpperCase()}
//           </div>
//           <div className="exo" style={{fontSize:28,color:c,lineHeight:1,marginBottom:3,
//             textShadow:`0 0 20px ${c}55`,fontWeight:700,key:value}}>
//             {value}
//           </div>
//           <div style={{fontSize:10,color:T.text}}>{sub}</div>
//           <div style={{position:"absolute",right:14,top:"50%",transform:"translateY(-50%)",
//             fontSize:28,opacity:.04,color:c,fontFamily:"Share Tech Mono"}}>{icon}</div>
//         </div>
//       ))}
//     </div>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  3-LAYER PIPELINE VISUALIZER (eye-catcher for judges)
// // ══════════════════════════════════════════════════════════════════════════════
// function PipelineViz({ev}) {
//   if (!ev) return null;
//   const layers = [
//     {id:"PKT", name:"PACKET LAYER",    prob:ev.packet_prob,   label:ev.packet_label,
//      model:"Isolation Forest + Autoencoder", icon:"◉",
//      desc:"Inspects TCP flags, packet size, TTL, protocol anomalies"},
//     {id:"FLW", name:"FLOW LAYER",      prob:ev.flow_prob,     label:ev.flow_label,
//      model:"Deep Autoencoder",               icon:"⇌",
//      desc:"Analyses flow duration, bytes/s, IAT patterns, connection counts"},
//     {id:"BEH", name:"BEHAVIOUR LAYER", prob:ev.behaviour_prob,label:ev.behaviour_label,
//      model:"LSTM Autoencoder",               icon:"≋",
//      desc:"Temporal patterns per IP: burst rate, unique dsts, session timing"},
//   ];

//   const final = PRI(ev.attack_probability);

//   return (
//     <div className="panel" style={{padding:"14px 18px"}}>
//       <div className="mono" style={{fontSize:8,letterSpacing:".2em",color:T.dimText,marginBottom:12}}>
//         ▶ 3-LAYER DETECTION PIPELINE · IP {ev.src_ip} → {ev.dst_ip}:{ev.dst_port}
//       </div>

//       <div style={{display:"flex",alignItems:"stretch",gap:0}}>
//         {/* Input */}
//         <div style={{
//           background:T.line,border:`1px solid ${T.border}`,padding:"10px 14px",
//           borderRadius:"2px 0 0 2px",minWidth:90,display:"flex",flexDirection:"column",
//           alignItems:"center",justifyContent:"center",gap:4,
//         }}>
//           <div style={{fontSize:18,color:T.dimText}}>📡</div>
//           <div className="mono" style={{fontSize:7,color:T.dimText,textAlign:"center",letterSpacing:".1em"}}>
//             LIVE<br/>PACKET
//           </div>
//           <div className="mono" style={{fontSize:9,color:T.cyan}}>{ev.proto}</div>
//         </div>

//         {/* Arrow */}
//         <div style={{display:"flex",alignItems:"center",padding:"0 4px"}}>
//           <div style={{width:20,height:1,background:T.cyan,opacity:.4}}/>
//           <div style={{width:0,height:0,borderTop:"4px solid transparent",
//             borderBottom:"4px solid transparent",borderLeft:`6px solid ${T.cyanDim}`}}/>
//         </div>

//         {/* Layers */}
//         {layers.map((layer, idx) => {
//           const p = PRI(layer.prob??0);
//           return (
//             <div key={layer.id} style={{display:"flex",alignItems:"stretch",gap:0}}>
//               <div style={{
//                 background:`${p.c}0c`,border:`1px solid ${p.c}30`,padding:"10px 14px",
//                 minWidth:170,display:"flex",flexDirection:"column",gap:5,
//                 borderRadius:idx===layers.length-1?"0":"0",
//               }}>
//                 <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
//                   <div className="mono" style={{fontSize:8,color:p.c,letterSpacing:".1em",fontWeight:700}}>
//                     LAYER {idx+1}: {layer.name}
//                   </div>
//                   <span className="bdg" style={{
//                     background:`${p.c}20`,color:p.c,border:`1px solid ${p.c}35`,fontSize:7}}>
//                     {layer.label?.toUpperCase()}
//                   </span>
//                 </div>
//                 <div style={{fontSize:8,color:T.dimText}}>{layer.model}</div>
//                 <div className="btr" style={{height:5}}>
//                   <div className="bfill" style={{width:`${(layer.prob??0)*100}%`,"--c":p.c}}/>
//                 </div>
//                 <div style={{display:"flex",justifyContent:"space-between"}}>
//                   <span style={{fontSize:8,color:T.text}}>{layer.desc.slice(0,40)}…</span>
//                   <span className="mono" style={{fontSize:11,color:p.c,fontWeight:700}}>
//                     {layer.prob?.toFixed(3)}
//                   </span>
//                 </div>
//               </div>

//               {idx < layers.length-1 && (
//                 <div style={{display:"flex",alignItems:"center",padding:"0 4px"}}>
//                   <div style={{width:16,height:1,background:T.cyan,opacity:.4}}/>
//                   <div style={{width:0,height:0,borderTop:"4px solid transparent",
//                     borderBottom:"4px solid transparent",borderLeft:`6px solid ${T.cyanDim}`}}/>
//                 </div>
//               )}
//             </div>
//           );
//         })}

//         {/* Fusion */}
//         <div style={{display:"flex",alignItems:"center",padding:"0 4px"}}>
//           <div style={{width:16,height:1,background:T.cyan,opacity:.4}}/>
//           <div style={{width:0,height:0,borderTop:"4px solid transparent",
//             borderBottom:"4px solid transparent",borderLeft:`6px solid ${T.cyanDim}`}}/>
//         </div>

//         <div style={{
//           background:`${final.c}12`,border:`1px solid ${final.c}40`,
//           padding:"10px 16px",minWidth:130,display:"flex",flexDirection:"column",
//           alignItems:"center",justifyContent:"center",gap:4,borderRadius:"0 2px 2px 0",
//         }}>
//           <div className="mono" style={{fontSize:7,color:T.dimText,letterSpacing:".15em"}}>
//             FUSION ENGINE
//           </div>
//           <div className="mono" style={{fontSize:8,color:T.dimText,letterSpacing:".1em",marginTop:2}}>
//             MAJORITY VOTE (2/3)
//           </div>
//           <div className="exo" style={{fontSize:20,color:final.c,fontWeight:900,
//             textShadow:`0 0 15px ${final.g}`}}>
//             {ev.label?.toUpperCase()}
//           </div>
//           <div className="mono" style={{fontSize:22,color:T.bright,lineHeight:1}}>
//             {ev.attack_probability?.toFixed(3)}
//           </div>
//           <span className="bdg" style={{background:`${final.c}20`,color:final.c,
//             border:`1px solid ${final.c}40`,marginTop:2}}>{final.l}</span>
//         </div>
//       </div>
//     </div>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  THREAT TABLE
// // ══════════════════════════════════════════════════════════════════════════════
// const GC = "90px 1fr 1fr 90px 90px 90px 110px 68px";
// const CH = ["PRIORITY","SRC IP","DST IP:PORT","PROTO","TYPE","LAYERS","SCORE","TIME"];

// function ThreatTable({events, selected, onSelect, filter, setFilter}) {
//   const sorted   = [...events].sort((a,b)=>b.attack_probability-a.attack_probability);
//   const filtered = filter==="all"?sorted:filter==="attack"?sorted.filter(e=>e.label==="attack"):sorted.filter(e=>e.label==="normal");

//   return (
//     <div className="panel" style={{flex:1}}>
//       <div className="phdr">
//         <div className="pulse" style={{width:6,height:6,borderRadius:"50%",
//           background:T.red,boxShadow:`0 0 6px ${T.red}`}}/>
//         Live Detections
//         <span className="mono" style={{fontSize:7,color:T.dimText,marginLeft:4}}>
//           (WebSocket · auto-refresh)
//         </span>
//         <div style={{marginLeft:"auto",display:"flex",gap:5}}>
//           {["all","attack","normal"].map(f=>(
//             <button key={f} className={`btn ${filter===f?"act":""}`} onClick={()=>setFilter(f)}>
//               {f.toUpperCase()}
//             </button>
//           ))}
//         </div>
//         <span className="mono" style={{color:T.cyan,fontSize:9,marginLeft:8}}>{filtered.length}</span>
//       </div>

//       <div className="mono" style={{display:"grid",gridTemplateColumns:GC,
//         padding:"0 14px",height:26,alignItems:"center",
//         borderBottom:`1px solid ${T.border}`,fontSize:7,letterSpacing:".15em",color:T.dimText}}>
//         {CH.map(c=><div key={c}>{c}</div>)}
//       </div>

//       <div style={{maxHeight:320,overflowY:"auto"}}>
//         {filtered.slice(0,30).map((ev,i)=>{
//           const p=PRI(ev.attack_probability);
//           return (
//             <div key={ev.id??i}
//               className={`tr sd mono ${selected?.id===ev.id?"sel":""}`}
//               style={{gridTemplateColumns:GC,"animationDelay":`${i*.02}s`}}
//               onClick={()=>onSelect(ev)}>
//               <Badge prob={ev.attack_probability}/>
//               <span style={{color:T.bright,fontSize:11}}>{ev.src_ip}</span>
//               <span style={{color:T.text,fontSize:10}}>{ev.dst_ip}:{ev.dst_port}</span>
//               <span style={{color:T.dimText,fontSize:10}}>{ev.proto}</span>
//               <span style={{color:p.c,fontSize:9}}>{ev.attack_type??"-"}</span>
//               {/* Layer indicators */}
//               <span style={{display:"flex",gap:3,alignItems:"center"}}>
//                 {[ev.packet_label,ev.flow_label,ev.behaviour_label].map((lbl,j)=>(
//                   <div key={j} title={["PKT","FLW","BEH"][j]}
//                     style={{width:6,height:6,borderRadius:"50%",
//                       background:lbl==="attack"?T.red:T.green,
//                       boxShadow:`0 0 4px ${lbl==="attack"?T.red:T.green}`}}/>
//                 ))}
//               </span>
//               <div>
//                 <div style={{fontSize:11,color:p.c,marginBottom:2}}>
//                   {ev.attack_probability?.toFixed(3)}
//                 </div>
//                 <MiniBar v={ev.attack_probability} c={p.c}/>
//               </div>
//               <span style={{color:T.dimText,fontSize:9}}>{fmtT(ev.timestamp)}</span>
//             </div>
//           );
//         })}
//       </div>
//     </div>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  INVESTIGATION PANEL
// // ══════════════════════════════════════════════════════════════════════════════
// function InvestPanel({ev}) {
//   if(!ev) return (
//     <div className="panel" style={{flex:1,display:"flex",alignItems:"center",
//       justifyContent:"center",flexDirection:"column",gap:8,color:T.dimText}}>
//       <div style={{fontSize:28}}>◎</div>
//       <div className="mono" style={{fontSize:9,letterSpacing:".14em"}}>SELECT EVENT</div>
//     </div>
//   );

//   const p=PRI(ev.attack_probability);
//   const layers=[
//     {name:"PKT",  full:"PACKET LAYER",   label:ev.packet_label,   prob:ev.packet_prob,   model:ev.packet_model},
//     {name:"FLW",  full:"FLOW LAYER",     label:ev.flow_label,     prob:ev.flow_prob,     model:ev.flow_model},
//     {name:"BEH",  full:"BEHAVIOUR",      label:ev.behaviour_label,prob:ev.behaviour_prob,model:ev.behaviour_model},
//   ];
//   const radar=layers.map(l=>({s:l.name,v:+((l.prob??0)*100).toFixed(1)}));

//   return (
//     <div className="panel" style={{flex:1,display:"flex",flexDirection:"column",minWidth:0}}>
//       <div className="phdr"><span>⊕</span> Investigate
//         <span className="mono" style={{marginLeft:"auto",color:T.dimText,fontSize:8}}>#{ev.id}</span>
//       </div>

//       {/* Verdict */}
//       <div style={{padding:"14px 16px",borderBottom:`1px solid ${T.border}`,
//         background:`linear-gradient(135deg,${p.c}0b,transparent 60%)`}}>
//         <div className="mono" style={{fontSize:7,letterSpacing:".2em",color:T.dimText,marginBottom:4}}>
//           FUSION RESULT · MAJORITY VOTE · {ev.proto}
//         </div>
//         <div className="exo" style={{fontSize:18,fontWeight:900,color:p.c,
//           textShadow:`0 0 16px ${p.g}`}}>{ev.label?.toUpperCase()}</div>
//         <div className="exo" style={{fontSize:24,color:T.bright,lineHeight:1.1}}>
//           {ev.attack_probability?.toFixed(3)}
//           <span style={{fontFamily:"Rajdhani",fontSize:11,color:T.text,marginLeft:6}}>confidence</span>
//         </div>
//         <div className="mono" style={{marginTop:8,display:"flex",gap:12,
//           fontSize:9,color:T.text,flexWrap:"wrap"}}>
//           <span>{ev.src_ip} → {ev.dst_ip}:{ev.dst_port}</span>
//           <span style={{color:p.c}}>{ev.attack_type}</span>
//         </div>
//         <div className="mono" style={{marginTop:4,display:"flex",gap:12,
//           fontSize:9,color:T.dimText}}>
//           <span>PKTS:{ev.pkt_count}</span>
//           <span>BYTES:{fmtN(ev.flow_bytes??0)}</span>
//           <span>BPS:{fmtN(ev.bytes_per_s??0)}</span>
//           <span>SYN:{ev.syn_cnt??0}</span>
//           <span>RST:{ev.rst_cnt??0}</span>
//         </div>
//       </div>

//       {/* Radar */}
//       <div style={{padding:"4px 0",borderBottom:`1px solid ${T.border}`}}>
//         <ResponsiveContainer width="100%" height={90}>
//           <RadarChart data={radar.map(r=>({subject:r.s,score:r.v}))} margin={{top:4,right:16,bottom:4,left:16}}>
//             <PolarGrid stroke={T.dim} strokeOpacity={.5}/>
//             <PolarAngleAxis dataKey="subject"
//               tick={{fill:T.text,fontSize:9,fontFamily:"Share Tech Mono"}}/>
//             <Radar dataKey="score" stroke={p.c} fill={p.c} fillOpacity={.16} strokeWidth={1.5}/>
//           </RadarChart>
//         </ResponsiveContainer>
//       </div>

//       {/* Layer breakdown */}
//       <div style={{padding:"12px 16px",display:"flex",flexDirection:"column",gap:11,flex:1}}>
//         <div className="mono" style={{fontSize:7,letterSpacing:".2em",color:T.dimText}}>DETECTION LAYERS</div>
//         {layers.map(l=>{
//           const lp=PRI(l.prob??0);
//           return (
//             <div key={l.name}>
//               <div style={{display:"flex",justifyContent:"space-between",marginBottom:3,alignItems:"flex-end"}}>
//                 <div>
//                   <div className="mono" style={{fontSize:9,color:T.text,letterSpacing:".08em"}}>{l.full}</div>
//                   <div style={{fontSize:8,color:T.dimText}}>{l.model}</div>
//                 </div>
//                 <div style={{display:"flex",gap:6,alignItems:"center"}}>
//                   <span className="mono" style={{fontSize:11,color:lp.c}}>{l.prob?.toFixed(3)}</span>
//                   <span className="bdg" style={{background:`${lp.c}18`,color:lp.c,
//                     border:`1px solid ${lp.c}30`,fontSize:7}}>{l.label?.toUpperCase()}</span>
//                 </div>
//               </div>
//               <div style={{background:`${T.dim}30`,borderRadius:2,height:5,overflow:"hidden"}}>
//                 <div style={{height:"100%",width:`${(l.prob??0)*100}%`,borderRadius:2,
//                   background:`linear-gradient(90deg,${lp.c}60,${lp.c})`,
//                   boxShadow:`0 0 8px ${lp.c}88`,transition:"width 1s ease"}}/>
//               </div>
//             </div>
//           );
//         })}
//       </div>

//       {/* Actions */}
//       <div style={{borderTop:`1px solid ${T.border}`,padding:"9px 14px",display:"flex",gap:5}}>
//         {["BLOCK IP","TRACE","QUARANTINE","WHITELIST"].map(a=>(
//           <button key={a} className="btn" style={{flex:1,textAlign:"center",fontSize:7}}>{a}</button>
//         ))}
//       </div>
//     </div>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  CHARTS
// // ══════════════════════════════════════════════════════════════════════════════
// function TrendChart({events}) {
//   const data = events
//     .sort((a,b)=>a.timestamp-b.timestamp)
//     .reduce((acc,ev)=>{
//       const b=Math.floor(ev.timestamp/5)*5;
//       const ex=acc.find(x=>x.t===b);
//       if(ex){ex.a.push(ev.attack_probability);}
//       else{acc.push({t:b,a:[ev.attack_probability]});}
//       return acc;
//     },[])
//     .slice(-30)
//     .map(({t,a})=>({
//       time:fmtT(t),
//       avg:+(a.reduce((x,y)=>x+y,0)/a.length).toFixed(3),
//       peak:+Math.max(...a).toFixed(3),
//     }));

//   const Tip=({active,payload})=>{
//     if(!active||!payload?.length) return null;
//     return <div style={{background:"#030b14",border:`1px solid #0a2840`,
//       padding:"5px 10px",fontFamily:"Share Tech Mono",fontSize:10,color:T.bright}}>
//       <div style={{color:T.dimText,fontSize:8,marginBottom:2}}>{payload[0]?.payload?.time}</div>
//       <div>AVG <span style={{color:T.cyan}}>{payload[0]?.value}</span></div>
//       {payload[1]&&<div>PEAK <span style={{color:T.red}}>{payload[1]?.value}</span></div>}
//     </div>;
//   };

//   return (
//     <div className="panel">
//       <div className="phdr">▲ Threat Score Trend (5s buckets)</div>
//       <div style={{padding:"10px 8px 6px"}}>
//         <ResponsiveContainer width="100%" height={100}>
//           <AreaChart data={data} margin={{top:4,right:14,bottom:0,left:0}}>
//             <defs>
//               <linearGradient id="gA" x1="0" y1="0" x2="0" y2="1">
//                 <stop offset="5%" stopColor={T.cyan} stopOpacity={.25}/>
//                 <stop offset="95%" stopColor={T.cyan} stopOpacity={0}/>
//               </linearGradient>
//               <linearGradient id="gB" x1="0" y1="0" x2="0" y2="1">
//                 <stop offset="5%" stopColor={T.red} stopOpacity={.2}/>
//                 <stop offset="95%" stopColor={T.red} stopOpacity={0}/>
//               </linearGradient>
//             </defs>
//             <XAxis dataKey="time" tick={{fill:T.dimText,fontSize:8,fontFamily:"Share Tech Mono"}}
//               axisLine={false} tickLine={false}/>
//             <YAxis domain={[0,1]} tick={{fill:T.dimText,fontSize:8}} axisLine={false} tickLine={false} width={26}/>
//             <Tooltip content={<Tip/>} cursor={{stroke:`${T.cyan}25`,strokeWidth:1}}/>
//             <Area type="monotone" dataKey="avg" stroke={T.cyan} strokeWidth={1.5}
//               fill="url(#gA)" dot={false} activeDot={{r:3,fill:T.cyan}}/>
//             <Area type="monotone" dataKey="peak" stroke={T.red} strokeWidth={1}
//               fill="url(#gB)" dot={false} activeDot={{r:3,fill:T.red}}/>
//           </AreaChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }

// function AttackChart({stats}) {
//   if(!stats?.attack_types) return null;
//   const data=Object.entries(stats.attack_types).map(([n,c])=>({n,c})).sort((a,b)=>b.c-a.c).slice(0,6);
//   const CS=[T.red,T.orange,T.yellow,T.cyan,T.green,T.purple];
//   return (
//     <div className="panel">
//       <div className="phdr">▦ Attack Classification</div>
//       <div style={{padding:"10px 8px 6px"}}>
//         <ResponsiveContainer width="100%" height={100}>
//           <BarChart data={data} margin={{top:4,right:14,bottom:0,left:0}}>
//             <XAxis dataKey="n" tick={{fill:T.dimText,fontSize:7,fontFamily:"Share Tech Mono"}}
//               axisLine={false} tickLine={false}/>
//             <YAxis tick={{fill:T.dimText,fontSize:7}} axisLine={false} tickLine={false} width={22}/>
//             <Tooltip
//               contentStyle={{background:"#030b14",border:`1px solid #0a2840`,
//                 fontFamily:"Share Tech Mono",fontSize:10,color:T.bright}}/>
//             <Bar dataKey="c" radius={[2,2,0,0]}>
//               {data.map((_,i)=><Cell key={i} fill={CS[i%CS.length]} opacity={.85}/>)}
//             </Bar>
//           </BarChart>
//         </ResponsiveContainer>
//       </div>
//     </div>
//   );
// }

// function ProtoChart({stats}) {
//   if(!stats?.proto_dist) return null;
//   const data=Object.entries(stats.proto_dist).map(([n,c])=>({n,c}));
//   const CS={TCP:T.cyan,UDP:T.purple,ICMP:T.orange,OTHER:T.dimText};
//   return (
//     <div className="panel">
//       <div className="phdr">⇌ Protocol Distribution</div>
//       <div style={{padding:"10px 16px",display:"flex",flexDirection:"column",gap:6}}>
//         {data.map(({n,c})=>{
//           const total=data.reduce((a,b)=>a+b.c,0);
//           const pct=total>0?c/total:0;
//           const col=CS[n]||T.text;
//           return (
//             <div key={n}>
//               <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
//                 <span className="mono" style={{fontSize:9,color:col}}>{n}</span>
//                 <span className="mono" style={{fontSize:9,color:T.text}}>
//                   {c} <span style={{color:T.dimText}}>({(pct*100).toFixed(0)}%)</span>
//                 </span>
//               </div>
//               <MiniBar v={pct} c={col}/>
//             </div>
//           );
//         })}
//       </div>
//     </div>
//   );
// }

// function Heatmap({events, onSelect}) {
//   const last=events.slice(-60);
//   return (
//     <div className="panel">
//       <div className="phdr">◈ Risk Heatmap · Last 60</div>
//       <div style={{padding:"10px 14px",display:"grid",gridTemplateColumns:"repeat(12,1fr)",gap:3}}>
//         {last.map((ev,i)=>{
//           const p=PRI(ev.attack_probability);
//           return <div key={i} onClick={()=>onSelect(ev)}
//             title={`${ev.src_ip} | ${ev.attack_probability}`}
//             style={{height:14,borderRadius:2,cursor:"pointer",background:p.c,
//               opacity:.3+ev.attack_probability*.7,transition:"opacity .15s,transform .1s"}}
//             onMouseEnter={e=>{e.target.style.opacity=1;e.target.style.transform="scaleY(1.4)";}}
//             onMouseLeave={e=>{e.target.style.opacity=.3+ev.attack_probability*.7;e.target.style.transform="";}}
//           />;
//         })}
//       </div>
//       <div className="mono" style={{padding:"2px 14px 9px",display:"flex",gap:12,fontSize:7,color:T.dimText}}>
//         <span style={{color:T.green}}>■ LOW</span>
//         <span style={{color:T.yellow}}>■ MED</span>
//         <span style={{color:T.orange}}>■ HIGH</span>
//         <span style={{color:T.red}}>■ CRIT</span>
//       </div>
//     </div>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  OFFLINE SCREEN
// // ══════════════════════════════════════════════════════════════════════════════
// function Offline() {
//   return (
//     <div style={{minHeight:"100vh",display:"flex",alignItems:"center",
//       justifyContent:"center",flexDirection:"column",gap:16}}>
//       <div className="exo" style={{fontSize:52,color:T.red,textShadow:`0 0 30px ${T.red}`}}>⊗</div>
//       <div className="exo" style={{fontSize:18,color:T.red,letterSpacing:".1em"}}>BACKEND OFFLINE</div>
//       <div className="mono" style={{fontSize:11,color:T.text,textAlign:"center",lineHeight:1.8}}>
//         WebSocket: <span style={{color:T.cyan}}>{WS_URL}</span> unreachable<br/>
//         Start the backend as Administrator/root:
//       </div>
//       <div style={{background:T.panel,border:`1px solid ${T.border}`,padding:"14px 22px",
//         fontFamily:"Share Tech Mono",fontSize:11,color:T.cyan,borderLeft:`3px solid ${T.cyan}`}}>
//         <div style={{color:T.dimText,fontSize:9,marginBottom:6}}># Windows (Run as Admin)</div>
//         python live_capture_backend.py<br/>
//         <div style={{color:T.dimText,fontSize:9,marginTop:8,marginBottom:4}}># Linux / Mac</div>
//         sudo python live_capture_backend.py
//       </div>
//       <div className="mono" style={{fontSize:9,color:T.dimText}}>
//         Retrying WebSocket every 3 seconds…
//       </div>
//     </div>
//   );
// }

// // ══════════════════════════════════════════════════════════════════════════════
// //  ROOT APP
// // ══════════════════════════════════════════════════════════════════════════════
// export default function App() {
//   const {events, stats, conn, pkts, flows} = useWebSocket();
//   const [selected, setSelected] = useState(null);
//   const [filter,   setFilter]   = useState("all");
//   const [tab,      setTab]      = useState("live");   // live | pipeline | log

//   // Auto-select most dangerous live event
//   useEffect(()=>{
//     if(events.length){
//       const top=[...events].sort((a,b)=>b.attack_probability-a.attack_probability)[0];
//       setSelected(prev => prev?.id===top?.id ? prev : top);
//     }
//   },[events.length]);

//   const isOffline = conn==="error" && events.length===0;

//   return (
//     <div style={{minHeight:"100vh",background:T.bg}}>
//       <style>{CSS}</style>
//       {isOffline ? <Offline/> : (
//         <>
//           <Header conn={conn} pkts={pkts} flows={flows} stats={stats}/>

//           <div style={{padding:"12px 18px",display:"flex",flexDirection:"column",gap:10}}>

//             {/* KPI row */}
//             <LiveCounter pkts={pkts} flows={flows} stats={stats}/>

//             {/* Tabs */}
//             <div style={{display:"flex",gap:0,borderBottom:`1px solid ${T.border}`}}>
//               {[
//                 ["live",     "◉ LIVE MONITOR"],
//                 ["pipeline", "⇌ 3-LAYER PIPELINE"],
//                 ["log",      "≡ EVENT LOG"],
//               ].map(([k,l])=>(
//                 <div key={k}
//                   style={{padding:"6px 14px",fontSize:8,fontWeight:600,letterSpacing:".18em",
//                     cursor:"pointer",borderBottom:`2px solid ${tab===k?T.cyan:"transparent"}`,
//                     color:tab===k?T.cyan:T.dimText,transition:"all .15s",
//                     fontFamily:"Share Tech Mono"}}
//                   onClick={()=>setTab(k)}>{l}</div>
//               ))}
//               {conn==="reconnecting"&&(
//                 <div className="mono blink" style={{marginLeft:"auto",alignSelf:"center",
//                   fontSize:8,color:T.yellow,padding:"0 10px"}}>
//                   ⚠ RECONNECTING…
//                 </div>
//               )}
//             </div>

//             {/* ── LIVE MONITOR ── */}
//             {tab==="live" && (
//               <div style={{display:"grid",gridTemplateColumns:"1fr 280px",gap:10}}>
//                 <div style={{display:"flex",flexDirection:"column",gap:10}}>
//                   <ThreatTable events={events} selected={selected}
//                     onSelect={setSelected} filter={filter} setFilter={setFilter}/>
//                   <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10}}>
//                     <TrendChart events={events}/>
//                     <AttackChart stats={stats}/>
//                     <ProtoChart stats={stats}/>
//                   </div>
//                   <Heatmap events={events} onSelect={ev=>{setSelected(ev);setTab("pipeline");}}/>
//                 </div>
//                 <InvestPanel ev={selected}/>
//               </div>
//             )}

//             {/* ── 3-LAYER PIPELINE ── */}
//             {tab==="pipeline" && (
//               <div style={{display:"flex",flexDirection:"column",gap:10}}>
//                 <div className="panel" style={{padding:"14px 18px",
//                   background:`linear-gradient(135deg,rgba(0,100,120,.08),transparent)`}}>
//                   <div className="exo" style={{fontSize:18,color:T.bright,marginBottom:4,fontWeight:700}}>
//                     3-Layer Detection Pipeline
//                   </div>
//                   <div style={{fontSize:11,color:T.text,lineHeight:1.7,maxWidth:700}}>
//                     Every captured packet flows through <span style={{color:T.cyan}}>three independent ML models</span>.
//                     The <span style={{color:T.purple}}>Fusion Engine</span> applies <strong>majority voting</strong> (eq. 1 from the paper)
//                     — a final ATTACK alert fires only when ≥2 layers agree.
//                     This eliminates false positives that fool single-layer systems.
//                   </div>
//                 </div>

//                 {/* Show pipeline for selected event */}
//                 {selected ? (
//                   <PipelineViz ev={selected}/>
//                 ) : (
//                   <div className="panel" style={{padding:30,textAlign:"center",color:T.dimText}}>
//                     <div className="mono" style={{fontSize:10}}>SELECT AN EVENT FROM THE LIVE MONITOR TAB TO SEE ITS PIPELINE</div>
//                   </div>
//                 )}

//                 {/* Last 5 events pipeline */}
//                 <div className="panel">
//                   <div className="phdr">≡ Recent Events — Click to Inspect Pipeline</div>
//                   <div style={{maxHeight:320,overflowY:"auto"}}>
//                     {[...events].sort((a,b)=>b.timestamp-a.timestamp).slice(0,15).map((ev,i)=>{
//                       const p=PRI(ev.attack_probability);
//                       return (
//                         <div key={ev.id??i} onClick={()=>setSelected(ev)}
//                           className="tr mono" style={{
//                             display:"grid",
//                             gridTemplateColumns:"90px 120px 100px 1fr 1fr 1fr 100px",
//                             cursor:"pointer",
//                             background:selected?.id===ev.id?`${T.cyanFaint}`:undefined}}>
//                           <Badge prob={ev.attack_probability}/>
//                           <span style={{color:T.bright,fontSize:11}}>{ev.src_ip}</span>
//                           <span style={{color:T.dimText,fontSize:10}}>{ev.proto}</span>
//                           <div style={{display:"flex",alignItems:"center",gap:4}}>
//                             <div style={{width:5,height:5,borderRadius:"50%",
//                               background:PRI(ev.packet_prob??0).c}}/>
//                             <span style={{fontSize:9,color:T.dimText}}>PKT</span>
//                             <span style={{color:PRI(ev.packet_prob??0).c,fontSize:9}}>
//                               {ev.packet_prob?.toFixed(2)}
//                             </span>
//                           </div>
//                           <div style={{display:"flex",alignItems:"center",gap:4}}>
//                             <div style={{width:5,height:5,borderRadius:"50%",
//                               background:PRI(ev.flow_prob??0).c}}/>
//                             <span style={{fontSize:9,color:T.dimText}}>FLW</span>
//                             <span style={{color:PRI(ev.flow_prob??0).c,fontSize:9}}>
//                               {ev.flow_prob?.toFixed(2)}
//                             </span>
//                           </div>
//                           <div style={{display:"flex",alignItems:"center",gap:4}}>
//                             <div style={{width:5,height:5,borderRadius:"50%",
//                               background:PRI(ev.behaviour_prob??0).c}}/>
//                             <span style={{fontSize:9,color:T.dimText}}>BEH</span>
//                             <span style={{color:PRI(ev.behaviour_prob??0).c,fontSize:9}}>
//                               {ev.behaviour_prob?.toFixed(2)}
//                             </span>
//                           </div>
//                           <span style={{color:p.c,fontWeight:700,fontSize:10}}>
//                             {ev.label?.toUpperCase()} ({ev.attack_probability?.toFixed(3)})
//                           </span>
//                         </div>
//                       );
//                     })}
//                   </div>
//                 </div>
//               </div>
//             )}

//             {/* ── EVENT LOG ── */}
//             {tab==="log" && (
//               <div className="panel">
//                 <div className="phdr">≡ Raw Event Log
//                   <span className="mono" style={{marginLeft:"auto",color:T.dimText,fontSize:8}}>
//                     {events.length} EVENTS IN BUFFER
//                   </span>
//                 </div>
//                 <div style={{maxHeight:600,overflowY:"auto"}}>
//                   {[...events].reverse().map((ev,i)=>{
//                     const p=PRI(ev.attack_probability);
//                     return (
//                       <div key={ev.id??i} className="mono"
//                         onClick={()=>{setSelected(ev);setTab("pipeline");}}
//                         style={{padding:"6px 14px",borderBottom:`1px solid ${T.line}`,
//                           fontSize:9,color:T.text,display:"flex",gap:14,cursor:"pointer"}}>
//                         <span style={{color:T.dimText,width:65,flexShrink:0}}>{fmtT(ev.timestamp)}</span>
//                         <span style={{color:T.bright,width:115,flexShrink:0}}>{ev.src_ip}</span>
//                         <span style={{color:T.dimText,width:80,flexShrink:0}}>{ev.proto} :{ev.dst_port}</span>
//                         <span style={{color:p.c,width:130,flexShrink:0}}>{ev.attack_type}</span>
//                         <span style={{color:T.dimText}}>
//                           P:<span style={{color:PRI(ev.packet_prob??0).c}}>{ev.packet_prob?.toFixed(2)}</span>{" "}
//                           F:<span style={{color:PRI(ev.flow_prob??0).c}}>{ev.flow_prob?.toFixed(2)}</span>{" "}
//                           B:<span style={{color:PRI(ev.behaviour_prob??0).c}}>{ev.behaviour_prob?.toFixed(2)}</span>
//                         </span>
//                         <span style={{marginLeft:"auto",color:p.c,fontWeight:700}}>
//                           {ev.label?.toUpperCase()} {ev.attack_probability?.toFixed(3)}
//                         </span>
//                       </div>
//                     );
//                   })}
//                 </div>
//               </div>
//             )}

//           </div>
//         </>
//       )}
//     </div>
//   );
// }



import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis, YAxis
} from "recharts";

// ─── API config (same as your Streamlit) ──────────────────────────────────────
const API_BASE   = "http://127.0.0.1:8000";
const REFRESH_MS = 1000;   // matches Streamlit REFRESH_SECONDS = 1.0
const MAX_ROWS   = 150;    // matches Streamlit MAX_ROWS = 150

// ─── Design tokens ────────────────────────────────────────────────────────────
const C = {
  bg:       "#030a12",
  panel:    "#060e1a",
  panelHi:  "#091422",
  border:   "#0c1f34",
  line:     "#081629",
  cyan:     "#00e5ff",
  cyanGlow: "rgba(0,229,255,0.18)",
  green:    "#00f5a0",
  red:      "#ff2d55",
  orange:   "#ff8c00",
  yellow:   "#ffd60a",
  purple:   "#bf5af2",
  text:     "#5fa8c8",
  bright:   "#dff4ff",
  dim:      "#152a3d",
  dimTxt:   "#2c4d66",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmtTime = ts => new Date(ts * 1000).toLocaleTimeString("en-GB", { hour12: false });
const fmtNum  = n  => n == null ? "—" : typeof n === "number" ? n.toFixed(4) : n;
const fmtKB   = n  => n == null ? "—" : n > 1e6 ? (n/1e6).toFixed(2)+"M" : n > 1e3 ? (n/1e3).toFixed(1)+"K" : n.toFixed(1);

const riskOf = label => label === "attack" ? {c:C.red, glow:"rgba(255,45,85,0.4)", lbl:"ATTACK"} : {c:C.green, glow:"rgba(0,245,160,0.3)", lbl:"NORMAL"};

// ─── Global CSS ────────────────────────────────────────────────────────────────
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600&family=Barlow+Condensed:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #root { height: 100%; }
body {
  background: ${C.bg};
  color: ${C.text};
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 14px;
  overflow-x: hidden;
}

::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: ${C.bg}; }
::-webkit-scrollbar-thumb { background: #0a3a55; border-radius: 2px; }

.mono  { font-family: 'JetBrains Mono', monospace; }
.orb   { font-family: 'Orbitron', monospace; }
.cond  { font-family: 'Barlow Condensed', sans-serif; }

/* Scanlines */
body::after {
  content: '';
  position: fixed; inset: 0;
  pointer-events: none; z-index: 9998;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
  );
}

/* ── Animations ── */
@keyframes pulse-ring {
  0%   { transform: scale(0.6); opacity: 0.9; }
  100% { transform: scale(2.6); opacity: 0; }
}
@keyframes blink  { 0%,100%{opacity:1} 50%{opacity:0.1} }
@keyframes fadein { from{opacity:0;transform:translateY(-5px)} to{opacity:1;transform:translateY(0)} }
@keyframes flow-beam {
  0%   { transform: translateX(-100%); opacity: 0; }
  40%  { opacity: 1; }
  100% { transform: translateX(250%); opacity: 0; }
}
@keyframes score-fill { from{width:0} to{width:var(--w)} }
@keyframes glow-breathe { 0%,100%{opacity:.35} 50%{opacity:1} }
@keyframes spin-slow { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@keyframes data-in { from{opacity:0;transform:translateX(-10px)} to{opacity:1;transform:translateX(0)} }
@keyframes number-pop { 0%{transform:scale(.8);opacity:0} 60%{transform:scale(1.05)} 100%{transform:scale(1);opacity:1} }

.blink  { animation: blink 2.5s step-end infinite; }
.fadein { animation: fadein .3s ease forwards; }

/* ── Panels ── */
.panel {
  background: ${C.panel};
  border: 1px solid ${C.border};
  position: relative;
  overflow: hidden;
}
.panel::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, ${C.cyan}30, transparent);
  pointer-events: none;
}

/* ── Panel header ── */
.phdr {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px solid ${C.border};
  background: rgba(0,229,255,0.018);
  font-family: 'Orbitron', monospace;
  font-size: 9px; font-weight: 600;
  letter-spacing: .22em; text-transform: uppercase;
  color: ${C.cyan};
}

/* ── Layer cards ── */
.layer-card {
  background: ${C.panel};
  border: 1px solid ${C.border};
  border-top: 2.5px solid var(--accent, ${C.cyan});
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
  cursor: default;
  transition: border-color .25s, background .25s;
}
.layer-card::after {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 45%;
  background: linear-gradient(to top, var(--accentFaint, rgba(0,229,255,.04)), transparent);
  pointer-events: none;
}
.layer-card.ATTACK {
  --accent: ${C.red};
  --accentFaint: rgba(255,45,85,.06);
  border-color: rgba(255,45,85,.4);
}
.layer-card.NORMAL {
  --accent: ${C.green};
  --accentFaint: rgba(0,245,160,.04);
  border-color: rgba(0,245,160,.25);
}

/* ── Score bar ── */
.score-bar-track {
  height: 5px; border-radius: 3px;
  background: rgba(255,255,255,.05);
  overflow: hidden; position: relative;
}
.score-bar-fill {
  height: 100%; border-radius: 3px;
  background: var(--c, ${C.cyan});
  box-shadow: 0 0 8px var(--c, ${C.cyan});
  transition: width .7s cubic-bezier(.4,0,.2,1);
}
.score-bar-beam {
  position: absolute; top: 0; bottom: 0;
  width: 40%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.3), transparent);
  animation: flow-beam 2.5s ease-in-out infinite;
}

/* ── Table rows ── */
.trow {
  display: grid;
  align-items: center;
  padding: 0 16px;
  height: 36px;
  border-bottom: 1px solid ${C.line};
  cursor: pointer;
  transition: background .1s;
  animation: data-in .2s ease forwards;
}
.trow:hover { background: rgba(0,229,255,.035); }
.trow.attack-row { border-left: 2px solid rgba(255,45,85,.5); }
.trow.normal-row { border-left: 2px solid rgba(0,245,160,.25); }

/* ── Badge ── */
.badge {
  display: inline-flex; align-items: center;
  padding: 2px 8px; border-radius: 2px;
  font-size: 9px; font-weight: 700;
  letter-spacing: .12em;
  font-family: 'JetBrains Mono', monospace;
}

/* ── Dot indicator ── */
.dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--c);
  box-shadow: 0 0 7px var(--c);
  flex-shrink: 0;
  position: relative;
}
.dot.live::after {
  content: '';
  position: absolute; inset: 0;
  border-radius: 50%;
  background: var(--c);
  animation: pulse-ring 1.8s ease-out infinite;
}

/* ── Button ── */
.btn {
  padding: 5px 12px;
  border: 1px solid ${C.border};
  background: transparent;
  color: ${C.text};
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px; letter-spacing: .1em;
  cursor: pointer;
  transition: all .15s;
}
.btn:hover { border-color: ${C.cyan}; color: ${C.cyan}; background: ${C.cyanGlow}; }
.btn.active { border-color: ${C.cyan}; color: ${C.cyan}; background: rgba(0,229,255,.07); }
.btn.danger:hover { border-color: ${C.red}; color: ${C.red}; background: rgba(255,45,85,.05); }

/* ── Threshold pill ── */
.thr-pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 2px 8px; border-radius: 2px;
  font-size: 9px; letter-spacing: .1em;
  font-family: 'JetBrains Mono', monospace;
  border: 1px dashed rgba(255,255,255,.12);
  color: ${C.dimTxt};
}

/* ── Fusion box ── */
.fusion-box {
  padding: 20px 24px;
  border: 1px solid var(--fc, ${C.border});
  background: linear-gradient(135deg, var(--fbg, rgba(0,0,0,0)) 0%, transparent 70%);
  position: relative;
  overflow: hidden;
  transition: all .4s;
}
.fusion-box::before {
  content: '';
  position: absolute; inset: 0;
  background: repeating-linear-gradient(
    45deg,
    transparent, transparent 6px,
    var(--fline, rgba(255,255,255,.01)) 6px,
    var(--fline, rgba(255,255,255,.01)) 7px
  );
  pointer-events: none;
}

/* ── KPI ── */
.kpi {
  background: ${C.panel};
  border: 1px solid ${C.border};
  border-left: 3px solid var(--c, ${C.cyan});
  padding: 14px 18px;
  position: relative;
}

/* ── Connection wire SVG animation ── */
@keyframes wire-flow {
  0%   { stroke-dashoffset: 60; opacity: .2; }
  50%  { opacity: .9; }
  100% { stroke-dashoffset: 0; opacity: .2; }
}
.wire { stroke-dasharray: 8 4; animation: wire-flow 1.8s linear infinite; }

/* ── Tabs ── */
.tab {
  padding: 7px 14px;
  font-family: 'Orbitron', monospace;
  font-size: 8px; font-weight: 600;
  letter-spacing: .18em; text-transform: uppercase;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  color: ${C.dimTxt};
  transition: all .15s;
}
.tab.on { color: ${C.cyan}; border-bottom-color: ${C.cyan}; }
.tab:hover:not(.on) { color: ${C.text}; }
`;

// ══════════════════════════════════════════════════════════════════════════════
//  DATA HOOK  — polls /events every 1 second (exact match to Streamlit)
// ══════════════════════════════════════════════════════════════════════════════
function useEvents() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("connecting");

  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/events`);
      if (!r.ok) throw new Error();
      const data = await r.json();
      setEvents(data.slice(-MAX_ROWS));
      setStatus("live");
    } catch {
      setStatus("offline");
    }
  }, []);

  useEffect(() => {
    fetch_();
    const t = setInterval(fetch_, REFRESH_MS);
    return () => clearInterval(t);
  }, [fetch_]);

  return { events, status };
}

// ══════════════════════════════════════════════════════════════════════════════
//  HEADER
// ══════════════════════════════════════════════════════════════════════════════
function Header({ status, total, attacks }) {
  const [clk, setClk] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setClk(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const connC = status === "live" ? C.green : status === "offline" ? C.red : C.yellow;

  return (
    <header style={{
      height: 52, padding: "0 22px",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      background: `linear-gradient(180deg, #050f1e 0%, ${C.bg} 100%)`,
      borderBottom: `1px solid ${C.border}`,
      position: "sticky", top: 0, zIndex: 200,
    }}>
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 13 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 4,
          background: `linear-gradient(135deg, ${C.cyan}, #0040ff)`,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: `0 0 18px rgba(0,229,255,.45)`,
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <polygon points="9,2 16,6 16,12 9,16 2,12 2,6" stroke="white" strokeWidth="1.5" fill="none"/>
            <circle cx="9" cy="9" r="2" fill="white"/>
          </svg>
        </div>
        <div>
          <div className="orb" style={{
            fontSize: 14, fontWeight: 800, letterSpacing: ".1em",
            color: C.bright, lineHeight: 1,
          }}>
            VECTRA <span style={{ color: C.cyan }}>SOC</span>
          </div>
          <div className="mono" style={{
            fontSize: 7, letterSpacing: ".22em", color: C.dimTxt, marginTop: 2,
          }}>3-LAYER NETWORK ANOMALY DETECTION</div>
        </div>
      </div>

      {/* Status row */}
      <div className="mono" style={{
        display: "flex", gap: 20, fontSize: 10,
        color: C.text, alignItems: "center",
      }}>
        <span style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <div className="dot live" style={{ "--c": connC }} />
          <span style={{ color: connC, letterSpacing: ".1em", fontSize: 9 }}>
            {status === "live" ? "LIVE CAPTURE" : status === "offline" ? "BACKEND OFFLINE" : "CONNECTING…"}
          </span>
        </span>
        <span style={{ color: C.dimTxt }}>│</span>
        <span>EVENTS <span style={{ color: C.cyan }}>{total}</span></span>
        <span style={{ color: C.dimTxt }}>│</span>
        <span>ATTACKS <span style={{ color: C.red }}>{attacks}</span></span>
        <span style={{ color: C.dimTxt }}>│</span>
        <span className="blink" style={{ color: C.cyan }}>
          {clk.toLocaleTimeString("en-GB", { hour12: false })}
        </span>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">
          <button className="btn">API DOCS ↗</button>
        </a>
        <button className="btn danger">⊗ CLEAR</button>
      </div>
    </header>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  LAYER CARD  — replaces the 3 st.columns cards from Streamlit
// ══════════════════════════════════════════════════════════════════════════════
function LayerCard({ title, layerNum, label, score, threshold, extra, modelName, icon }) {
  const r = riskOf(label);
  const isAttack = label === "attack";
  const scoreVal = score != null ? Math.min(score, 1) : 0;
  const threshVal = threshold != null ? Math.min(threshold, 1) : null;

  return (
    <div className={`layer-card ${isAttack ? "ATTACK" : "NORMAL"}`}>
      {/* Top row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
        <div>
          <div className="mono" style={{
            fontSize: 8, letterSpacing: ".2em", color: C.dimTxt, marginBottom: 5,
          }}>
            LAYER {layerNum} · {modelName}
          </div>
          <div className="orb" style={{ fontSize: 13, fontWeight: 700, color: C.bright, letterSpacing: ".08em" }}>
            {title}
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          <span className="badge" style={{
            background: `${r.c}20`, color: r.c,
            border: `1px solid ${r.c}40`,
          }}>{r.lbl}</span>
          <div style={{ fontSize: 26, opacity: .06, color: r.c, lineHeight: 1 }}>{icon}</div>
        </div>
      </div>

      {/* Score meter */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
          <span className="mono" style={{ fontSize: 9, color: C.dimTxt, letterSpacing: ".1em" }}>
            SCORE
          </span>
          <span className="mono" style={{ fontSize: 12, color: r.c, fontWeight: 600 }}>
            {score != null ? score.toFixed(4) : "—"}
          </span>
        </div>
        <div className="score-bar-track">
          <div
            className="score-bar-fill"
            style={{ width: `${scoreVal * 100}%`, "--c": r.c }}
          />
          <div className="score-bar-beam" />
          {/* Threshold marker */}
          {threshVal != null && (
            <div style={{
              position: "absolute", top: -3, bottom: -3,
              left: `${threshVal * 100}%`,
              width: 1.5, background: C.yellow,
              boxShadow: `0 0 5px ${C.yellow}`,
            }} />
          )}
        </div>
      </div>

      {/* Threshold info */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="thr-pill">
THR: {
  layerNum === 3 && threshold != null
    ? threshold.toFixed(3)
    : "—"
}       </span>
        {extra && extra.map(({ k, v }) => (
          <span key={k} className="mono" style={{ fontSize: 9, color: C.dimTxt }}>
            {k}: <span style={{ color: C.text }}>{v}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  FUSION ENGINE  — replaces Streamlit's "final fused decision" div
// ══════════════════════════════════════════════════════════════════════════════
function FusionBox({ ev }) {
  if (!ev) return null;
  const r = riskOf(ev.final_label);
  const isAttack = ev.final_label === "attack";

  return (
    <div className="fusion-box" style={{
      "--fc": `${r.c}40`,
      "--fbg": `${r.c}06`,
      "--fline": `${r.c}08`,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 24, flexWrap: "wrap" }}>

        {/* Fusion verdict */}
        <div>
          <div className="mono" style={{ fontSize: 8, letterSpacing: ".2em", color: C.dimTxt, marginBottom: 5 }}>
            FUSION ENGINE · MAJORITY VOTE
          </div>
          <div className="orb" style={{
            fontSize: 28, fontWeight: 900, color: r.c,
            textShadow: `0 0 20px ${r.glow}`,
            letterSpacing: ".06em",
          }}>{r.lbl}</div>
        </div>

        {/* Divider */}
        <div style={{ width: 1, height: 50, background: C.border }} />

        {/* Packet info */}
        <div>
          <div className="mono" style={{ fontSize: 8, color: C.dimTxt, marginBottom: 5 }}>SOURCE</div>
          <div className="orb" style={{ fontSize: 15, color: C.bright }}>{ev.src_ip}</div>
        </div>

        <div style={{ width: 1, height: 50, background: C.border }} />

        <div>
          <div className="mono" style={{ fontSize: 8, color: C.dimTxt, marginBottom: 5 }}>PACKET SIZE</div>
          <div className="orb" style={{ fontSize: 15, color: C.bright }}>{ev.packet_size} <span style={{ fontSize: 9, color: C.dimTxt }}>bytes</span></div>
        </div>

        <div style={{ width: 1, height: 50, background: C.border }} />

        <div>
          <div className="mono" style={{ fontSize: 8, color: C.dimTxt, marginBottom: 5 }}>TIME</div>
          <div className="orb" style={{ fontSize: 15, color: C.bright }}>{fmtTime(ev.timestamp)}</div>
        </div>

        <div style={{ width: 1, height: 50, background: C.border }} />

        {/* Layer agreement viz */}
        <div>
          <div className="mono" style={{ fontSize: 8, color: C.dimTxt, marginBottom: 8 }}>LAYER VOTES</div>
          <div style={{ display: "flex", gap: 10 }}>
            {[
              { n: "PKT", lbl: ev.packet_layer_label },
              { n: "FLW", lbl: ev.flow_layer_label },
              { n: "BEH", lbl: ev.behavior_layer_label },
            ].map(({ n, lbl }) => {
              const lr = riskOf(lbl);
              return (
                <div key={n} style={{ textAlign: "center" }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 2,
                    background: `${lr.c}20`, border: `1px solid ${lr.c}50`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    marginBottom: 4,
                  }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: lr.c, boxShadow: `0 0 6px ${lr.c}` }} />
                  </div>
                  <div className="mono" style={{ fontSize: 7, color: C.dimTxt, letterSpacing: ".1em" }}>{n}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Big verdict icon */}
        <div style={{ marginLeft: "auto" }}>
          <div style={{
            width: 60, height: 60, borderRadius: "50%",
            background: `${r.c}15`,
            border: `2px solid ${r.c}60`,
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: `0 0 24px ${r.glow}`,
          }}>
            <span style={{ fontSize: 24 }}>
              {isAttack ? "⚠" : "✓"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  PIPELINE WIRE — animated 3-layer flow diagram
// ══════════════════════════════════════════════════════════════════════════════
function PipelineWire({ ev }) {
  if (!ev) return null;
  const labels = [ev.packet_layer_label, ev.flow_layer_label, ev.behavior_layer_label];
  const names  = ["PACKET", "FLOW", "BEHAVIOUR"];
  const scores = [ev.packet_layer_score, ev.flow_layer_score, ev.behavior_layer_prob];

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 0, padding: "12px 18px",
    }}>
      {/* Input packet */}
      <div style={{
        background: C.dim, border: `1px solid ${C.border}`,
        padding: "8px 12px", minWidth: 80, textAlign: "center",
      }}>
        <div style={{ fontSize: 16, marginBottom: 3 }}>📡</div>
        <div className="mono" style={{ fontSize: 7, color: C.dimTxt, letterSpacing: ".1em" }}>PACKET</div>
        <div className="mono" style={{ fontSize: 9, color: C.cyan }}>{ev.src_ip}</div>
      </div>

      {names.map((name, i) => {
        const r = riskOf(labels[i]);
        return (
          <div key={name} style={{ display: "flex", alignItems: "center" }}>
            {/* Wire */}
            <svg width="36" height="20" style={{ overflow: "visible" }}>
              <line x1="0" y1="10" x2="36" y2="10"
                stroke={r.c} strokeWidth="1.5" opacity=".5"
                className="wire"
              />
              <polygon points="30,6 36,10 30,14" fill={r.c} opacity=".5" />
            </svg>

            {/* Layer box */}
            <div style={{
              background: `${r.c}0d`,
              border: `1px solid ${r.c}35`,
              padding: "10px 14px", minWidth: 130,
            }}>
              <div className="mono" style={{ fontSize: 7, color: C.dimTxt, marginBottom: 4, letterSpacing: ".14em" }}>
                LAYER {i + 1}
              </div>
              <div className="orb" style={{ fontSize: 10, color: C.bright, marginBottom: 5 }}>{name}</div>
              <div style={{ marginBottom: 5 }}>
                <div className="score-bar-track" style={{ height: 3 }}>
                  <div className="score-bar-fill"
                    style={{ width: `${Math.min(scores[i] ?? 0, 1) * 100}%`, "--c": r.c }} />
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="mono" style={{ fontSize: 9, color: r.c }}>
                  {scores[i]?.toFixed(3) ?? "—"}
                </span>
                <span className="badge" style={{
                  background: `${r.c}20`, color: r.c,
                  border: `1px solid ${r.c}35`, fontSize: 7,
                }}>{r.lbl}</span>
              </div>
            </div>
          </div>
        );
      })}

      {/* Final wire */}
      <svg width="36" height="20">
        <line x1="0" y1="10" x2="36" y2="10"
          stroke={riskOf(ev.final_label).c} strokeWidth="1.5" opacity=".5" className="wire" />
        <polygon points="30,6 36,10 30,14" fill={riskOf(ev.final_label).c} opacity=".5" />
      </svg>

      {/* Fusion output */}
      {(() => {
        const fr = riskOf(ev.final_label);
        return (
          <div style={{
            background: `${fr.c}12`,
            border: `1px solid ${fr.c}50`,
            padding: "10px 16px", minWidth: 100,
            textAlign: "center",
          }}>
            <div className="mono" style={{ fontSize: 7, color: C.dimTxt, marginBottom: 4 }}>FUSION</div>
            <div className="orb" style={{
              fontSize: 16, color: fr.c,
              textShadow: `0 0 12px ${fr.glow}`,
            }}>{fr.lbl}</div>
          </div>
        );
      })()}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  TREND CHART — attack probability over time
// ══════════════════════════════════════════════════════════════════════════════
function TrendChart({ events }) {
  const data = events
    .slice(-40)
    .map(ev => ({
      t: fmtTime(ev.timestamp),
      pkt: ev.packet_layer_score != null ? +ev.packet_layer_score.toFixed(3) : 0,
      flw: ev.flow_layer_score   != null ? +ev.flow_layer_score.toFixed(3)   : 0,
      beh: ev.behavior_layer_prob!= null ? +ev.behavior_layer_prob.toFixed(3): 0,
    }));

  const Tip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{
        background: "#020c16", border: `1px solid ${C.border}`,
        padding: "8px 12px", fontFamily: "JetBrains Mono", fontSize: 10, color: C.bright,
      }}>
        <div style={{ color: C.dimTxt, fontSize: 8, marginBottom: 4 }}>{payload[0]?.payload?.t}</div>
        {payload.map(p => (
          <div key={p.dataKey} style={{ color: p.color }}>
            {p.dataKey.toUpperCase()}: {p.value}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="panel">
      <div className="phdr">
        <div className="dot live" style={{ "--c": C.cyan, width: 5, height: 5 }} />
        Layer Score Trend
        <div style={{ marginLeft: "auto", display: "flex", gap: 14, alignItems: "center" }}>
          {[["PKT", C.cyan], ["FLW", C.purple], ["BEH", C.orange]].map(([l, c]) => (
            <span key={l} className="mono" style={{ fontSize: 8, color: C.dimTxt }}>
              <span style={{ color: c }}>■</span> {l}
            </span>
          ))}
        </div>
      </div>
      <div style={{ padding: "12px 8px 8px" }}>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
            <defs>
              {[["gP", C.cyan], ["gF", C.purple], ["gB", C.orange]].map(([id, c]) => (
                <linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={c} stopOpacity={.25} />
                  <stop offset="95%" stopColor={c} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <XAxis dataKey="t" tick={{ fill: C.dimTxt, fontSize: 8, fontFamily: "JetBrains Mono" }}
              axisLine={false} tickLine={false} />
            <YAxis domain={[0, 1]} tick={{ fill: C.dimTxt, fontSize: 8 }}
              axisLine={false} tickLine={false} width={28} />
            <Tooltip content={<Tip />} cursor={{ stroke: `${C.cyan}25`, strokeWidth: 1 }} />
            <Area type="monotone" dataKey="pkt" stroke={C.cyan}   strokeWidth={1.5} fill="url(#gP)" dot={false} />
            <Area type="monotone" dataKey="flw" stroke={C.purple} strokeWidth={1.2} fill="url(#gF)" dot={false} />
            <Area type="monotone" dataKey="beh" stroke={C.orange} strokeWidth={1.2} fill="url(#gB)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  TRAFFIC STATS  — bytes/s and packets/s from Streamlit flow layer data
// ══════════════════════════════════════════════════════════════════════════════
function TrafficChart({ events }) {
  const data = events.slice(-30).map(ev => ({
    t: fmtTime(ev.timestamp),
    bps: ev.flow_bytes_s   != null ? Math.round(ev.flow_bytes_s)   : 0,
    pps: ev.flow_packets_s != null ? Math.round(ev.flow_packets_s) : 0,
  }));

  return (
    <div className="panel">
      <div className="phdr">
        <span>⇌</span> Flow Traffic
        <span className="mono" style={{ marginLeft: "auto", fontSize: 8, color: C.dimTxt }}>
          bytes/s + packets/s
        </span>
      </div>
      <div style={{ padding: "12px 8px 8px" }}>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
            <XAxis dataKey="t" tick={{ fill: C.dimTxt, fontSize: 8, fontFamily: "JetBrains Mono" }}
              axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: C.dimTxt, fontSize: 8 }} axisLine={false} tickLine={false} width={30} />
            <Tooltip
              contentStyle={{
                background: "#020c16", border: `1px solid ${C.border}`,
                fontFamily: "JetBrains Mono", fontSize: 10, color: C.bright,
              }} />
            <Bar dataKey="bps" radius={[2, 2, 0, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={d.bps > 5000 ? C.red : d.bps > 1000 ? C.orange : C.cyan} opacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  HEATMAP — risk grid
// ══════════════════════════════════════════════════════════════════════════════
function RiskHeatmap({ events, onSelect }) {
  const last = events.slice(-60);
  return (
    <div className="panel">
      <div className="phdr"><span>◈</span> Risk Heatmap · Last 60 Packets</div>
      <div style={{ padding: "10px 14px", display: "grid", gridTemplateColumns: "repeat(12,1fr)", gap: 3 }}>
        {last.map((ev, i) => {
          const r = riskOf(ev.final_label);
          const intensity = ev.packet_layer_score != null ? Math.min(ev.packet_layer_score, 1) : 0.3;
          return (
            <div key={i} onClick={() => onSelect?.(ev)}
              title={`${ev.src_ip} | ${ev.final_label} | score:${ev.packet_layer_score?.toFixed(3)}`}
              style={{
                height: 14, borderRadius: 2, cursor: "pointer",
                background: r.c, opacity: 0.25 + intensity * 0.75,
                transition: "transform .1s, opacity .1s",
              }}
              onMouseEnter={e => { e.target.style.transform = "scaleY(1.5)"; e.target.style.opacity = 1; }}
              onMouseLeave={e => { e.target.style.transform = ""; e.target.style.opacity = 0.25 + intensity * 0.75; }}
            />
          );
        })}
      </div>
      <div className="mono" style={{
        padding: "2px 14px 9px",
        display: "flex", gap: 14, fontSize: 8, color: C.dimTxt,
      }}>
        <span style={{ color: C.green }}>■ NORMAL</span>
        <span style={{ color: C.yellow }}>■ WARNING</span>
        <span style={{ color: C.red }}>■ ATTACK</span>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  TABLE  — "Recent Packets" (exact match to Streamlit table, but beautiful)
// ══════════════════════════════════════════════════════════════════════════════
const COLS = [
  { key: "time",                  label: "TIME",     w: "65px" },
  { key: "src_ip",               label: "SRC IP",    w: "1fr" },
  { key: "packet_size",          label: "PKT SIZE",  w: "75px" },
  { key: "flow_bytes_s",         label: "BYTES/S",   w: "80px" },
  { key: "flow_packets_s",       label: "PKTS/S",    w: "70px" },
  { key: "packet_layer_label",   label: "PKT LYR",   w: "75px" },
  { key: "flow_layer_label",     label: "FLW LYR",   w: "75px" },
  { key: "behavior_layer_label", label: "BEH LYR",   w: "75px" },
  { key: "final_label",          label: "FINAL",     w: "80px" },
  { key: "packet_layer_score",   label: "PKT SCORE", w: "85px" },
  { key: "flow_layer_score",     label: "FLW SCORE", w: "85px" },
  { key: "behavior_layer_prob",  label: "BEH PROB",  w: "85px" },
];
const GCOLS = COLS.map(c => c.w).join(" ");

function PacketTable({ events, filter, setFilter }) {
  const sorted = [...events].reverse();
  const filtered = filter === "all" ? sorted
    : filter === "attack" ? sorted.filter(e => e.final_label === "attack")
    : sorted.filter(e => e.final_label === "normal");

  const LabelCell = ({ label }) => {
    const r = riskOf(label);
    return (
      <span className="badge" style={{
        background: `${r.c}18`, color: r.c, border: `1px solid ${r.c}35`, fontSize: 8,
      }}>{r.lbl}</span>
    );
  };

  return (
    <div className="panel">
      <div className="phdr">
        <div className="dot live" style={{ "--c": C.red, width: 5, height: 5 }} />
        Recent Packets
        <span className="mono" style={{ color: C.dimTxt, fontSize: 8, marginLeft: 4 }}>
          — last {MAX_ROWS} packets
        </span>
        <div style={{ marginLeft: "auto", display: "flex", gap: 5 }}>
          {["all", "attack", "normal"].map(f => (
            <button key={f} className={`btn ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}>
              {f.toUpperCase()}
            </button>
          ))}
        </div>
        <span className="mono" style={{ color: C.cyan, fontSize: 10, marginLeft: 8 }}>
          {filtered.length}
        </span>
      </div>

      {/* Column headers */}
      <div className="mono" style={{
        display: "grid", gridTemplateColumns: GCOLS,
        padding: "0 16px", height: 26, alignItems: "center",
        borderBottom: `1px solid ${C.border}`,
        fontSize: 7, letterSpacing: ".16em", color: C.dimTxt,
      }}>
        {COLS.map(c => <div key={c.key}>{c.label}</div>)}
      </div>

      <div style={{ maxHeight: 380, overflowY: "auto" }}>
        {filtered.slice(0, 100).map((ev, i) => {
          const isAtk = ev.final_label === "attack";
          return (
            <div key={i}
              className={`trow mono fadein ${isAtk ? "attack-row" : "normal-row"}`}
              style={{ gridTemplateColumns: GCOLS, animationDelay: `${i * .015}s` }}>
              <span style={{ color: C.dimTxt, fontSize: 9 }}>{fmtTime(ev.timestamp)}</span>
              <span style={{ color: C.bright, fontSize: 11 }}>{ev.src_ip}</span>
              <span style={{ color: C.text, fontSize: 10 }}>{ev.packet_size}<span style={{ color: C.dimTxt, fontSize: 8 }}>B</span></span>
              <span style={{ color: C.text, fontSize: 10 }}>{fmtKB(ev.flow_bytes_s)}</span>
              <span style={{ color: C.text, fontSize: 10 }}>{ev.flow_packets_s?.toFixed(1) ?? "—"}</span>
              <LabelCell label={ev.packet_layer_label} />
              <LabelCell label={ev.flow_layer_label} />
              <LabelCell label={ev.behavior_layer_label} />
              <span className="badge" style={{
                background: isAtk ? `${C.red}20` : `${C.green}15`,
                color: isAtk ? C.red : C.green,
                border: `1px solid ${isAtk ? C.red : C.green}40`,
                fontWeight: 700, fontSize: 9,
              }}>{ev.final_label?.toUpperCase()}</span>
              <span style={{ color: C.cyan, fontSize: 10, fontFamily: "JetBrains Mono" }}>
                {ev.packet_layer_score?.toFixed(4) ?? "—"}
              </span>
              <span style={{ color: C.purple, fontSize: 10 }}>
                {ev.flow_layer_score?.toFixed(3) ?? "—"}
              </span>
              <span style={{ color: C.orange, fontSize: 10 }}>
                {ev.behavior_layer_prob?.toFixed(3) ?? "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  OFFLINE SCREEN
// ══════════════════════════════════════════════════════════════════════════════
function Offline() {
  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", flexDirection: "column", gap: 16,
    }}>
      <div className="orb" style={{ fontSize: 52, color: C.red, textShadow: `0 0 30px ${C.red}` }}>⊗</div>
      <div className="orb" style={{ fontSize: 18, color: C.red, letterSpacing: ".1em" }}>BACKEND OFFLINE</div>
      <div className="mono" style={{ fontSize: 11, color: C.text, textAlign: "center", lineHeight: 1.8 }}>
        Cannot reach <span style={{ color: C.cyan }}>{API_BASE}</span>
        <br />Make sure <code style={{ color: C.cyan }}>realtime_backend.py</code> is running.
      </div>
      <div style={{
        background: C.panel, border: `1px solid ${C.border}`,
        padding: "14px 22px",
        fontFamily: "JetBrains Mono", fontSize: 11, color: C.cyan,
        borderLeft: `3px solid ${C.cyan}`,
      }}>
        python realtime_backend.py
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  ROOT APP
// ══════════════════════════════════════════════════════════════════════════════
export default function App() {
  const { events, status } = useEvents();
  const [selected, setSelected] = useState(null);
  const [filter,   setFilter]   = useState("all");
  const [tab,      setTab]      = useState("monitor");

  const latest  = events.length ? events[events.length - 1] : null;
  const attacks = events.filter(e => e.final_label === "attack").length;

  // Auto-select latest event for cards
  useEffect(() => {
    if (latest) setSelected(latest);
  }, [latest?.timestamp]);

  if (status === "offline" && events.length === 0) return (
    <div style={{ minHeight: "100vh", background: C.bg }}>
      <style>{CSS}</style>
      <Offline />
    </div>
  );

  const ev = selected || latest;

  return (
    <div style={{ minHeight: "100vh", background: C.bg }}>
      <style>{CSS}</style>

      <Header status={status} total={events.length} attacks={attacks} />

      <div style={{ padding: "14px 20px", display: "flex", flexDirection: "column", gap: 10 }}>

        {/* ── TITLE BANNER ── */}
        <div style={{ marginBottom: 2 }}>
          <div className="orb" style={{ fontSize: 11, color: C.dimTxt, letterSpacing: ".22em" }}>
            REALTIME 3-LAYER NETWORK ANOMALY DETECTION
          </div>
          <div style={{ fontSize: 12, color: C.dimTxt, marginTop: 4, lineHeight: 1.6, maxWidth: 680 }}>
            Live packets from your WiFi interface · processed through{" "}
            <span style={{ color: C.cyan }}>Packet Layer</span> →{" "}
            <span style={{ color: C.purple }}>Flow Layer</span> →{" "}
            <span style={{ color: C.orange }}>Behaviour Layer</span> →{" "}
            <span style={{ color: C.bright }}>Fusion Engine</span>
          </div>
        </div>

        {/* ── KPI ROW ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
          {[
            { label: "Total Packets",   value: events.length,     c: C.cyan,   icon: "◈" },
            { label: "Attacks Found",   value: attacks,           c: C.red,    icon: "⚠" },
            { label: "Normal Traffic",  value: events.length - attacks, c: C.green, icon: "✓" },
            { label: "Latest Packet",   value: ev ? fmtTime(ev.timestamp) : "—", c: C.yellow, icon: "⏱" },
          ].map(({ label, value, c, icon }) => (
            <div key={label} className="kpi" style={{ "--c": c }}>
              <div className="mono" style={{ fontSize: 8, letterSpacing: ".2em", color: C.dimTxt, marginBottom: 7 }}>
                {icon} {label.toUpperCase()}
              </div>
              <div className="orb" style={{
                fontSize: 26, color: c, lineHeight: 1,
                textShadow: `0 0 16px ${c}44`, fontWeight: 700,
              }}>{value}</div>
            </div>
          ))}
        </div>

        {/* ── TABS ── */}
        <div style={{ display: "flex", gap: 0, borderBottom: `1px solid ${C.border}` }}>
          {[
            ["monitor",  "◉ LIVE MONITOR"],
            ["pipeline", "⇌ PIPELINE VIEW"],
            ["table",    "≡ PACKET TABLE"],
          ].map(([k, l]) => (
            <div key={k} className={`tab ${tab === k ? "on" : ""}`} onClick={() => setTab(k)}>{l}</div>
          ))}
          {status === "offline" && (
            <div className="mono blink" style={{
              marginLeft: "auto", fontSize: 8, color: C.orange,
              alignSelf: "center", padding: "0 12px",
            }}>⚠ STALE DATA — BACKEND UNREACHABLE</div>
          )}
        </div>

        {/* ══════════════════════════════════════════════════
            TAB 1 — LIVE MONITOR
        ══════════════════════════════════════════════════ */}
        {tab === "monitor" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>

            {/* 3 layer cards — exact mirror of Streamlit col_pkt / col_flow / col_beh */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>

              {/* Packet Layer Card */}
              <LayerCard
                title="Packet Layer"
                layerNum={1}
                label={ev?.packet_layer_label ?? "normal"}
                score={ev?.packet_layer_score}
                threshold={ev?.packet_layer_threshold}
                modelName="Autoencoder"
                icon="◉"
                extra={[]}
              />

              {/* Flow Layer Card */}
              <LayerCard
                title="Flow Layer"
                layerNum={2}
                label={ev?.flow_layer_label ?? "normal"}
                score={ev?.flow_layer_score}
                threshold={ev?.flow_layer_threshold}
                modelName="Random Forest"
                icon="⇌"
                extra={[
                  { k: "bytes/s", v: ev?.flow_bytes_s?.toFixed(1) ?? "—" },
                  { k: "pkts/s",  v: ev?.flow_packets_s?.toFixed(1) ?? "—" },
                ]}
              />

              {/* Behaviour Layer Card */}
             <LayerCard
  title="Behaviour Layer"
  layerNum={3}
  label={ev?.behavior_layer_label ?? "normal"}
  score={ev?.behavior_layer_prob}
  threshold={ev?.behavior_layer_threshold}   // 👈 ADD THIS
  modelName="GRU Sequence"
  icon="≋"
  extra={[
    { k: "window", v: "last 10 vectors" },
  ]}
/>
            </div>

            {/* Fusion result — exact mirror of Streamlit "second_row_placeholder" */}
            {ev && <FusionBox ev={ev} />}

            {/* Charts row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <TrendChart events={events} />
              <TrafficChart events={events} />
            </div>

            <RiskHeatmap events={events} onSelect={setSelected} />
          </div>
        )}

        {/* ══════════════════════════════════════════════════
            TAB 2 — PIPELINE VIEW (judge impression tab)
        ══════════════════════════════════════════════════ */}
        {tab === "pipeline" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {/* Explainer */}
            <div className="panel" style={{ padding: "16px 20px" }}>
              <div className="orb" style={{ fontSize: 14, color: C.bright, marginBottom: 8, fontWeight: 700 }}>
                3-Layer Detection Architecture
              </div>
              <div style={{ fontSize: 12, color: C.text, lineHeight: 1.7, maxWidth: 700 }}>
                Each captured WiFi packet passes through three independent ML models.
                The <span style={{ color: C.bright, fontWeight: 600 }}>Fusion Engine</span> uses
                majority voting — a FINAL ATTACK verdict fires only when ≥2 layers agree,
                eliminating single-layer false positives.
              </div>
            </div>

            {/* Live pipeline for latest packet */}
            <div className="panel" style={{ overflow: "hidden" }}>
              <div className="phdr">⇌ Live Pipeline · Latest Packet</div>
              {ev
                ? <PipelineWire ev={ev} />
                : <div style={{ padding: 30, color: C.dimTxt, fontFamily: "JetBrains Mono", fontSize: 10 }}>
                    Waiting for first packet…
                  </div>
              }
            </div>

            {/* Last 10 pipeline snapshots */}
            <div className="panel">
              <div className="phdr">≡ Recent Pipeline Snapshots</div>
              <div style={{ maxHeight: 400, overflowY: "auto" }}>
                {[...events].reverse().slice(0, 15).map((ev, i) => {
                  const fr = riskOf(ev.final_label);
                  return (
                    <div key={i} onClick={() => setSelected(ev)}
                      style={{
                        padding: "10px 16px",
                        borderBottom: `1px solid ${C.line}`,
                        cursor: "pointer",
                        background: selected?.timestamp === ev.timestamp ? `${C.cyan}06` : undefined,
                        display: "grid",
                        gridTemplateColumns: "65px 120px 1fr 1fr 1fr 100px",
                        alignItems: "center", gap: 0,
                      }}>
                      <span className="mono" style={{ fontSize: 9, color: C.dimTxt }}>
                        {fmtTime(ev.timestamp)}
                      </span>
                      <span className="mono" style={{ fontSize: 11, color: C.bright }}>
                        {ev.src_ip}
                      </span>
                      {/* Mini layer bars */}
                      {[
                        { n: "PKT", v: ev.packet_layer_score,   c: C.cyan },
                        { n: "FLW", v: ev.flow_layer_score,     c: C.purple },
                        { n: "BEH", v: ev.behavior_layer_prob,  c: C.orange },
                      ].map(({ n, v, c }) => (
                        <div key={n} style={{ padding: "0 10px" }}>
                          <div className="mono" style={{ fontSize: 7, color: C.dimTxt, marginBottom: 3 }}>
                            {n} {v?.toFixed(3) ?? "—"}
                          </div>
                          <div className="score-bar-track" style={{ height: 3 }}>
                            <div className="score-bar-fill"
                              style={{ width: `${Math.min(v ?? 0, 1) * 100}%`, "--c": c }} />
                          </div>
                        </div>
                      ))}
                      <span className="badge" style={{
                        background: `${fr.c}20`, color: fr.c, border: `1px solid ${fr.c}40`,
                        fontSize: 9, fontWeight: 800,
                      }}>{fr.lbl}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════
            TAB 3 — PACKET TABLE (exact Streamlit df replacement)
        ══════════════════════════════════════════════════ */}
        {tab === "table" && (
          <PacketTable events={events} filter={filter} setFilter={setFilter} />
        )}

      </div>
    </div>
  );
}











