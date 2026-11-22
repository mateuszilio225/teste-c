import {createRoom,person,action,tick,publicState} from './engine.mjs';
const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const clean=s=>String(s||'').replace(/[<>\x00-\x1f]/g,'').trim().slice(0,24);
const digest=async s=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),x=>x.toString(16).padStart(2,'0')).join('');
const code=()=>Array.from(crypto.getRandomValues(new Uint8Array(6)),n=>'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[n%32]).join('');
export async function api(request,env){
 const url=new URL(request.url),path=url.pathname;try{
 if(!env.DB)return json({error:'O banco da sala está indisponível. O treino local continua funcionando.'},503);
 if(request.method==='POST'&&request.headers.get('Origin')&&request.headers.get('Origin')!==url.origin)return json({error:'Origem inválida.'},403);
 let body={};if(request.method==='POST'){if(!request.headers.get('content-type')?.includes('application/json'))return json({error:'Envie JSON.'},415);if(Number(request.headers.get('content-length')||0)>2048)return json({error:'Pedido muito grande.'},413);const raw=await request.text();if(raw.length>2048)return json({error:'Pedido muito grande.'},413);try{body=JSON.parse(raw);}catch{return json({error:'JSON inválido.'},400);}}
 const now=Date.now();
 if(path==='/api/rooms'&&request.method==='POST'){
 const name=clean(body.name);if(!name)return json({error:'Escolha o nome da sua equipe.'},400);const ip=request.headers.get('CF-Connecting-IP')||'shared';const key=await digest(ip);const quota=await env.DB.prepare('SELECT count FROM rate_limits WHERE key=? AND window>?').bind(key,now-3600000).first();if((quota?.count||0)>=30)return json({error:'Muitas salas criadas. Volte mais tarde ou entre em uma sala existente.'},429);
 await env.DB.prepare('INSERT INTO rate_limits (key,window,count) VALUES (?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN window<? THEN 1 ELSE count+1 END, window=CASE WHEN window<? THEN excluded.window ELSE window END').bind(key,now,now-3600000,now-3600000).run();
 const roomCode=code(),id=crypto.randomUUID(),token=crypto.randomUUID()+crypto.randomUUID(),s=createRoom(roomCode,id,name,crypto.getRandomValues(new Uint32Array(1))[0]);s.capacity=[2,4,8].includes(body.capacity)?body.capacity:4;const auth={[await digest(token)]:id};await env.DB.prepare('INSERT INTO rooms (code,state,auth,version,updated_at,expires_at) VALUES (?,?,?,1,?,?)').bind(roomCode,JSON.stringify(s),JSON.stringify(auth),now,now+86400000).run();return json({token,id,state:publicState(s,id),serverNow:now},201);
 }
 const found=path.match(/^\/api\/rooms\/([A-Z2-9]{6})(?:\/(join|action))?$/);if(!found)return json({error:'Rota não encontrada.'},404);const roomCode=found[1],operation=found[2];
 for(let attempt=0;attempt<5;attempt++){
 const row=await env.DB.prepare('SELECT * FROM rooms WHERE code=? AND expires_at>?').bind(roomCode,now).first();if(!row)return json({error:'Sala não encontrada ou expirada (24 horas).'},404);const s=JSON.parse(row.state),auth=JSON.parse(row.auth);const bearer=request.headers.get('Authorization')?.replace(/^Bearer /,'')||'';const hash=bearer?await digest(bearer):'';let id=auth[hash],token;
 if(operation==='join'&&request.method==='POST'){
  if(!id){if(s.phase!=='lobby')return json({error:'O leilão já começou. Novas equipes entram na próxima sala.'},409);if(s.members.length>=s.capacity)return json({error:'Sala cheia.'},409);const name=clean(body.name);if(!name)return json({error:'Dê um nome à sua equipe.'},400);if(s.members.some(m=>m.name.toLowerCase()===name.toLowerCase()))return json({error:'Esse nome já está na sala.'},409);id=crypto.randomUUID();token=crypto.randomUUID()+crypto.randomUUID();auth[await digest(token)]=id;s.members.push(person(id,name));}
 }else{
  if(!id||!s.members.some(m=>m.id===id))return json({error:'Entre na sala para continuar.'},401);
  if(operation==='action'&&request.method==='POST')action(s,id,body,now);else if(!operation&&request.method==='GET')tick(s,now);else return json({error:'Método inválido.'},405);
 }
 const state=JSON.stringify(s),authText=JSON.stringify(auth);if(state!==row.state||authText!==row.auth){const update=await env.DB.prepare('UPDATE rooms SET state=?, auth=?, version=version+1, updated_at=? WHERE code=? AND version=?').bind(state,authText,now,roomCode,row.version).run();if(!update.meta.changes)continue;}
 return json({state:publicState(s,id),id,...(token?{token}:{}),serverNow:now});
 }return json({error:'A sala recebeu vários lances juntos. Tente novamente.'},409);
 }catch(e){if(e.message?.includes('UNIQUE constraint'))return json({error:'Tente criar a sala novamente.'},409);console.error('Room API:',e.message);return json({error:e.message?.includes('D1')?'Não consegui salvar a sala. Tente novamente.':e.message||'Erro na sala.'},400);}
}
