import assert from 'node:assert/strict';import fs from 'node:fs';
const base=process.argv[2];if(!base?.startsWith('https://'))throw new Error('Supply the deployed HTTPS URL.');
const report={site:base,revision:3,checks:[],physical_devices:false};
async function req(path,body,token){const response=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});const data=await response.json();return{status:response.status,...data};}
const mark=name=>{report.checks.push(name);console.log('PASS',name);};
try{
const h=await req('/api/rooms',{name:'Smoke A',capacity:2,config:{format:'knockout',supply:'exact',showOverall:false,gameplay:'mechanical'}});assert.equal(h.status,201,h.error);const c=h.state.code,path='/api/rooms/'+c;const g=await req(path+'/join',{name:'Smoke B'});assert.equal(g.status,200,g.error);mark('Two separate anonymous sessions join persisted room');
let r=await req(path+'/action',{type:'start'},h.token);assert.equal(r.status,200,r.error);let s=r.state;assert.equal(s.market.pool.length,10);assert.equal(s.config.showOverall,false);const unsold=s.auction.card;r=await req(path+'/action',{type:'speed'},h.token);assert.equal(r.status,200,r.error);s=r.state;assert.equal(s.sold.length,0);assert.ok(s.members.every(m=>m.balance===50&&Object.keys(m.roster).length===0));assert.ok(s.market.unsold.includes(unsold));mark('Unsold lot does not charge or allocate any player; exact market and hidden-overall settings persist');
for(let i=0;i<12&&s.phase==='auction';i++){
const role=(await import('../data/players.json',{with:{type:'json'}})).default.find(p=>p.id===s.auction.card).role;
const buyer=!s.members.find(m=>m.id===h.id).roster[role]?h:g;
r=await req(path+'/action',{type:'bid',amount:s.auction.bid+1,card:s.auction.card},buyer.token);assert.equal(r.status,200,r.error);
const viewed=await req(path,undefined,buyer===h?g.token:h.token);assert.equal(viewed.state.auction.leader,buyer.id);
r=await req(path+'/action',{type:'speed'},h.token);assert.equal(r.status,200,r.error);s=r.state;
}
assert.equal(s.phase,'tournament');assert.equal(new Set(s.members.flatMap(m=>Object.values(m.roster))).size,10);mark('Bids synchronize between sessions, then ten exclusive cards close both line-ups');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let totalTurns=0;
for(let game=1;game<=3&&s.phase!=='finished';game++){
for(const p of [h,g]){r=await req(path+'/action',{type:'choose',option:0,match:s.series.match,game},p.token);assert.equal(r.status,200,r.error);s=r.state;}
assert.equal(s.series.stage,'tactics');
for(let turn=0;turn<24&&s.series.stage==='tactics';turn++){
const a=(await req(path,undefined,h.token)).state,b=(await req(path,undefined,g.token)).state;
assert.equal(a.series.tactics.phase,'planning');assert.equal(b.series.tactics.phase,'planning');
const order=(v,p)=>({type:'orders',match:v.series.match,game,turn:v.series.tactics.turn,orders:{units:v.series.tactics.units.filter(u=>u.side===v.series.tactics.side).map(u=>({role:u.role,x:p===h?50:u.x,y:p===h?50:u.y,stance:p===h?'engage':'farm',buy:u.gold>=3&&u.items.length<3?'blade':null,target:null})),ward:null}});
const ah=order(a,h),bg=order(b,g);r=await req(path+'/action',ah,h.token);assert.equal(r.status,200,r.error);
const privateView=await req(path,undefined,g.token);assert.equal(privateView.state.series.tactics.myOrders,null);assert.equal(privateView.state.series.tactics.orders,undefined);
r=await req(path+'/action',bg,g.token);assert.equal(r.status,200,r.error);assert.equal(r.state.series.tactics.phase,'replay');assert.equal(r.state.series.tactics.frames.length,1);assert.equal(r.state.series.tactics.report.length,0);
await wait(Math.max(0,r.state.series.tactics.deadline-Date.now()+120));r=await req(path,undefined,h.token);assert.equal(r.status,200,r.error);s=r.state;totalTurns++;
if(totalTurns%5===0)console.log('Resolved tactical turns:',totalTurns);
}
assert.equal(s.series.stage,'result');assert.equal(s.series.result.mode,'mechanical');assert.ok(s.series.result.score.some(n=>n>0));
r=await req(path+'/action',{type:'next'},h.token);assert.equal(r.status,200,r.error);s=r.state;
}
assert.equal(s.phase,'finished');assert.ok([2,3].includes(s.matches[0].games.length));assert.equal(Math.max(...s.matches[0].score),2);const champs=s.matches[0].games.flatMap(x=>x.comps.flatMap(x=>Object.values(x.champions)));assert.equal(new Set(champs).size,s.matches[0].games.length*10);mark('Hosted mechanical BO3 resolves hidden orders simultaneously, reveals replay progressively, scores actual objectives, ends at two wins and preserves Fearless');
const reconnected=await req(path+'/join',{name:'Ignored'},g.token);assert.equal(reconnected.id,g.id);assert.equal(reconnected.state.champion,s.champion);mark('Existing session reconnects after championship');report.tactical_turns=totalTurns;report.passed=true;
}catch(e){report.passed=false;report.error=e.message;console.error('FAIL',e.message);process.exitCode=1;}
fs.mkdirSync('reports',{recursive:true});fs.writeFileSync('reports/published-mechanical-smoke.json',JSON.stringify(report,null,2));
