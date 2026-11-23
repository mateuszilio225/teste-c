import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {api} from '../worker/api.mjs';
import {database} from '../scripts/d1-local.mjs';
import {PLAYERS,catalog} from '../worker/engine.mjs';
const defaults=JSON.parse(readFileSync(new URL('../data/official-overalls.json',import.meta.url),'utf8'));
const call=async(path,env,body,headers={})=>{
 const r=await api(new Request('https://rift.test'+path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...headers},...(body===undefined?{}:{body:JSON.stringify(body)})}),env);
 return {status:r.status,...await r.json()};
};
test('32 overalls oficiais batem exatamente com jogadores e posicoes',()=>{
 const expectedRoles={ADC:['duduhh','ayu','rabelo','morttheus','bao','jeskla','hena','strensh'],SUP:['ackerman','jojo','uzent','ceos','manel','momochi','scamber','shiku'],MID:['feisty','tutsz','kaze','mireu','namiru','fuuu','cody','enga'],JG:['curse','tatu','sinatra','disamis','stepz','cariok','peach','booki']};
 assert.equal(Object.keys(defaults).length,32);
 for(const [role,names] of Object.entries(expectedRoles))for(const id of names){
  assert.equal(catalog.get(id)?.role,role,'role '+id);
  assert.equal(catalog.get(id)?.overall,defaults[id],id);
 }
 assert.equal(PLAYERS.filter(p=>p.role==='TOP').length,8);
});
test('presets antigos ficam inativos; novo admin pode definir overrides de todas as proximas salas',async()=>{
 const DB=database(),env={DB,ADMIN_PASSWORD:'admin-test-secret-v6'};
 try{
  await DB.prepare('INSERT INTO rating_presets(player_id,overall,updated_at,revision) VALUES (?,?,?,0)').bind('duduhh',50,1).run();
  const old=await call('/api/presets',env);assert.equal(old.status,200);assert.equal(old.ratings.duduhh,undefined);
  const a=await call('/api/rooms',env,{name:'Equipe Padrão',capacity:2});
  assert.equal(a.status,201);assert.equal(a.state.ratingOverrides.duduhh,undefined);
  assert.equal(catalog.get('duduhh').overall,88);
  const save=await call('/api/presets',env,{playerId:'duduhh',overall:92},{'X-Admin-Key':env.ADMIN_PASSWORD});assert.equal(save.status,200);
  const now=await call('/api/presets',env);assert.equal(now.ratings.duduhh,92);
  const b=await call('/api/rooms',env,{name:'Equipe Customizada',capacity:2});assert.equal(b.status,201);assert.equal(b.state.ratingOverrides.duduhh.overall,92);
 }finally{DB.close();}
});
