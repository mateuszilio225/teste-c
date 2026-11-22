import {test} from 'node:test';import assert from 'node:assert/strict';
import {api} from '../worker/api.mjs';import {database} from '../scripts/d1-local.mjs';import {catalog} from '../worker/engine.mjs';
test('duas sessões persistem ordens privadas, resolvem simultaneamente e recusam replay de rodada antiga',async()=>{
 const DB=database(),env={DB},realNow=Date.now;let clock=realNow();Date.now=()=>clock;
 const req=async(path,body,token)=>{const r=await api(new Request('https://tactics.test'+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})}),env);return{status:r.status,...await r.json()};};
 try{
 const h=await req('/api/rooms',{name:'Tático A',capacity:2,config:{gameplay:'mechanical',format:'knockout',supply:'exact'}}),path='/api/rooms/'+h.state.code,g=await req(path+'/join',{name:'Tático B'});assert.equal(h.status,201);assert.equal(g.status,200);let s=(await req(path+'/action',{type:'start'},h.token)).state;
 for(let i=0;i<15&&s.phase==='auction';i++){const card=catalog.get(s.auction.card),buyer=!s.members.find(m=>m.id===h.id).roster[card.role]?h:g;assert.equal((await req(path+'/action',{type:'bid',card:card.id,amount:1},buyer.token)).status,200);s=(await req(path+'/action',{type:'speed'},h.token)).state;}
 for(const p of [h,g])s=(await req(path+'/action',{type:'choose',option:0,match:s.series.match,game:1},p.token)).state;
 assert.equal(s.series.stage,'tactics');const hview=(await req(path,undefined,h.token)).state,gview=(await req(path,undefined,g.token)).state;
 const plan=(v,x,y)=>({type:'orders',match:v.series.match,game:v.series.game,turn:v.series.tactics.turn,orders:{units:v.series.tactics.units.filter(u=>u.side===v.series.tactics.side).map(u=>({role:u.role,x,y,stance:'engage',buy:u.role==='JG'&&u.gold>=3&&u.items.length<3?'blade':null,target:null})),ward:null}});
 const hp=plan(hview,50,50),gp=plan(gview,65,65);let r=await req(path+'/action',hp,h.token);assert.equal(r.status,200,r.error);assert.equal(r.state.series.tactics.phase,'planning');const hidden=(await req(path,undefined,g.token)).state.series.tactics;assert.equal(hidden.myOrders,null);assert.equal(hidden.orders,undefined);assert.equal(hidden.locked[h.id],true);assert.ok(hidden.units.every(u=>u.side===hidden.side));
 r=await req(path+'/action',gp,g.token);assert.equal(r.status,200,r.error);assert.equal(r.state.series.tactics.phase,'replay');const before=(await req(path,undefined,h.token)).state.series.tactics;assert.equal(before.report.length,0);assert.equal(before.orders,undefined);assert.equal(before.frames.length,1);
 clock=r.state.series.tactics.deadline+1;r=await req(path,undefined,h.token);assert.equal(r.state.series.tactics.turn,2);assert.equal(r.state.series.tactics.phase,'planning');assert.equal(r.state.series.tactics.units.find(u=>u.side===r.state.series.tactics.side&&u.role==='JG').gold,1);assert.equal((await req(path+'/action',hp,h.token)).status,400);
 // Both confirmations race against the same persisted D1 room version.
 const gv=(await req(path,undefined,g.token)).state,results=await Promise.all([req(path+'/action',plan(r.state,50,50),h.token),req(path+'/action',plan(gv,65,65),g.token)]);assert.ok(results.every(r=>r.status===200));const after=(await req(path,undefined,h.token)).state.series.tactics;assert.equal(after.phase,'replay');assert.equal(after.turn,2);
 }finally{Date.now=realNow;DB.close();}
});
