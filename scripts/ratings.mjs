import fs from 'node:fs';
const csv=p=>{const [head,...rows]=fs.readFileSync(p,'utf8').trim().split('\n').map(l=>l.split(','));return rows.map(r=>Object.fromEntries(head.map((k,i)=>[k,['name','team','role','phase'].includes(k)?r[i]:Number(r[i])])));};
const regular=csv('data/regular.csv'),playoffs=csv('data/playoffs.csv'),teamData=csv('data/teams.csv');
const shini=playoffs.find(p=>p.name==='Shini');regular.push({...shini,team:'FUR',role:'JG',games:0});
const teams=teamData.filter(t=>t.phase==='regular').map(t=>{const p=teamData.find(x=>x.team===t.team&&x.phase==='playoffs'),w=p?p.games/(p.games+8):0;return{team:t.team,weight:w,regular:t,playoffs:p||null,...Object.fromEntries(['wr','dragons','barons','gd15'].map(k=>[k,p?w*p[k]+(1-w)*t[k]:t[k]]))};});
function percentile(list,v,key,invert=false){const n=(list.filter(x=>x[key]<v).length+.5*list.filter(x=>x[key]===v).length)/list.length;return invert?1-n:n;}
for(const t of teams)t.score=64+24*(.45*percentile(teams,t.wr,'wr')+.25*percentile(teams,t.dragons,'dragons')+.2*percentile(teams,t.barons,'barons')+.1*percentile(teams,t.gd15,'gd15'));
const players=regular.filter(p=>p.name.toLowerCase()!=='luuukz').map(p=>{const last=playoffs.find(q=>q.name.toLowerCase()===p.name.toLowerCase());const metrics={...p},recent=p.games?(last?last.games/(last.games+8):0):1;for(const k of ['wr','kda','deaths','kp','dpm','vspm','gd15','csd15'])metrics[k]=last?last[k]*recent+p[k]*(1-recent):p[k];return{id:p.name.toLowerCase(),name:p.name,team:p.team,role:p.role,regular:p.games?{...p}:null,playoffs:last||null,metrics,confidence:Math.min(1,(p.games+(last?.games||0))/15),recentWeight:recent};});
function pct(p,key,invert=false){return percentile(players.filter(x=>x.role===p.role).map(x=>x.metrics),p.metrics[key],key,invert);}
for(const p of players){const micro=p.role==='SUP'?.45*pct(p,'kda')+.35*pct(p,'kp')+.2*pct(p,'deaths',true):.35*pct(p,'gd15')+.25*pct(p,'csd15')+.25*pct(p,'dpm')+.15*pct(p,'kda');const macro=.55*pct(p,'kp')+.45*pct(p,'vspm'),mental=.6*pct(p,'deaths',true)+.4*pct(p,'kda');const t=teams.find(x=>x.team===p.team),individual={};for(const [k,v] of Object.entries({micro,macro,mental}))individual[k]=64+24*(.5+(v-.5)*p.confidence);p.micro=Math.round(.8*individual.micro+.2*t.score);p.macro=Math.round(.65*individual.macro+.35*t.score);p.mental=Math.round(.75*individual.mental+.25*t.score);p.overall=Math.round(.4*p.micro+.4*p.macro+.2*p.mental);p.price=Math.max(5,Math.min(16,Math.round(5+(p.overall-65)*.45)));p.teamForm=Math.round(t.score);p.ratingVersion=2;}
// Reaplica as notas oficiais após o recálculo estatístico, para não perder
// os overalls aprovados pelo organizador ao executar npm run ratings.
const officialRatings=JSON.parse(fs.readFileSync('data/official-overalls.json','utf8'));
for(const p of players){const o=officialRatings[p.id];if(!Number.isInteger(o))continue;
 const diff=o-p.overall;
 for(const k of ['micro','macro','mental'])p[k]=Math.max(40,Math.min(99,p[k]+diff));
 p.overall=o;p.price=Math.max(3,Math.min(20,Math.round(5+(o-65)*.45)));
 p.ratingVersion='official-v6';
}
const photos=JSON.parse(fs.readFileSync('data/player-photos.json','utf8'));
for(const p of players){delete p.metrics;p.photo=photos[p.id]?.path||null;}
fs.writeFileSync('data/players.json',JSON.stringify(players,null,2));fs.writeFileSync('data/team-form.json',JSON.stringify(teams,null,2));console.log(players.length+' players; ratings',Math.min(...players.map(p=>p.overall)),Math.max(...players.map(p=>p.overall)));
