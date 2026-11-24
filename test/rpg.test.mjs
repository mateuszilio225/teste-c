import {test} from 'node:test';
import assert from 'node:assert/strict';
import {rpgCreate,rpgAction,rpgPublic,RPG_REGIONS,RPG_CLASSES} from '../worker/rpg-engine.mjs';
import {rpgApi} from '../worker/rpg-api.mjs';
function db(){const rooms=new Map();return{rooms,prepare(sql){return{bind(...args){return{async first(){const x=rooms.get(args[0]);return x&&x.expires_at>args[1]?{...x}:null;},async run(){if(sql.startsWith('INSERT')){const [code,state,auth,now,expires_at]=args;if(rooms.has(code))throw Error('UNIQUE constraint failed');rooms.set(code,{code,state,auth,version:1,updated_at:now,expires_at});return{meta:{changes:1}};}if(sql.startsWith('UPDATE')){const [state,auth,,expires_at,code,version]=args;const x=rooms.get(code);if(x&&x.version===version){Object.assign(x,{state,auth,version:version+1,expires_at});return{meta:{changes:1}};}return{meta:{changes:0}};}throw Error(sql);}};}};}};}
const request=(path,token,body)=>new Request('https://rift.test'+path,{method:body===undefined?'GET':'POST',headers:{...(token?{Authorization:'Bearer '+token}:{}),...(body===undefined?{}:{'Content-Type':'application/json'})},...(body===undefined?{}:{body:JSON.stringify(body)})});
const send=async(path,env,token,body)=>{const r=await rpgApi(request(path,token,body),env);return {status:r.status,...await r.json()};};
test('12 regiões, classes distintas e criação sem vazar informações do mestre',()=>{
 assert.equal(RPG_REGIONS.length,12);assert.equal(RPG_CLASSES.length,5);
 const s=rpgCreate('RPG123','gm','Narrador',{preset:'brumaria',capacity:3});
 assert.equal(s.players.length,0);assert.equal(s.phase,'lobby');
 const p=rpgPublic(s,'p');assert.equal(p.regions[1].secret,undefined);assert.equal(p.gmNotes,undefined);
 const gm=rpgPublic(s,'gm');assert.ok(gm.regions[1].secret);
});
test('mestre e jogador criam sala, ficha, sessão, cena, pistas, testes e retomam por token',async()=>{
 const env={DB:db()};const guide=await send('/api/rpg/guide',env);assert.equal(guide.status,200);assert.equal(guide.regions.length,12);
 const c=await send('/api/rpg/rooms',env,null,{name:'Mestre A',capacity:2,preset:'brumaria'});assert.equal(c.status,201);assert.equal(c.state.viewRole,'mestre');
 const u=await send('/api/rpg/rooms/'+c.code+'/join',env,null,{name:'Jogador A'});assert.equal(u.status,200);assert.equal(u.state.viewRole,'jogador');
 const path='/api/rpg/rooms/'+c.code+'/action';
 let x=await send(path,env,u.token,{type:'character',name:'Selene',classId:'investigador',origin:'Jornalista'});assert.equal(x.status,200);assert.equal(x.state.players[0].character.stats.mente,3);
 x=await send(path,env,c.token,{type:'start'});assert.equal(x.state.phase,'playing');
 x=await send(path,env,c.token,{type:'scene',region:'farol'});assert.equal(x.status,200);assert.equal(x.state.scene.region,'farol');assert.ok(x.state.revealed.includes('farol'));
 x=await send(path,env,u.token,{type:'scene',region:'abismo'});assert.notEqual(x.status,200);
 x=await send(path,env,c.token,{type:'clue',text:'Chave de prata',region:'farol'});assert.equal(x.state.clues.length,1);
 x=await send(path,env,c.token,{type:'requestRoll',playerId:u.id,attribute:'mente',dc:13});assert.equal(x.state.rollRequest.playerId,u.id);
 x=await send(path,env,u.token,{type:'roll'});assert.equal(x.state.rollRequest,null);assert.equal(x.state.log.at(-1).kind,'roll');
 x=await send(path,env,u.token,{type:'action',text:'Eu investigo as pegadas'});assert.equal(x.state.log.at(-1).kind,'action');
 x=await send('/api/rpg/rooms/'+c.code,env,c.token);assert.equal(x.state.viewRole,'mestre');assert.equal(x.state.clues[0].text,'Chave de prata');
 const noAuth=await send('/api/rpg/rooms/'+c.code,env);assert.equal(noAuth.status,401);
 const clash=await send('/api/rpg/rooms/'+c.code+'/join',env,null,{name:'Terceiro'});assert.equal(clash.status,409);
});
test('sanitização, GM apenas, fichas e limites',()=>{
 const s=rpgCreate('ABCD12','gm','Mestre');s.players.push({id:'p',name:'Pessoa',character:null});
 assert.throws(()=>rpgAction(s,'p',{type:'start'}),/mestre/);
 assert.throws(()=>rpgAction(s,'p',{type:'character',name:'A',classId:'guardiao',origin:'Jornalista'}),/Escolha/);
 rpgAction(s,'p',{type:'character',name:'Rafa',classId:'guardiao',origin:'Jornalista'});
 rpgAction(s,'gm',{type:'start'});
 assert.throws(()=>rpgAction(s,'p',{type:'notes',text:'Segredo'}),/mestre/);
 rpgAction(s,'gm',{type:'notes',text:'Segredo do vilão'});
 assert.equal(rpgPublic(s,'p').gmNotes,undefined);assert.equal(rpgPublic(s,'gm').gmNotes,'Segredo do vilão');
 rpgAction(s,'gm',{type:'resource',playerId:'p',key:'hp',delta:-3});assert.equal(s.players[0].character.hp,s.players[0].character.maxHp-3);
 rpgAction(s,'gm',{type:'item',playerId:'p',item:'Medalhão'});assert.ok(s.players[0].character.inventory.includes('Medalhão'));
 rpgAction(s,'gm',{type:'chapter',number:3});assert.equal(s.campaign.chapter,3);
});
