import {mcCreate,mcAction,mcTick,mcPublic} from './mc-engine.mjs';
const mcRespond=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'no-store'}});
const mcSha=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),x=>x.toString(16).padStart(2,'0')).join('');
const mcCode=()=>Array.from(crypto.getRandomValues(new Uint8Array(6)),x=>'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[x%32]).join('');
const mcClean=s=>String(s||'').replace(/[<>\x00-\x1f]/g,'').trim().slice(0,26);
export async function mcApi(req,env){const url=new URL(req.url);if(!env.DB)return mcRespond({error:'Banco D1 indisponível.'},503);
 if(req.method==='POST'&&req.headers.get('Origin')&&req.headers.get('Origin')!==url.origin)return mcRespond({error:'Origem inválida.'},403);
 let body={};if(req.method==='POST'){if(!req.headers.get('content-type')?.includes('application/json'))return mcRespond({error:'JSON obrigatório.'},415);let raw=await req.text();if(raw.length>2500)return mcRespond({error:'Pedido muito grande.'},413);try{body=JSON.parse(raw);}catch{return mcRespond({error:'JSON inválido.'},400);}}
 const now=Date.now();let path=url.pathname;
 try{
 if(path==='/api/mc/rooms'&&req.method==='POST'){
 let name=mcClean(body.name);if(!name)return mcRespond({error:'Informe o nome da equipe.'},400);
 const capacity=[2,4,8].includes(body.capacity)?body.capacity:2;
 for(let trial=0;trial<6;trial++){
 const c=mcCode(),id=crypto.randomUUID(),token=crypto.randomUUID()+crypto.randomUUID(),s=mcCreate(c,id,name,capacity,crypto.getRandomValues(new Uint32Array(1))[0]);let auth={[await mcSha(token)]:id};
 try{await env.DB.prepare('INSERT INTO rooms(code,state,auth,version,updated_at,expires_at) VALUES(?,?,?,1,?,?)').bind(c,JSON.stringify(s),JSON.stringify(auth),now,now+86400000).run();return mcRespond({code:c,id,token,state:mcPublic(s,id),serverNow:now},201);}catch(e){if(!/UNIQUE/i.test(String(e)))throw e;}}
 return mcRespond({error:'Não foi possível criar a sala, tente novamente.'},503);
 }
 const match=path.match(/^\/api\/mc\/rooms\/([A-Z2-9]{6})(?:\/(join|action))?$/);if(!match)return mcRespond({error:'Rota inválida.'},404);const roomCode=match[1],operation=match[2],bearer=(req.headers.get('Authorization')||'').replace(/^Bearer /,'');const tokenHash=bearer?await mcSha(bearer):'';
 for(let attempt=0;attempt<18;attempt++){
  const db=await env.DB.prepare('SELECT * FROM rooms WHERE code=? AND expires_at>?').bind(roomCode,now).first();if(!db)return mcRespond({error:'Sala expirada ou não encontrada.'},404);
  const s=JSON.parse(db.state);if(s.kind!=='mc-battle')return mcRespond({error:'Esta é uma sala de LoL.'},400);
  const auth=JSON.parse(db.auth);let id=auth[tokenHash],newToken;
  if(operation==='join'&&req.method==='POST'){
   if(!id){if(s.phase!=='lobby'||s.members.length>=s.capacity)return mcRespond({error:'A sala já começou ou está cheia.'},409);
    let name=mcClean(body.name);if(!name||s.members.some(m=>m.name.toLowerCase()===name.toLowerCase()))return mcRespond({error:'Escolha um nome diferente.'},409);
    id=crypto.randomUUID();newToken=crypto.randomUUID()+crypto.randomUUID();auth[await mcSha(newToken)]=id;s.members.push({id,name,bot:false,balance:50,roster:[]});}
  }else{if(!id||!s.members.some(m=>m.id===id))return mcRespond({error:'Entre nesta sala primeiro.'},401);
   if(operation==='action'&&req.method==='POST'){mcTick(s,now);mcAction(s,id,body,now);}
   else if(!operation&&req.method==='GET')mcTick(s,now);else return mcRespond({error:'Método não permitido.'},405);}
  let state=JSON.stringify(s),authString=JSON.stringify(auth);
  if(state!==db.state||authString!==db.auth){const change=await env.DB.prepare('UPDATE rooms SET state=?,auth=?,version=version+1,updated_at=? WHERE code=? AND version=?').bind(state,authString,now,roomCode,db.version).run();if(!change.meta.changes)continue;}
  return mcRespond({state:mcPublic(s,id),id,...(newToken?{token:newToken}:{}),serverNow:now});
 }
 return mcRespond({error:'Conflito entre lances. Tente novamente.',retryable:true},409);
 }catch(e){return mcRespond({error:e.message||'Erro na sala.'},400);}
}
