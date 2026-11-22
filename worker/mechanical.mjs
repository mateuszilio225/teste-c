// Deterministic, simultaneous tactical rules. Coordinates and item numbers are
// deliberately a small board-game model, rather than live League patch data.
export const TACTICAL_ITEMS={
 blade:{name:'Lâmina',cost:3,damage:3,armor:0,range:0,vision:0,description:'+3 dano; ataques passam a ser físicos'},
 focus:{name:'Foco arcano',cost:3,damage:2,armor:0,range:2,vision:0,description:'+2 dano, +2 alcance; ataques passam a ser mágicos'},
 armor:{name:'Couraça',cost:3,damage:0,armor:5,range:0,vision:0,description:'−5 dano físico recebido (mínimo 2)'},
 veil:{name:'Véu',cost:3,damage:0,armor:0,resist:5,range:0,vision:0,description:'−5 dano mágico recebido (mínimo 2)'},
 lens:{name:'Lente',cost:2,damage:0,armor:0,range:0,vision:9,description:'+9 raio de visão; revela aproximações'},
 boots:{name:'Botas',cost:2,damage:0,armor:0,range:0,vision:0,speed:1,description:'+6 de deslocamento por rodada'}
};
export const TACTICAL_STANCES={farm:'Farmar',engage:'Iniciar',poke:'Poke',protect:'Proteger',retreat:'Recuar'};
export const TACTICAL_SITES=[{id:'top',name:'Rota superior',x:20,y:20},{id:'mid',name:'Rota do meio',x:50,y:50},{id:'bot',name:'Rota inferior',x:80,y:80},{id:'baron',name:'Larvas / Barão',x:35,y:35},{id:'dragon',name:'Dragão / Ancião',x:65,y:65}];
const MECH_ROLES=['TOP','JG','MID','ADC','SUP'];
const MECH_BASES=[{x:12,y:88},{x:88,y:12}];
const MECH_ROLE={TOP:{damage:13,range:11,armor:3,type:'physical'},JG:{damage:14,range:11,armor:2,type:'physical'},MID:{damage:16,range:17,armor:0,type:'magic'},ADC:{damage:17,range:17,armor:0,type:'physical'},SUP:{damage:10,range:13,armor:2,type:'magic'}};
const mechDistance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
const mechRound=n=>Math.round(n*10)/10;
const mechStat=(u,key)=>u.items.reduce((v,id)=>v+(TACTICAL_ITEMS[id][key]||0),0);
const mechAlive=u=>u.hp>0;
const mechVision=u=>24+mechStat(u,'vision')+Math.max(-1,Math.min(1,(u.macro-75)/10));
const mechHome=u=>MECH_BASES[u.side];
const mechVisible=(g,side,u)=>u.side===side||g.units.some(a=>a.side===side&&mechAlive(a)&&mechDistance(a,u)<=mechVision(a))||g.wards.some(w=>w.side===side&&w.until>=g.turn&&mechDistance(w,u)<=25);
function mechViewUnits(g,side){return g.units.filter(u=>side===null||mechVisible(g,side,u)).map(u=>structuredClone(u));}
function mechRemember(g){for(const side of [0,1])for(const u of g.units)if(u.side!==side&&mechVisible(g,side,u))g.lastSeen[side][u.id]={id:u.id,role:u.role,champ:u.champ,side:u.side,x:u.x,y:u.y,turn:g.turn,hp:u.hp};}
export function createTactics(teams,comps,players,now){
 const g={turn:1,phase:'planning',deadline:now+60000,botAt:now+2500,teams:teams.map(t=>t.id),comps,units:[],orders:{},locked:{},score:[0,0],kills:[0,0],nexus:[100,100],towers:[0,0],wards:[],lastSeen:[{},{}],sites:TACTICAL_SITES.map(s=>({...s,cooldown:0,pressure:[0,0]})),report:[],history:[],frames:[],winner:null};
 for(const [side,t] of teams.entries())for(const [i,role] of MECH_ROLES.entries()){
  const p=players.get(t.roster[role]),base=MECH_BASES[side],spread=(i-2)*2;
  g.units.push({id:side+'-'+role,side,role,champ:comps[side].champions[role],player:p.name,x:base.x+spread,y:base.y+spread,hp:100,gold:4,items:[],respawn:0,kills:0,skill:Math.round(Math.max(.97,Math.min(1.03,1+(p.micro-75)/500))*1000)/1000,macro:mechRound(p.macro),mental:p.mental,penalty:Math.max(-.02,(t.penalties[p.id]||0)/400)});
 }
 mechRemember(g);return g;
}
export function defaultTacticalOrders(g,side){return {units:g.units.filter(u=>u.side===side).map(u=>({role:u.role,x:u.x,y:u.y,stance:'farm',target:null,buy:null})),ward:null};}
export function validateTacticalOrders(g,side,input){
 if(!input||!Array.isArray(input.units)||input.units.length!==5)throw new Error('Defina uma ordem para cada um dos cinco campeões.');
 const seen=new Set(),units=input.units.map(o=>{
  if(!o||!MECH_ROLES.includes(o.role)||seen.has(o.role))throw new Error('Posições de campeões inválidas.');seen.add(o.role);
  if(!Number.isFinite(o.x)||!Number.isFinite(o.y)||o.x<3||o.x>97||o.y<3||o.y>97||!TACTICAL_STANCES[o.stance])throw new Error('Destino ou postura inválida.');
  const u=g.units.find(u=>u.side===side&&u.role===o.role),item=TACTICAL_ITEMS[o.buy];
  if(o.buy&&(!item||u.gold<item.cost||u.items.length>=3))throw new Error('Compra inválida: confira o ouro e os três espaços da build.');
  if(o.target&&!g.units.some(e=>e.side!==side&&e.role===o.target&&mechAlive(e)&&mechVisible(g,side,e)))throw new Error('O alvo precisa estar visível ao confirmar.');
  return{role:o.role,x:mechRound(o.x),y:mechRound(o.y),stance:o.stance,target:o.target||null,buy:o.buy||null};
 });
 let ward=null;if(input.ward){const w=input.ward;if(!Number.isFinite(w.x)||!Number.isFinite(w.y)||w.x<3||w.x>97||w.y<3||w.y>97||!g.units.some(u=>u.side===side&&mechAlive(u)&&mechDistance(u,w)<=22))throw new Error('Coloque a sentinela a até 22 de um aliado vivo.');ward={x:mechRound(w.x),y:mechRound(w.y)};}
 return{units,ward};
}
export function commitTacticalOrders(g,id,input,turn,now){const side=g.teams.indexOf(id);if(side<0)throw new Error('Só as equipes deste confronto podem dar ordens.');if(g.phase!=='planning'||turn!==g.turn||now>=g.deadline)throw new Error('A rodada mudou. Revise suas ordens.');if(g.locked[id])throw new Error('Suas ordens já estão confirmadas.');g.orders[id]=validateTacticalOrders(g,side,input);g.locked[id]=true;}
export function tacticalBotOrders(g,side){
 // Only the bot's own information is consulted. Never reads the other orders.
 const v=tacticalView(g,g.teams[side]),visible=v.units.filter(u=>u.side!==side&&mechAlive(u));
 const active=g.sites.filter(s=>s.cooldown<=g.turn),target=active.find(s=>s.id===(g.turn<7?'dragon':g.turn<13?'baron':'dragon'))||active.find(s=>s.id==='mid')||active[0];
 const p=defaultTacticalOrders(g,side);for(const [i,o] of p.units.entries()){
  const u=g.units.find(u=>u.side===side&&u.role===o.role),enemy=visible.filter(e=>mechDistance(u,e)<24).sort((a,b)=>a.hp-b.hp)[0];
  const danger=visible.filter(e=>mechDistance(u,e)<24).length>g.units.filter(a=>a.side===side&&mechAlive(a)&&mechDistance(u,a)<24).length;
  const dest=u.hp<32||danger?MECH_BASES[side]:enemy||target;
  o.x=Math.max(3,Math.min(97,dest.x+(i-2)*2));o.y=Math.max(3,Math.min(97,dest.y-(i-2)*2));o.stance=u.hp<32?'retreat':o.role==='SUP'?'protect':enemy?'engage':'farm';o.target=enemy?.role||null;
  if(u.items.length<3){const item=o.role==='TOP'||o.role==='SUP'?'armor':o.role==='MID'?'focus':'blade';if(u.gold>=TACTICAL_ITEMS[item].cost)o.buy=item;}
 }
 const scout=g.units.find(u=>u.side===side&&u.role==='SUP'&&mechAlive(u));if(scout)p.ward={x:scout.x,y:scout.y};return p;
}
function mechFrame(g,hits=[]){return{units:[mechViewUnits(g,0),mechViewUnits(g,1),mechViewUnits(g,null)],effects:[0,1,null].map(side=>hits.filter(h=>{const a=g.units.find(u=>u.id===h.from),b=g.units.find(u=>u.id===h.to);return side===null||(mechVisible(g,side,a)&&mechVisible(g,side,b));}).slice(0,12).map(h=>{const a=g.units.find(u=>u.id===h.from),b=g.units.find(u=>u.id===h.to);return{from:a.id,to:b.id,x:a.x,y:a.y,tx:b.x,ty:b.y,side:a.side,damage:h.damage,flank:h.flank,protected:!!h.guards};})),nexus:[...g.nexus],score:[...g.score],kills:[...g.kills],towers:[...g.towers],sites:structuredClone(g.sites)};}
export function resolveTacticalTurn(g,now){
 const orders=g.teams.map((id,side)=>g.orders[id]||defaultTacticalOrders(g,side)),lines=[],fought=new Set(),damages=new Map(),deathLines=[];
 const add=(kind,text,side=null)=>lines.push({kind,text,side});
 g.frames=[mechFrame(g)];
 for(const [side,p] of orders.entries()){
  if(p.ward)g.wards.push({side,...p.ward,until:g.turn+1});
  for(const o of p.units){const u=g.units.find(u=>u.side===side&&u.role===o.role);if(o.buy){u.gold-=TACTICAL_ITEMS[o.buy].cost;u.items.push(o.buy);}}
 }
 const orderOf=u=>orders[u.side].units.find(o=>o.role===u.role);
 for(let step=0;step<6;step++){
  const next=g.units.map(u=>{if(!mechAlive(u))return{x:u.x,y:u.y};const o=orderOf(u),d=mechDistance(u,o),speed=4.3+mechStat(u,'speed')+(o.stance==='retreat'?.7:0);return d>speed?{x:u.x+(o.x-u.x)*speed/d,y:u.y+(o.y-u.y)*speed/d}:{x:o.x,y:o.y};});
  g.units.forEach((u,i)=>{u.x=mechRound(next[i].x);u.y=mechRound(next[i].y);});
  const hits=[];
  for(const u of g.units.filter(mechAlive)){
   const o=orderOf(u),profile=MECH_ROLE[u.role],range=profile.range+mechStat(u,'range')+(o.stance==='poke'?3:0);
   const targets=g.units.filter(e=>e.side!==u.side&&mechAlive(e)&&mechVisible(g,u.side,e)&&mechDistance(u,e)<=range);
   targets.sort((a,b)=>Number(b.role===o.target)-Number(a.role===o.target)||a.hp-b.hp||mechDistance(u,a)-mechDistance(u,b)||a.role.localeCompare(b.role));
   const target=targets[0];if(!target)continue;fought.add(u.id);fought.add(target.id);
   const guards=g.units.filter(a=>a.side===target.side&&a.id!==target.id&&mechAlive(a)&&orderOf(a).stance==='protect'&&mechDistance(a,target)<=12);
   const allies=g.units.filter(a=>a.side===u.side&&mechAlive(a)&&a.id!==u.id&&mechDistance(a,target)<=17);
   const flank=allies.some(a=>{const ax=a.x-target.x,ay=a.y-target.y,bx=u.x-target.x,by=u.y-target.y;return(ax*bx+ay*by)/Math.max(1,Math.hypot(ax,ay)*Math.hypot(bx,by))<-.25;});
   const focuses=u.items.filter(id=>id==='focus').length,blades=u.items.filter(id=>id==='blade').length,physical=focuses>blades?'magic':blades>0?'physical':profile.type;
   const resist=physical==='magic'?mechStat(target,'resist'):MECH_ROLE[target.role].armor+mechStat(target,'armor');
   const stance=o.stance==='engage'?(step===0?1.3:1.1):o.stance==='farm'?.8:o.stance==='retreat'?.55:1;
   const styleBonus=g.comps[u.side].style==='engage'&&o.stance==='engage'?1.04:g.comps[u.side].style==='control'&&o.stance==='protect'?1.04:g.comps[u.side].style==='pick'&&o.stance==='poke'?1.04:g.comps[u.side].style==='scale'&&o.stance==='farm'?1.04:1;
   const damage=mechRound(Math.max(2,(profile.damage+mechStat(u,'damage')-resist)*stance*(1+u.penalty)*u.skill*styleBonus*(flank?1.15:1)*(guards.length?.75:1)));
   hits.push({from:u.id,to:target.id,damage,flank,guards:guards.length});
  }
  for(const hit of hits){const t=g.units.find(u=>u.id===hit.to);t.hp=mechRound(Math.max(0,t.hp-hit.damage));damages.set(hit.from,(damages.get(hit.from)||0)+hit.damage);}
  for(const u of g.units){if(u.hp===0&&!u.respawn){u.respawn=2;const contributors=hits.filter(h=>h.to===u.id),killer=contributors.sort((a,b)=>b.damage-a.damage||a.from.localeCompare(b.from))[0],a=g.units.find(a=>a.id===killer?.from);if(a){a.kills++;a.gold++;g.kills[a.side]++;g.score[a.side]+=2;const flanked=contributors.some(h=>h.flank),protectedUnit=contributors.some(h=>h.guards);deathLines.push({kind:'fight',side:a.side,text:`${a.champ} elimina ${u.champ}: ${contributors.length} atacante(s) no alcance${flanked?', fogo cruzado +15%':''}${protectedUnit?', proteção aliada −25% de dano recebido':''}. Abate +2 pontos.`});}}}
  for(const u of g.units)if(mechAlive(u)&&mechDistance(u,mechHome(u))<12)u.hp=Math.min(100,mechRound(u.hp+12));
  mechRemember(g);g.frames.push(mechFrame(g,hits));
 }
 lines.push(...deathLines.slice(0,10));
 for(const site of g.sites){if(site.cooldown>g.turn)continue;
  const near=[0,1].map(side=>g.units.filter(u=>u.side===side&&mechAlive(u)&&mechDistance(u,site)<=11));
  if(near[0].length&&near[1].length){add('contest',`${site.name}: objetivo contestado. Nenhum lado captura enquanto houver inimigo vivo no covil.`);continue;}
  const side=near[0].length?0:near[1].length?1:-1;if(side<0)continue;
  if(['top','mid','bot'].includes(site.id)){
   const pressure=near[side].reduce((v,u)=>v+(orderOf(u).stance==='retreat'?0:1),0);site.pressure[side]+=pressure;
   if(site.pressure[side]>=5){site.pressure[side]=0;g.towers[side]++;g.score[side]+=5;g.nexus[1-side]=Math.max(0,g.nexus[1-side]-20);site.cooldown=g.turn+2;add('tower',`${site.name}: ${near[side].length} campeão(ões) convertem pressão em torre. +5 pontos, −20 de Nexus rival.`,side);}
   else add('pressure',`${site.name}: pressão ${site.pressure[side]}/5 para a próxima torre.`,side);
  }else{
   const baron=site.id==='baron'&&g.turn>=7,elder=site.id==='dragon'&&g.turn>=13,need=baron||elder?3:2;
   if(near[side].length<need){add('late',`${baron?'Barão':elder?'Ancião':site.id==='baron'?'Larvas':'Dragão'}: faltaram aliados no alcance. Precisa de ${need} vivos no covil.`);continue;}
   const name=baron?'Barão':elder?'Ancião':site.id==='baron'?'Larvas':'Dragão',points=baron||elder?9:6;
   g.score[side]+=points;site.cooldown=g.turn+3;for(const u of g.units.filter(u=>u.side===side))u.gold+=2;
   if(baron||elder)g.nexus[1-side]=Math.max(0,g.nexus[1-side]-20);
   add('objective',`${name}: ${near[side].length} aliados chegaram e bloquearam a contestação. +${points} pontos, +2 ouro por campeão${baron||elder?', −20 Nexus rival':''}.`,side);
  }
 }
 for(const u of g.units.filter(mechAlive)){
  const farm=orderOf(u).stance==='farm'&&!fought.has(u.id)&&g.sites.some(s=>mechDistance(u,s)<=14)&&mechDistance(u,mechHome(u))>16;
  if(farm)u.gold++;u.hp=Math.min(100,mechRound(u.hp+(fought.has(u.id)?3:8)));
 }
 if(!lines.length)add('rotation','Rotação sem abates. Destinos distantes exigem mais de uma rodada; as sentinelas revelam aproximações.');
 g.report=lines;g.history.push({turn:g.turn,report:lines,score:[...g.score],kills:[...g.kills]});g.history=g.history.slice(-16);
 const ending=g.nexus.some(n=>n===0)||g.turn>=16;
 if(ending){const values=[0,1].map(side=>g.score[side]*1000+g.nexus[side]*5+g.units.filter(u=>u.side===side).reduce((v,u)=>v+u.hp,0)/100);if(g.nexus[0]===0&&g.nexus[1]>0)values[1]=Infinity;else if(g.nexus[1]===0&&g.nexus[0]>0)values[0]=Infinity;if(values[0]===values[1]){g.winner='draw';add('finish','Empate técnico: mesmos pontos, Nexus e vida. Uma rodada de desempate será jogada.');g.winner=null;}else{g.winner=g.teams[values[0]>values[1]?0:1];add('finish','Vitória por '+(g.nexus.some(n=>n===0)?'destruição do Nexus':'pontos; desempate por Nexus restante e depois vida total')+'.');}}
 g.frames.push(mechFrame(g));g.phase='replay';g.replayStarted=now;g.replayEnds=now+6500;g.deadline=g.replayEnds;g.orders={};
}
export function nextTacticalTurn(g,now){g.turn++;g.phase='planning';g.orders={};g.locked={};g.frames=[];g.deadline=now+60000;g.botAt=now+2500;g.wards=g.wards.filter(w=>w.until>=g.turn);for(const u of g.units){if(u.respawn){u.respawn--;if(!u.respawn){Object.assign(u,mechHome(u));u.hp=100;}}}mechRemember(g);}
export function tacticalView(g,viewer,now=Date.now()){
 const side=g.teams.indexOf(viewer),r={turn:g.turn,phase:g.phase,deadline:g.deadline,teams:[...g.teams],comps:g.comps,score:[...g.score],nexus:[...g.nexus],kills:[...g.kills],towers:[...g.towers],sites:structuredClone(g.sites),locked:{...g.locked},report:structuredClone(g.report),history:structuredClone(g.history),winner:g.winner,side};
 r.units=side<0?[]:mechViewUnits(g,side);r.lastSeen=side<0?[]:Object.values(g.lastSeen[side]).filter(u=>!r.units.some(a=>a.id===u.id));r.wards=g.wards.filter(w=>w.side===side);r.myOrders=side<0?null:structuredClone(g.orders[viewer]||null);
 // During replay reveal only frames already reached; no future health or positions.
 if(g.phase==='replay'){
  const index=Math.min(g.frames.length-1,Math.max(0,Math.floor((now-g.replayStarted)/900))),frames=g.frames.slice(0,index+1).map(f=>({...f,units:f.units[side<0?2:side],effects:(f.effects||[[],[],[]])[side<0?2:side]}));
  r.frames=frames;r.units=frames.at(-1)?.units||[];r.score=frames.at(-1)?.score||r.score;r.kills=frames.at(-1)?.kills||r.kills;r.nexus=frames.at(-1)?.nexus||r.nexus;r.report=index>=g.frames.length-1?r.report:[];r.history=index>=g.frames.length-1?r.history:r.history.slice(0,-1);r.sites=frames.at(-1)?.sites||[];r.towers=frames.at(-1)?.towers||[0,0];r.lastSeen=[];r.winner=index>=g.frames.length-1?r.winner:null;
 }
 return r;
}
export function tacticalResult(g){const side=g.teams.indexOf(g.winner),mvp=[...g.units].filter(u=>u.side===side).sort((a,b)=>b.kills-a.kills||b.hp-a.hp)[0];return{mode:'mechanical',winner:g.winner,kills:g.kills,duration:g.turn*2,comps:g.comps,mvp:mvp?.player||'Equipe',score:g.score,nexus:g.nexus,events:g.history.flatMap(h=>h.report.map(e=>({...e,turn:h.turn}))),powers:[0,0],probability:.5};}
