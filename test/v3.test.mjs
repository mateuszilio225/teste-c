import {test} from 'node:test';
import assert from 'node:assert/strict';
import {api} from '../worker/api.mjs';
import {database} from '../scripts/d1-local.mjs';
import {PLAYERS,ROLES,catalog,createRoom,person,action,tick,chemistry,power} from '../worker/engine.mjs';

function req(path,body,token,headers={}){return new Request('https://rift.test'+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(token?{Authorization:'Bearer '+token}:{}),...headers},...(body===undefined?{}:{body:JSON.stringify(body)})});}
async function call(path,env,body,token,headers){const r=await api(req(path,body,token,headers),env);return {status:r.status,...await r.json()};}

test('overalls fornecidos são padrão de 32 jogadores; Shini não aparece; foto do Dynquedo fica só na capa',()=>{
 const expected={duduhh:88,ayu:86,rabelo:82,morttheus:84,bao:80,jeskla:80,hena:77,strensh:75,ackerman:89,jojo:88,uzent:85,ceos:83,manel:82,momochi:81,scamber:79,shiku:77,feisty:90,tutsz:86,kaze:84,mireu:83,namiru:81,fuuu:80,cody:80,enga:76,curse:88,tatu:87,sinatra:84,disamis:84,stepz:83,cariok:80,peach:79,booki:78};
 for(const [id,rating] of Object.entries(expected))assert.equal(catalog.get(id)?.overall,rating,id);
 assert.equal(PLAYERS.some(x=>x.id==='shini'),false);
 assert.equal(PLAYERS.some(x=>x.id==='dynquedo'),false);
});

test('botões de incremento usam preço atual, incluindo disputa simultânea; reset é 5s',async()=>{
 const DB=database(),env={DB};try{
 const h=await call('/api/rooms',env,{name:'T1',capacity:2}),g=await call('/api/rooms/'+h.state.code+'/join',env,{name:'T2'}),path='/api/rooms/'+h.state.code+'/action';
 const start=await call(path,env,{type:'start'},h.token);const card=start.state.auction.card;
 const attempts=await Promise.all([call(path,env,{type:'bid',increment:1,card},h.token),call(path,env,{type:'bid',increment:5,card},g.token)]);
 assert.ok(attempts.every(x=>x.status===200),JSON.stringify(attempts.map(x=>x.error)));
 const last=await call('/api/rooms/'+h.state.code,env,undefined,h.token);
 assert.equal(last.state.auction.bid,6);
 assert.equal(last.state.auction.leader,g.id===last.state.auction.leader?g.id:h.id);
 assert.equal(last.state.auction.ends-last.state.auction.startedAt,5000);
 const m=last.state.members.find(x=>x.id===h.id),n=last.state.members.find(x=>x.id===g.id);
 assert.equal(m.spent+n.spent,0);
 }finally{DB.close();}
});

test('leilão sem compras completa todas as posições com sorteio sem duplicar cartas',()=>{
 const s=createRoom('AAA222','host','A',23);s.capacity=2;s.config.supply='exact';s.members.push(person('guest','B'));
 action(s,'host',{type:'start'},100);
 let now=100;
 for(let i=0;i<80&&s.phase==='auction';i++){now=s.auction.ends+1;tick(s,now);}
 assert.equal(s.phase,'tournament');const ids=s.members.flatMap(m=>Object.values(m.roster));assert.equal(ids.length,10);assert.equal(new Set(ids).size,10);
 assert.ok(s.members.every(m=>ROLES.every(r=>m.roster[r])));assert.ok(s.members.every(m=>m.spent===0&&m.autoRoster.length===5));
});

test('entrosamento por clube/nacionalidade dá bônus pequeno e overall permanece dominante',()=>{
 const s=createRoom('AAA223','h','A',45);const mk=(ids)=>Object.fromEntries(ROLES.map((r,i)=>[r,ids[i]]));
 // team FUR: Guigo, Tatu, Tutsz, Ayu, JoJo
 const m=person('a','A');m.roster=mk(['guigo','tatu','tutsz','ayu','jojo']);
 const c=chemistry(m,s);assert.equal(c.points,15);assert.ok(c.bonus>0&&c.bonus<=2.6);
 const two=person('b','B');two.roster=mk(['boal','curse','kaze','bao','scamber']);
 const cb=chemistry(two,s);assert.ok(cb.points<c.points);
});

test('admin secreto salva padrão global e rank geral é atualizado só uma vez no servidor',async()=>{
 const DB=database(),env={DB,ADMIN_PASSWORD:'a-very-long-test-admin-secret'};try{
  let r=await call('/api/presets',env,{playerId:'tatu',overall:95},null,{'X-Admin-Key':'wrong'});assert.equal(r.status,403);
  r=await call('/api/presets',env,{playerId:'tatu',overall:93},null,{'X-Admin-Key':env.ADMIN_PASSWORD});assert.equal(r.status,200);
  const presets=await call('/api/presets',env);assert.equal(presets.ratings.tatu,93);
  const a=await call('/api/rooms',env,{name:'Time-A',capacity:2,profileToken:'secure-player-token-aaaaaaaaaaaaaaaa'});
  assert.equal(a.status,201);assert.equal(a.state.ratingOverrides.tatu.overall,93);assert.equal(a.state.members[0].rankId,undefined);
  const b=await call('/api/rooms/'+a.state.code+'/join',env,{name:'Time-B',profileToken:'secure-player-token-bbbbbbbbbbbbbbbb'});
  const row=await DB.prepare('SELECT * FROM rooms WHERE code=?').bind(a.state.code).first();
  const state=JSON.parse(row.state);state.phase='finished';state.champion=a.id;state.matches=[{stage:'playoffs',round:1,a:a.id,b:b.id,winner:a.id,score:[2,1]}];state.series=null;
  await DB.prepare('UPDATE rooms SET state=?,version=version+1 WHERE code=?').bind(JSON.stringify(state),a.state.code).run();
  await call('/api/rooms/'+a.state.code,env,undefined,a.token);
  await call('/api/rooms/'+a.state.code,env,undefined,b.token);
  const leaders=await call('/api/leaderboard',env);assert.equal(leaders.leaders.length,2);assert.equal(leaders.leaders[0].name,'Time-A');assert.equal(leaders.leaders[0].lp,18);assert.equal(leaders.leaders[1].lp,88);
  const profile=await call('/api/profile',env,undefined,null,{'X-Profile-Token':'secure-player-token-aaaaaaaaaaaaaaaa'});assert.equal(profile.profile.titles,1);
  const awards=await DB.prepare('SELECT marker FROM rank_awards').bind().all();assert.equal(awards.results.length,2);
 }finally{DB.close();}
});
