import {createRoom,person,action,tick,publicState,setConfig,catalog} from './engine.mjs';
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const clean=s=>String(s||'').replace(/[<>\x00-\x1f]/g,'').trim().slice(0,24);
const digest=async s=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),x=>x.toString(16).padStart(2,'0')).join('');
const code=()=>Array.from(crypto.getRandomValues(new Uint8Array(6)),n=>'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[n%32]).join('');

const accountId=async t=>typeof t==='string'&&t.length>=30&&t.length<=128?await digest('rift-profile-1:'+t):null;
const deltaFor=(position,total)=>position===1?(total===2?18:total===4?22:25):total===2?-12:position===2?-5:position<=Math.ceil(total/2)?-10:-16;
function finishPositions(s){const scores=s.members.map(m=>{
 const games=s.matches.filter(x=>x.winner&&(x.a===m.id||x.b===m.id));
 const rounds=games.filter(x=>x.stage==='playoffs'&&x.winner===m.id).map(x=>x.round);
 const points=games.filter(x=>x.winner===m.id).length;
 const gameDiff=games.reduce((acc,x)=>acc+(x.a===m.id?x.score[0]-x.score[1]:x.score[1]-x.score[0]),0);
 return{id:m.id,win:m.id===s.champion?1:0,top:rounds.length?Math.max(...rounds):0,points,gameDiff};
 });scores.sort((a,b)=>b.win-a.win||b.top-a.top||b.points-a.points||b.gameDiff-a.gameDiff);
 return Object.fromEntries(scores.map((x,i)=>[x.id,i+1]));
}
async function awardRanks(db,s){
 if(s.phase!=='finished')return;
 const positions=finishPositions(s),now=Date.now();
 for(const m of s.members.filter(x=>!x.bot&&x.rankId)){
  const place=positions[m.id]||s.members.length,delta=deltaFor(place,s.members.length),marker=s.code+':'+s.created+':'+m.id;
  const prior=await db.prepare('INSERT OR IGNORE INTO rank_awards (marker,profile_id,delta,placed,created_at) VALUES (?,?,?,?,?)').bind(marker,m.rankId,delta,place,now).run();
  if(!prior.meta.changes)continue;
  const existing=await db.prepare('SELECT * FROM rank_profiles WHERE id=?').bind(m.rankId).first();
  let score=(existing?.step??4)*100+(existing?.lp??0)+delta;score=Math.max(0,Math.min(3099,score));
  const step=Math.floor(score/100),lp=score%100;
  await db.prepare('INSERT INTO rank_profiles(id,name,step,lp,wins,losses,titles,updated_at) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,step=excluded.step,lp=excluded.lp,wins=rank_profiles.wins+excluded.wins,losses=rank_profiles.losses+excluded.losses,titles=rank_profiles.titles+excluded.titles,updated_at=excluded.updated_at')
   .bind(m.rankId,m.name,step,lp,place===1?1:0,place===1?0:1,place===1?1:0,now).run();
 }
}

export async function api(request,env){
 const url=new URL(request.url),path=url.pathname;try{
 if(!env.DB)return json({error:'O banco da sala está indisponível. O treino local continua funcionando.'},503);
 if(request.method==='POST'&&request.headers.get('Origin')&&request.headers.get('Origin')!==url.origin)return json({error:'Origem inválida.'},403);
 let body={};if(request.method==='POST'){if(!request.headers.get('content-type')?.includes('application/json'))return json({error:'Envie JSON.'},415);if(Number(request.headers.get('content-length')||0)>2048)return json({error:'Pedido muito grande.'},413);const raw=await request.text();if(raw.length>2048)return json({error:'Pedido muito grande.'},413);try{body=JSON.parse(raw);}catch{return json({error:'JSON inválido.'},400);}}
 const now=Date.now();
 if(path==='/api/profile'&&request.method==='GET'){
  const id=await accountId(request.headers.get('X-Profile-Token'));
  if(!id)return json({error:'Perfil anônimo inválido.'},400);
  const p=await env.DB.prepare('SELECT name,step,lp,wins,losses,titles,updated_at FROM rank_profiles WHERE id=?').bind(id).first();
  return json({profile:p||{name:'Equipe',step:4,lp:0,wins:0,losses:0,titles:0}});
 }
 if(path==='/api/leaderboard'&&request.method==='GET'){
 const results=await env.DB.prepare('SELECT name,step,lp,wins,losses,titles,updated_at FROM rank_profiles ORDER BY (step*100+lp) DESC,titles DESC,wins DESC LIMIT 100').bind().all();
 return json({leaders:results.results||[],serverNow:now});
 }
 if(path==='/api/presets'&&request.method==='GET'){
 const result=await env.DB.prepare('SELECT player_id,overall FROM rating_presets').bind().all();
 return json({ratings:Object.fromEntries((result.results||[]).map(x=>[x.player_id,x.overall]))});
 }
 if(path==='/api/presets'&&request.method==='POST'){
  const secret=env.ADMIN_PASSWORD;
  if(typeof secret!=='string'||secret.length<12)return json({error:'Admin global não configurado. Defina o secret ADMIN_PASSWORD nas configurações do Worker.'},503);
  const supplied=request.headers.get('X-Admin-Key')||'';
  if(supplied.length!==secret.length||await digest(supplied)!==await digest(secret))return json({error:'Senha de administrador global inválida.'},403);
  const playerId=String(body.playerId||''),base=catalog.get(playerId),overall=Number(body.overall);
  if(!base||!Number.isInteger(overall)||overall<40||overall>99)return json({error:'Jogador ou overall inválido.'},400);
  await env.DB.prepare('INSERT INTO rating_presets(player_id,overall,updated_at) VALUES (?,?,?) ON CONFLICT(player_id) DO UPDATE SET overall=excluded.overall,updated_at=excluded.updated_at').bind(playerId,overall,now).run();
  return json({ok:true,playerId,overall});
 }
 if(path==='/api/rooms'&&request.method==='POST'){
 const name=clean(body.name);if(!name)return json({error:'Escolha o nome da sua equipe.'},400);const ip=request.headers.get('CF-Connecting-IP')||'shared';const key=await digest(ip);const quota=await env.DB.prepare('SELECT count FROM rate_limits WHERE key=? AND window>?').bind(key,now-3600000).first();if((quota?.count||0)>=30)return json({error:'Muitas salas criadas. Volte mais tarde ou entre em uma sala existente.'},429);
 await env.DB.prepare('INSERT INTO rate_limits (key,window,count) VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN window<? THEN 1 ELSE count+1 END, window=CASE WHEN window<? THEN excluded.window ELSE window END').bind(key,now,now-3600000,now-3600000).run();
 const roomCode=code(),id=crypto.randomUUID(),token=crypto.randomUUID()+crypto.randomUUID(),s=createRoom(roomCode,id,name,crypto.getRandomValues(new Uint32Array(1))[0]);s.members[0].logo=typeof body.logo==='string'&&body.logo.length<=16?body.logo:'FUR';s.members[0].rankId=await accountId(body.profileToken);s.capacity=[2,4,8].includes(body.capacity)?body.capacity:4;setConfig(s,body.config||{});
 const presets=await env.DB.prepare('SELECT player_id,overall FROM rating_presets').bind().all();
 for(const x of presets.results||[]){const p=catalog.get(x.player_id);if(!p)continue;const diff=x.overall-p.overall;const adjust=k=>Math.max(40,Math.min(99,p[k]+diff));s.ratingOverrides[p.id]={overall:x.overall,micro:adjust('micro'),macro:adjust('macro'),mental:adjust('mental'),price:Math.max(3,Math.min(20,Math.round(5+(x.overall-65)*.45)))};}
 const auth={[await digest(token)]:id};await env.DB.prepare('INSERT INTO rooms (code,state,auth,version,updated_at,expires_at) VALUES (?,?,?,1,?,?)').bind(roomCode,JSON.stringify(s),JSON.stringify(auth),now,now+86400000).run();return json({token,id,state:publicState(s,id),serverNow:now},201);
 }
 const found=path.match(/^\/api\/rooms\/([A-Z2-9]{6})(?:\/(join|action))?$/);if(!found)return json({error:'Rota não encontrada.'},404);const roomCode=found[1],operation=found[2];
 for(let attempt=0;attempt<20;attempt++){
 const row=await env.DB.prepare('SELECT * FROM rooms WHERE code=? AND expires_at>?').bind(roomCode,now).first();if(!row)return json({error:'Sala não encontrada ou expirada (24 horas).'},404);const s=JSON.parse(row.state),auth=JSON.parse(row.auth);const bearer=request.headers.get('Authorization')?.replace(/^Bearer /,'')||'';const hash=bearer?await digest(bearer):'';let id=auth[hash],token;
 if(operation==='join'&&request.method==='POST'){
  if(!id){if(s.phase!=='lobby')return json({error:'O leilão já começou. Novas equipes entram na próxima sala.'},409);if(s.members.length>=s.capacity)return json({error:'Sala cheia.'},409);const name=clean(body.name);if(!name)return json({error:'Dê um nome à sua equipe.'},400);if(s.members.some(m=>m.name.toLowerCase()===name.toLowerCase()))return json({error:'Esse nome já está na sala.'},409);id=crypto.randomUUID();token=crypto.randomUUID()+crypto.randomUUID();auth[await digest(token)]=id;const member=person(id,name,false,body.logo);member.rankId=await accountId(body.profileToken);s.members.push(member);}
 }else{
  if(!id||!s.members.some(m=>m.id===id))return json({error:'Entre na sala para continuar.'},401);
  if(operation==='action'&&request.method==='POST')action(s,id,body,now);else if(!operation&&request.method==='GET')tick(s,now);else return json({error:'Método inválido.'},405);
 }
 const state=JSON.stringify(s),authText=JSON.stringify(auth);if(state!==row.state||authText!==row.auth){const update=await env.DB.prepare('UPDATE rooms SET state=?, auth=?, version=version+1, updated_at=? WHERE code=? AND version=?').bind(state,authText,now,roomCode,row.version).run();if(!update.meta.changes)continue;}
 if(s.phase==='finished')await awardRanks(env.DB,s);return json({state:publicState(s,id),id,...(token?{token}:{}),serverNow:now});
 }return json({error:'Muitos lances simultâneos; tente mais uma vez.',retryable:true},409);
 }catch(e){if(e.message?.includes('UNIQUE constraint'))return json({error:'Tente criar a sala novamente.'},409);console.error('Room API:',e.message);return json({error:e.message?.includes('D1')?'Não consegui salvar a sala. Tente novamente.':e.message||'Erro na sala.'},400);}
}
