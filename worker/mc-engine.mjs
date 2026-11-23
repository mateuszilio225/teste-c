// Mode-specific, deterministic freestyle auction engine. Does not mutate the LoL game state.
import MC_PLAYERS from '../data/mc-roster.json' with {type:'json'};
export const MC_BY_ID = new Map(MC_PLAYERS.map(p=>[p.id,p]));

const mcSumTeam=(team)=>team.roster.reduce((a,id)=>a+(MC_BY_ID.get(id)?.overall||0),0);

const mcLog=(s,msg)=>{s.mcLog.push(msg);if(s.mcLog.length>50)s.mcLog.shift();};
const mcSeeded=(s)=>{s.seed=(Math.imul(s.seed,1664525)+1013904223)>>>0;return s.seed/2**32;};
const mcShuffle=(s,a)=>{let b=[...a];for(let i=b.length-1;i>0;i--){const j=Math.floor(mcSeeded(s)*(i+1));[b[i],b[j]]=[b[j],b[i]];}return b;};
export function mcCreate(code,id,name,capacity=2,seed=1234){return {kind:'mc-battle',v:1,code,host:id,seed:seed>>>0,capacity,phase:'lobby',members:[{id,name,bot:false,balance:50,roster:[]}],auction:null,market:[],sold:[],match:null,queue:[],round:0,champion:null,mcLog:[],created:Date.now()};}
export function mcPublic(s,id){return {...s,myId:id,seed:undefined};}
function mcAssignBots(s){while(s.members.length<s.capacity){let i=s.members.length+1;s.members.push({id:'bot-'+i,name:'Bot '+i,bot:true,balance:50,roster:[]});}}
function mcStartAuction(s,now){s.phase='auction';s.market=mcShuffle(s,MC_PLAYERS.map(x=>x.id));s.auction=null;mcNextLot(s,now);mcLog(s,'Leilão aberto — cada equipe monta um trio de cinco MCs.');}
function mcNextLot(s,now){const target=s.capacity*5;const full=s.members.every(m=>m.roster.length>=5);if(full||s.market.length===0){mcSettleLot(s);mcFinishAuction(s,now);return;}
 const next=s.market.shift();s.auction={mc:next,bid:0,leader:null,ends:now+16000,lastBids:[]};}
function mcSettleLot(s){const lot=s.auction;if(!lot?.leader)return;const winner=s.members.find(x=>x.id===lot.leader);const p=MC_BY_ID.get(lot.mc);if(winner&&winner.balance>=lot.bid&&winner.roster.length<5){winner.balance-=lot.bid;winner.roster.push(lot.mc);s.sold.push({mc:lot.mc,team:winner.id,price:lot.bid});mcLog(s,`${p.name} vendido para ${winner.name} por ${lot.bid}.`);}}
function mcAutoComplete(s){const used=new Set(s.members.flatMap(m=>m.roster));let leftovers=MC_PLAYERS.filter(p=>!used.has(p.id)).sort((a,b)=>b.overall-a.overall);for(const m of s.members){while(m.roster.length<5){let p=leftovers.shift();if(!p)break;m.roster.push(p.id);used.add(p.id);} }}
function mcFinishAuction(s,now){mcAutoComplete(s);s.phase='battles';s.auction=null;const ordering=mcShuffle(s,s.members.map(x=>x.id));s.queue=[];for(let i=0;i<ordering.length;i+=2)s.queue.push({a:ordering[i],b:ordering[i+1]});s.round=1;mcNextMatch(s,now);mcLog(s,'Leilão encerrado. Começam os confrontos de MCs.');}
function mcNextMatch(s,now){if(!s.queue.length){s.phase='finished';return;}
 const {a,b}=s.queue.shift();s.match={a,b,duels:[],usedA:[],usedB:[],scoreA:0,scoreB:0,turn:s.round%2?a:b,startedAt:now};}
function mcBotPick(s,now){const m=s.match;if(!m||s.phase!=='battles')return false;const picker=s.members.find(x=>x.id===m.turn);if(!picker?.bot)return false;const ownA=m.turn===m.a,ownIds=picker.roster.filter(x=>!(ownA?m.usedA:m.usedB).includes(x));const rival=s.members.find(x=>x.id===(ownA?m.b:m.a));const remaining=rival.roster.filter(x=>!(ownA?m.usedB:m.usedA).includes(x));if(!ownIds.length||!remaining.length)return false;
 // Defensivo: usa o menor MC que vence algum rival, ou sacrifica o menor contra o maior.
 const ours=ownIds.map(id=>MC_BY_ID.get(id)).sort((a,b)=>a.overall-b.overall);const foes=remaining.map(id=>MC_BY_ID.get(id)).sort((a,b)=>a.overall-b.overall);
 let chosen=null;for(const mine of ours){const target=foes.find(x=>x.overall<mine.overall);if(target){chosen={mine:mine.id,enemy:target.id};break;}}
 chosen ||= {mine:ours[0].id,enemy:foes[foes.length-1].id};mcAction(s,picker.id,{type:'duel',own:chosen.mine,enemy:chosen.enemy},now);return true;}
function mcResolveMatch(s,now){const m=s.match,ta=s.members.find(x=>x.id===m.a),tb=s.members.find(x=>x.id===m.b);const aTotal=mcSumTeam(ta),bTotal=mcSumTeam(tb);const winner=m.scoreA===m.scoreB?(aTotal>=bTotal?m.a:m.b):(m.scoreA>m.scoreB?m.a:m.b);mcLog(s,`${ta.name} ${m.scoreA} × ${m.scoreB} ${tb.name} — ${s.members.find(x=>x.id===winner).name} avançou.`);s.winners??=[];s.winners.push(winner);s.match=null;
 if(s.queue.length){mcNextMatch(s,now);return;}
 if(s.winners.length===1){s.champion=s.winners[0];s.phase='finished';mcLog(s,`CAMPEÃO: ${s.members.find(x=>x.id===s.champion).name}`);return;}
 let w=[...s.winners];s.winners=[];s.round++;s.queue=[];for(let i=0;i<w.length;i+=2)s.queue.push({a:w[i],b:w[i+1]});mcNextMatch(s,now);}
export function mcTick(s,now=Date.now()){if(s.phase==='auction'&&s.auction){const lot=s.auction;if(now>=lot.ends){mcSettleLot(s);mcNextLot(s,now);}}if(s.phase==='battles'&&s.match){let i=0;while(s.match&&i++<10&&mcBotPick(s,now));}}
export function mcAction(s,id,a,now=Date.now()){const team=s.members.find(m=>m.id===id);if(!team)throw Error('Equipe inválida.');
 if(a.type==='start'){if(s.phase!=='lobby'||s.host!==id)throw Error('Apenas o criador inicia o torneio.');mcAssignBots(s);mcStartAuction(s,now);return;}
 if(a.type==='endAuction'){if(s.phase!=='auction'||s.host!==id)throw Error('Somente o criador pode encerrar o leilão.');mcFinishAuction(s,now);return;}
 if(a.type==='skip'){if(s.phase!=='auction'||s.host!==id)throw Error('Somente o criador pode passar o lote.');mcSettleLot(s);mcNextLot(s,now);return;}
 if(a.type==='bid'){if(s.phase!=='auction'||!s.auction)throw Error('Leilão indisponível.');const lot=s.auction;if(now>=lot.ends)throw Error('Lote finalizado.');if(String(a.mc||'')!==lot.mc)throw Error('A carta mudou. Atualize o lance.');if(team.roster.length>=5)throw Error('Seu elenco está completo.');if(lot.leader===id)throw Error('Seu lance já está na liderança.');const inc=a.allin?team.balance:Number(a.inc);if(!a.allin&&![1,5,10].includes(inc))throw Error('Incremento inválido.');const next=a.allin?team.balance:lot.bid+inc;if(next<=lot.bid||next>team.balance)throw Error('Saldo insuficiente.');lot.bid=next;lot.leader=id;lot.ends=now+5000;lot.lastBids.unshift({team:team.name,amount:next});lot.lastBids=lot.lastBids.slice(0,5);return;}
 if(a.type==='duel'){if(s.phase!=='battles'||!s.match)throw Error('Não há confronto aberto.');const m=s.match;if(m.turn!==id)throw Error('Agora é a vez do adversário escolher.');const asA=id===m.a,own=String(a.own||''),enemy=String(a.enemy||''),opponent=s.members.find(x=>x.id===(asA?m.b:m.a));if(!team.roster.includes(own)||!opponent.roster.includes(enemy))throw Error('Escolha um MC de cada elenco.');if((asA?m.usedA:m.usedB).includes(own)||(asA?m.usedB:m.usedA).includes(enemy))throw Error('Um MC não pode batalhar duas vezes no mesmo confronto.');const left=MC_BY_ID.get(own),right=MC_BY_ID.get(enemy);const duelWinner=left.overall===right.overall?'empate':left.overall>right.overall?id:opponent.id;
 const mcA=asA?left:right,mcB=asA?right:left;m.duels.push({mcA:mcA.id,mcB:mcB.id,ovrA:mcA.overall,ovrB:mcB.overall,winner:duelWinner});m.usedA.push(mcA.id);m.usedB.push(mcB.id);if(duelWinner===m.a)m.scoreA++;if(duelWinner===m.b)m.scoreB++;
 if(m.duels.length===5){mcResolveMatch(s,now);}else{m.turn=id===m.a?m.b:m.a;}return;}
 throw Error('Ação desconhecida.');}
