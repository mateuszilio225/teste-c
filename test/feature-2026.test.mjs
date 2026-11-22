import {test} from 'node:test';
import assert from 'node:assert/strict';
import {CBLOL_DRAFTS,ALL_DRAFTS,ROLES,createRoom,person,action,tick,publicState,catalog} from '../worker/engine.mjs';

function testMode(draftPool){const s=createRoom('AAB234','host','Time Host',123);s.capacity=2;s.config.draftPool=draftPool;s.members.push(person('other','Time Convidado'));
 action(s,'host',{type:'start'},100);let now=100;
 for(let i=0;i<250&&s.phase==='auction';i++){
  const card=catalog.get(s.auction.card),buyer=s.members.find(m=>!m.roster[card.role]);
  action(s,buyer.id,{type:'bid',card:card.id,amount:1},++now);action(s,'host',{type:'speed'},++now);
 }
 assert.equal(s.phase,'tournament');
 const offers=Object.values(s.series.offers).flat();assert.equal(offers.length,4);
 assert.ok(offers.every(d=>draftPool==='worlds'?d.event==='Worlds 2026':draftPool==='cblol'?d.event.startsWith('CBLOL'):true));
 return{s,now};
}
test('36 CBLOL compos reais: IDs unicos, 5 funções e 4 packs Fearless',()=>{
 assert.equal(CBLOL_DRAFTS.length,36);assert.equal(new Set(ALL_DRAFTS.map(d=>d.id)).size,ALL_DRAFTS.length);
 const packs=Object.groupBy(CBLOL_DRAFTS,d=>d.series);assert.equal(Object.keys(packs).length,4);
 for(const drafts of Object.values(packs)){
  assert.ok(drafts.length>=8);const picked=drafts.flatMap(d=>Object.values(d.champions));assert.equal(picked.length,new Set(picked).size);
  for(const d of drafts){assert.deepEqual(Object.keys(d.champions),ROLES);assert.match(d.source,/^https:\/\/riftwise\.gg/);assert.equal(d.event,'CBLOL 2026 Split 2');}
 }
});
test('modo CBLOL, Worlds ou misto entrega quatro opções reais',()=>{
 for(const mode of ['cblol','worlds','mixed']){const {s,now}=testMode(mode);assert.equal(s.series.deadline-now,10000);}
});
test('a cada lance, timer reinicia para 3 segundos exatos',()=>{
 const s=createRoom('AAB234','host','Host',5);s.capacity=2;s.members.push(person('guest','Guest'));
 action(s,'host',{type:'start'},100);assert.equal(s.auction.ends,10100);
 const card=s.auction.card;
 action(s,'host',{type:'bid',card,amount:1},500);assert.equal(s.auction.ends,3500);
 action(s,'guest',{type:'bid',card,amount:2},600);assert.equal(s.auction.ends,3600);
 tick(s,3601);assert.ok(s.sold.includes(card));
});
test('editor autorizado altera notas só nesta sala, sem autorização rejeita',()=>{
 const s=createRoom('AAB234','host','Host',123);s.members.push(person('guest','Convidado'));
 const base=catalog.get('tatu');assert.ok(base);
 assert.throws(()=>action(s,'guest',{type:'rating',playerId:'tatu',overall:92},100),/permissão/);
 action(s,'host',{type:'editor',memberId:'guest',enabled:true},101);
 action(s,'guest',{type:'rating',playerId:'tatu',overall:92},102);
 assert.equal(s.ratingOverrides.tatu.overall,92);assert.equal(publicState(s,'guest').ratingOverrides.tatu.overall,92);
 assert.equal(catalog.get('tatu').overall,base.overall);
 action(s,'host',{type:'editor',memberId:'guest',enabled:false},103);
 assert.throws(()=>action(s,'guest',{type:'rating',playerId:'tatu',overall:50},104),/permissão/);
 assert.throws(()=>action(s,'host',{type:'rating',playerId:'tatu',overall:101},105),/40 e 99/);
 const other=createRoom('AAB235','new','Outro time');assert.deepEqual(other.ratingOverrides,{});
});
