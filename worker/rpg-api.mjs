import {rpgCreate,rpgAction,rpgPublic,RPG_CLASSES,RPG_ORIGINS,RPG_PRESETS,RPG_REGIONS} from './rpg-engine.mjs';
const reply=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const hash=async t=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(t))),x=>x.toString(16).padStart(2,'0')).join('');
const genCode=()=>Array.from(crypto.getRandomValues(new Uint8Array(6)),n=>'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[n%32]).join('');
const rpgApiClean=(t,max)=>String(t??'').replace(/[<>\x00-\x1f]/g,'').trim().slice(0,max);
const roll20=()=>{const b=new Uint32Array(1);crypto.getRandomValues(b);return 1+b[0]%20;};
export async function rpgApi(req,env){
 const {pathname:path,origin}=new URL(req.url);
 if(path==='/api/rpg/guide'&&req.method==='GET')return reply({classes:RPG_CLASSES,origins:RPG_ORIGINS,presets:RPG_PRESETS,regions:RPG_REGIONS.map(({secret,clue,choices,...rest})=>rest)});
 if(!env.DB)return reply({error:'O banco D1 está indisponível para o RPG.'},503);
 if(req.method==='POST'&&req.headers.get('Origin')&&req.headers.get('Origin')!==origin)return reply({error:'Origem inválida.'},403);
 let data={};if(req.method==='POST'){
  if(!req.headers.get('content-type')?.includes('application/json'))return reply({error:'Envie JSON.'},415);
  const raw=await req.text();if(raw.length>3600)return reply({error:'Pedido grande demais.'},413);
  try{data=JSON.parse(raw);}catch{return reply({error:'JSON inválido.'},400);}
 }
 const now=Date.now(),expiration=now+30*86400000;
 try{
 if(path==='/api/rpg/rooms'&&req.method==='POST'){
  const name=rpgApiClean(data.name,26);if(name.length<2)return reply({error:'Informe o nome do mestre.'},400);
  for(let i=0;i<6;i++){
   const code=genCode(),id=crypto.randomUUID(),token=crypto.randomUUID()+crypto.randomUUID();
   const room=rpgCreate(code,id,name,data);
   const auth={[await hash(token)]:id};
   try{
    await env.DB.prepare('INSERT INTO rooms(code,state,auth,version,updated_at,expires_at) VALUES (?,?,?,1,?,?)').bind(code,JSON.stringify(room),JSON.stringify(auth),now,expiration).run();
    return reply({code,id,token,state:rpgPublic(room,id),version:1},201);
   }catch(e){if(!String(e.message||e).includes('UNIQUE'))throw e;}
  }
  return reply({error:'Não foi possível criar a campanha.'},503);
 }
 const match=path.match(/^\/api\/rpg\/rooms\/([A-Z2-9]{6})(?:\/(join|action))?$/);if(!match)return reply({error:'Rota não encontrada.'},404);
 const [,code,op]=match,bearer=(req.headers.get('Authorization')||'').replace(/^Bearer /,''),key=bearer?await hash(bearer):'';
 for(let attempt=0;attempt<18;attempt++){
  const row=await env.DB.prepare('SELECT * FROM rooms WHERE code=? AND expires_at>?').bind(code,now).first();
  if(!row)return reply({error:'Sala não encontrada ou expirada.'},404);
  const room=JSON.parse(row.state),auth=JSON.parse(row.auth);
  if(room.kind!=='rift-rpg')return reply({error:'Essa sala pertence a outro modo do Rift Draft.'},400);
  let actor=auth[key],newToken;
  if(op==='join'&&req.method==='POST'){
   if(!actor){
    if(room.phase!=='lobby')return reply({error:'A campanha já começou. O mestre pode criar outra sala para novos jogadores.'},409);
    if(room.players.length>=room.capacity)return reply({error:'Mesa cheia.'},409);
    const name=rpgApiClean(data.name,26);if(name.length<2||room.players.some(p=>p.name.toLowerCase()===name.toLowerCase())||room.gm.name.toLowerCase()===name.toLowerCase())return reply({error:'Escolha outro nome de jogador.'},400);
    actor=crypto.randomUUID();newToken=crypto.randomUUID()+crypto.randomUUID();auth[await hash(newToken)]=actor;
    room.players.push({id:actor,name,character:null});
   }
  }else{
   if(!actor||actor!==room.gm.id&&!room.players.some(p=>p.id===actor))return reply({error:'Entre nesta campanha antes de continuar.'},401);
   if(op==='action'&&req.method==='POST')rpgAction(room,actor,data,roll20);
   else if(op||req.method!=='GET')return reply({error:'Método não permitido.'},405);
  }
  const state=JSON.stringify(room),authorization=JSON.stringify(auth);
  let version=row.version;
  if(state!==row.state||authorization!==row.auth){
   const result=await env.DB.prepare('UPDATE rooms SET state=?,auth=?,version=version+1,updated_at=?,expires_at=? WHERE code=? AND version=?').bind(state,authorization,now,expiration,code,row.version).run();
   if(!result.meta.changes)continue;
   version++;
  }
  return reply({state:rpgPublic(room,actor),id:actor,...(newToken?{token:newToken}:{}),version});
 }
 return reply({error:'A mesa recebeu ações simultâneas. Tente novamente.',retryable:true},409);
 }catch(e){console.error('RPG API:',e.message);return reply({error:e.message||'Falha na campanha.'},400);}
}
