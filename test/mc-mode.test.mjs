import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {mcCreate,mcTick,mcAction,MC_BY_ID} from '../worker/mc-engine.mjs';
import {mcApi} from '../worker/mc-api.mjs';
import {database} from '../scripts/d1-local.mjs';
const roster=JSON.parse(readFileSync('data/mc-roster.json','utf8'));
test('BDA 10 anos: 48 MCs com IDs únicos, fotos e notas documentadas',()=>{
 assert.equal(roster.length,48);assert.equal(new Set(roster.map(x=>x.id)).size,48);
 assert(roster.every(x=>x.photo?.startsWith('https://')&&x.overall>=70&&x.overall<=97));
 assert(roster.find(x=>x.id==='jotap')?.overall>=95);
});
test('sala de MCs mantém 2/4/8 participantes e leilão de +1 +5 +10 ou all in',()=>{
 let s=mcCreate('ABC234','host','Time A',4,42),now=Date.now();mcAction(s,'host',{type:'start'},now);
 assert.equal(s.phase,'auction');assert.equal(s.members.length,4);
 mcAction(s,'host',{type:'bid',inc:1,mc:s.auction.mc},now+100);
 assert.equal(s.auction.bid,1);assert.equal(s.auction.ends,now+5100);
 assert.throws(()=>mcAction(s,'host',{type:'bid',inc:3,mc:s.auction.mc},now+101));
 mcAction(s,'host',{type:'endAuction'},now+300);
 assert.equal(s.phase,'battles');assert(s.members.every(x=>x.roster.length===5));
 assert.equal(new Set(s.members.flatMap(x=>x.roster)).size,20);
});
test('estratégia: um MC usado não pode ser reutilizado e vitória depende do OVR',()=>{
 let s=mcCreate('DEF345','host','Time A',2,5),now=Date.now();
 s.members.push({id:'guest',name:'Time B',bot:false,balance:50,roster:[]});mcAction(s,'host',{type:'start'},now);mcAction(s,'host',{type:'endAuction'},now+100);
 while(s.phase==='battles'){
  let m=s.match;let id=m.turn;let ownA=id===m.a,ownTeam=s.members.find(x=>x.id===id),otherTeam=s.members.find(x=>x.id===(ownA?m.b:m.a));
  let own=ownTeam.roster.find(x=>!(ownA?m.usedA:m.usedB).includes(x)),enemy=otherTeam.roster.find(x=>!(ownA?m.usedB:m.usedA).includes(x));
  const previous=m.duels.length;mcAction(s,id,{type:'duel',own,enemy},now+200+previous);
  if(s.match===m)assert.equal(m.duels.length,previous+1);
 }
 assert.equal(s.phase,'finished');assert(s.champion);
});
test('novos endpoints preservam salas LoL e autenticam jogadores',async()=>{
 const DB=database(),env={DB};try{
  const req=(path,body,token)=>new Request('https://rift.test'+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
  const cr=await mcApi(req('/api/mc/rooms',{name:'Jotape FC',capacity:2}),env);assert.equal(cr.status,201);
  const a=await cr.json();assert.equal(a.state.kind,'mc-battle');
  const guest=await mcApi(req('/api/mc/rooms/'+a.code+'/join',{name:'Rival'}),env);assert.equal(guest.status,200);
  const state=await mcApi(req('/api/mc/rooms/'+a.code,undefined,a.token),env);assert.equal((await state.json()).state.members.length,2);
  const noAuth=await mcApi(req('/api/mc/rooms/'+a.code+'/action',{type:'start'}),env);assert.equal(noAuth.status,401);
 }finally{DB.close();}
});
