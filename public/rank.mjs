// Ranking de progresso local: sem conta autenticada, vinculado ao nome da equipe neste navegador.
const TIERS=['Ferro','Bronze','Prata','Ouro','Platina','Esmeralda','Diamante','Mestre','Grão-Mestre','Desafiante'];
const DIVISIONS=['IV','III','II','I'];
const storageKey=name=>'rift-rank-v1:'+String(name||'').trim().toLocaleLowerCase('pt-BR');
const fresh=()=>({step:4,lp:0,wins:0,losses:0,titles:0,history:[],recorded:[]}); // Bronze IV
export function getRank(name){try{const r=JSON.parse(localStorage.getItem(storageKey(name)));return r&&Number.isInteger(r.step)?{...fresh(),...r}:fresh();}catch{return fresh();}}
export function rankLabel(r){const step=Math.max(0,Math.min(r.step,4*7+2));if(step>=28)return TIERS[Math.min(9,7+step-28)];return `${TIERS[Math.floor(step/4)]} ${DIVISIONS[step%4]}`;}
export function rankPercent(r){return Math.max(0,Math.min(100,r.lp));}
function placement(room,id){const teams=room.members;
 const scores=teams.map((m,i)=>{const played=room.matches.filter(x=>x.winner&&(x.a===m.id||x.b===m.id));const playoffs=played.filter(x=>x.stage==='playoffs');const wonPlayoffs=playoffs.filter(x=>x.winner===m.id);const wins=played.filter(x=>x.winner===m.id).length;
 const latest=playoffs.length?Math.max(...playoffs.map(x=>x.round)):0;
 const lastLoss=playoffs.filter(x=>x.winner!==m.id).sort((a,b)=>b.round-a.round)[0];
 const groupWins=played.filter(x=>x.stage!=='playoffs'&&x.winner===m.id).length;
 const diff=played.reduce((n,x)=>n+(x.a===m.id?x.score[0]-x.score[1]:x.score[1]-x.score[0]),0);
 return{id:m.id,isChampion:m.id===room.champion,played:played.length,latest,won:wonPlayoffs.length,lastLoss:!!lastLoss,groupWins,wins,diff,index:i};});
 scores.sort((a,b)=>Number(b.isChampion)-Number(a.isChampion)||b.latest-a.latest||b.won-a.won||b.groupWins-a.groupWins||b.diff-a.diff||b.wins-a.wins||a.index-b.index);
 return scores.findIndex(x=>x.id===id)+1;
}
export function applyRankResult(room,id){if(room.phase!=='finished'||!id)return null;const m=room.members.find(m=>m.id===id);if(!m?.roster)return null;const r=getRank(m.name);const marker=`${room.code}:${room.created}:${id}`;
 if(r.recorded.includes(marker))return null;
 const place=placement(room,id),total=room.members.length;
 // Progresso deliberadamente lento: campeão sobe, vice perde pouco, eliminação precoce perde mais.
 const delta=place===1?(total===2?18:total===4?22:25):total===2?-12:place===2?-5:place<=Math.ceil(total/2)?-10:-16;
 let lp=r.lp+delta,step=r.step;
 while(lp>=100&&step<30){step++;lp-=100;}
 while(lp<0&&step>0){step--;lp+=100;}
 if(step===0&&lp<0)lp=0;
 r.step=step;r.lp=lp;r.wins+=Number(place===1);r.losses+=Number(place!==1);r.titles+=Number(place===1);
 const entry={room:marker,date:new Date().toISOString(),place,total,delta,rank:rankLabel(r),lp:r.lp};
 r.history=[entry,...r.history].slice(0,30);r.recorded=[marker,...r.recorded].slice(0,150);
 try{localStorage.setItem(storageKey(m.name),JSON.stringify(r));}catch{}
 return entry;
}
export function rankHtml(name){const r=getRank(name);return `<b>${r.wins} - ${r.losses}</b><span>${rankLabel(r)}</span><small>${r.lp} PDL · ${r.titles} títulos</small>`;}
