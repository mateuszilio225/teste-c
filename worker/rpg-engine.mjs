// Rift Chronicles: original rules-light mystery RPG for a human game master.
// No official Ordem Paranormal content, assets, monsters or rulebook text.
export const RPG_CLASSES = [
  {id:'guardiao',name:'Guardião',icon:'🛡️',description:'Resiste ao perigo e protege o grupo.',stats:{corpo:3,mente:1,instinto:2,presenca:1},talent:'Uma vez por cena, absorve 2 de dano de um aliado.'},
  {id:'investigador',name:'Investigador',icon:'🔎',description:'Lê pistas e conecta acontecimentos.',stats:{corpo:1,mente:3,instinto:2,presenca:1},talent:'Uma vez por cena, pode pedir ao mestre uma pista extra.'},
  {id:'sensitivo',name:'Sensitivo',icon:'🔮',description:'Percebe fenômenos ocultos e ecos do Véu.',stats:{corpo:1,mente:2,instinto:2,presenca:3},talent:'Uma vez por cena, sente a presença de forças anômalas.'},
  {id:'socorrista',name:'Socorrista',icon:'🩺',description:'Cuida da equipe sob pressão.',stats:{corpo:2,mente:2,instinto:1,presenca:3},talent:'Uma vez por cena, recupera até 3 pontos de Vida de um aliado.'},
  {id:'infiltrador',name:'Infiltrador',icon:'🗝️',description:'Encontra entradas, atalhos e rotas de fuga.',stats:{corpo:2,mente:1,instinto:3,presenca:2},talent:'Uma vez por cena, obtém vantagem narrativa em furtividade.'}
];
export const RPG_ORIGINS = ['Jornalista','Ex-policial','Estudante','Médico','Artista','Pesquisador','Sobrevivente','Detetive'];
export const RPG_PRESETS = [
 {id:'brumaria',name:'O Véu de Brumária',genre:'Mistério sobrenatural',description:'Uma cidade costeira esquece pessoas durante a madrugada. As pistas levam a um farol apagado há 80 anos.',goal:'Descobrir o que rouba as memórias dos moradores.'},
 {id:'estacao',name:'Última Parada',genre:'Suspense urbano',description:'Uma estação de metrô abandonada emite sinais de rádio que ninguém deveria compreender.',goal:'Encontrar a origem do sinal antes da próxima lua nova.'},
 {id:'coroa',name:'A Coroa das Cinzas',genre:'Fantasia sombria',description:'Uma vila nas montanhas recebe cartas assinadas por um rei que desapareceu há séculos.',goal:'Quebrar o pacto que mantém o vale isolado.'}
];
export const RPG_REGIONS = [
 {id:'praca',name:'Praça dos Relógios',x:21,y:55,type:'cidade',chapter:1,description:'Os sinos tocam à meia-noite, mas cada morador ouve uma hora diferente.',secret:'O relógio parado marca a hora do desaparecimento do primeiro vigia.',npc:'Dona Celina, relojoeira',clue:'Um bilhete com a inscrição: não confie nas horas.',choices:['Conversar com a relojoeira','Examinar o mecanismo','Seguir a patrulha']},
 {id:'arquivo',name:'Arquivo Municipal',x:33,y:42,type:'cidade',chapter:1,description:'Documentos lacrados descrevem bairros que não existem mais.',secret:'A planta mais antiga da cidade mostra uma porta sob o lago.',npc:'Ivo, arquivista',clue:'Mapa de 1926 com uma passagem submersa.',choices:['Pesquisar desaparecidos','Convencer o arquivista','Copiar a planta']},
 {id:'mercado',name:'Mercado da Névoa',x:37,y:70,type:'cidade',chapter:1,description:'Barracas desertas deixam frutas frescas e rádios ligados.',secret:'Um vendedor misterioso guarda uma chave do farol.',npc:'Nara, comerciante',clue:'Recibo emitido por uma loja fechada há trinta anos.',choices:['Vasculhar barracas','Perseguir uma silhueta','Interrogar Nara']},
 {id:'ponte',name:'Ponte Quebrada',x:45,y:56,type:'estrada',chapter:1,description:'Atravessar a ponte parece levar sempre ao mesmo ponto.',secret:'É possível cruzar usando o reflexo da lua no rio.',npc:'O Passageiro',clue:'Marcas de botas apontam nos dois sentidos ao mesmo tempo.',choices:['Testar a travessia','Investigar a água','Procurar um atalho']},
 {id:'floresta',name:'Mata das Vozes',x:56,y:38,type:'floresta',chapter:2,description:'As árvores repetem conversas de viajantes que nunca passaram por ali.',secret:'As vozes cessam quando alguém pronuncia o nome do vigia.',npc:'Lena, guarda-florestal',clue:'Um gravador reproduz a voz de um personagem do grupo.',choices:['Seguir a voz','Marcar o caminho','Montar acampamento']},
 {id:'cemiterio',name:'Cemitério de Sal',x:60,y:65,type:'ruina',chapter:2,description:'Há lápides com nomes de pessoas que ainda estão vivas.',secret:'Uma lápide vazia aponta para o porão da capela.',npc:'O Zelador',clue:'Fotografia de um funeral que ainda não aconteceu.',choices:['Comparar nomes','Abrir o mausoléu','Questionar o zelador']},
 {id:'capela',name:'Capela Afundada',x:70,y:53,type:'ruina',chapter:2,description:'Velas acesas iluminam um santuário parcialmente submerso.',secret:'O sino da capela mantém a passagem para o farol fechada.',npc:'Irmandade dos Ecos',clue:'Partitura com notas que fazem a água recuar.',choices:['Descifrar a partitura','Enfrentar a irmandade','Descer às catacumbas']},
 {id:'hospital',name:'Hospital Velho',x:22,y:26,type:'ruina',chapter:2,description:'Prontuários novos surgem em salas abandonadas há décadas.',secret:'O laboratório registrou o primeiro contato com o Véu.',npc:'Dr. Amaral',clue:'Uma fita com os últimos minutos de uma pesquisa proibida.',choices:['Ler prontuários','Encontrar medicamentos','Seguir os sons do elevador']},
 {id:'observatorio',name:'Observatório do Norte',x:42,y:20,type:'torre',chapter:2,description:'Um telescópio apontado para o mar mostra uma costa impossível.',secret:'O céu visível pelo telescópio é de outra época.',npc:'Aurora, astrônoma',clue:'Almanaque com uma constelação ausente do céu atual.',choices:['Ajustar o telescópio','Estudar o almanaque','Confrontar Aurora']},
 {id:'porto',name:'Porto das Sombras',x:76,y:72,type:'porto',chapter:3,description:'Barcos atracados carregam caixas vazias seladas com cera preta.',secret:'Uma embarcação retorna sempre sem sua tripulação.',npc:'Capitão Vicente',clue:'Diário náutico que termina amanhã.',choices:['Inspecionar o barco','Negociar passagem','Seguir as pegadas']},
 {id:'farol',name:'Farol Sem Luz',x:84,y:31,type:'torre',chapter:3,description:'Uma lente enorme gira sem emitir luz. Algo observa do outro lado do vidro.',secret:'A lente funciona como uma prisão para uma consciência antiga.',npc:'Vigia Sem Rosto',clue:'O diário do vigia descreve como selar a lente.',choices:['Subir a torre','Desativar o mecanismo','Dialogar com o vigia']},
 {id:'abismo',name:'Fenda do Véu',x:91,y:52,type:'anomalia',chapter:3,description:'O ar parece dobrado. Cada escolha traz de volta uma lembrança diferente.',secret:'O Véu pode ser fechado, destruído ou reescrito, com consequências distintas.',npc:'O Eco Primordial',clue:'Três runas marcam três possíveis desfechos.',choices:['Tentar selar a fenda','Romper o pacto','Aceitar negociar']}];
const rpgClamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const rpgSanitize=(x,max=180)=>String(x??'').replace(/[<>\x00-\x1f]/g,'').trim().slice(0,max);
const rpgRegion=id=>RPG_REGIONS.find(r=>r.id===id);
const rpgPlayer=(s,id)=>s.players.find(p=>p.id===id);
const rpgGmOnly=(s,id)=>{if(id!==s.gm.id)throw Error('Apenas o mestre pode fazer isso.');};
const rpgLog=(s,kind,text,extra={})=>{s.log.push({id:++s.seq,at:Date.now(),kind,text:rpgSanitize(text,420),...extra});if(s.log.length>110)s.log.shift();};
export function rpgCreate(code,gmId,gmName,opts={}){
 const preset=RPG_PRESETS.find(x=>x.id===opts.preset)||RPG_PRESETS[0];const title=rpgSanitize(opts.title,52)||preset.name;
 return {kind:'rift-rpg',version:1,code,gm:{id:gmId,name:rpgSanitize(gmName,26)},capacity:[2,3,4,5,6].includes(opts.capacity)?opts.capacity:4,phase:'lobby',created:Date.now(),seq:0,players:[],campaign:{preset:preset.id,title,genre:preset.genre,goal:preset.goal,difficulty:['leve','normal','tenso'].includes(opts.difficulty)?opts.difficulty:'normal',chapter:1},scene:{region:'praca',description:RPG_REGIONS[0].description,at:Date.now()},revealed:['praca'],clues:[],objective:'Explorar a Praça dos Relógios e encontrar a primeira pista.',npcs:[],rollRequest:null,initiative:[],log:[],gmNotes:'',session:1};
}
export function rpgPublic(s,id){const isGm=s.gm.id===id;return {...s,viewRole:isGm?'mestre':'jogador',players:s.players.map(p=>({...p,token:undefined})),gmNotes:isGm?s.gmNotes:undefined,regions:RPG_REGIONS.map(r=>(isGm||s.revealed.includes(r.id)?{...r,secret:isGm?r.secret:undefined,clue:isGm?r.clue:undefined,choices:isGm?r.choices:undefined}:{id:r.id,x:r.x,y:r.y,type:'oculto',name:'???'})),log:s.log.slice(-85),rollRequest:s.rollRequest&&(!isGm&&s.rollRequest.playerId!==id?{id:s.rollRequest.id,pending:true}:s.rollRequest)};}
export function rpgAction(s,id,a,rand=()=>Math.floor(Math.random()*20)+1){
 if(!a||typeof a.type!=='string')throw Error('Ação inválida.');
 const me=rpgPlayer(s,id),isGm=s.gm.id===id;
 if(!isGm&&!me)throw Error('Você não pertence a esta sala.');
 switch(a.type){
  case 'character':{
   if(!me||s.phase==='finished')throw Error('Entre como jogador para criar a ficha.');
   const cls=RPG_CLASSES.find(c=>c.id===a.classId),origin=RPG_ORIGINS.find(o=>o===a.origin),name=rpgSanitize(a.name,26);
   if(!cls||!origin||name.length<2)throw Error('Escolha nome, classe e origem.');
   const prev=me.character,health=12+cls.stats.corpo*2,focus=8+cls.stats.mente;
   if(s.phase!=='lobby'&&prev)throw Error('Ficha fechada depois do início da campanha.');
   me.character={name,classId:cls.id,origin,level:1,stats:{...cls.stats},hp:health,maxHp:health,focus,maxFocus:focus,tension:0,inventory:['Lanterna','Caderno de anotações','Rádio portátil'],status:'Pronto'};
   rpgLog(s,'system',`${me.name} criou ${name} (${cls.name}).`);break;
  }
  case 'start':{rpgGmOnly(s,id);if(s.phase!=='lobby')throw Error('Campanha já iniciada.');if(s.players.length<1||s.players.some(p=>!p.character))throw Error('Os jogadores precisam criar suas fichas.');s.phase='playing';rpgLog(s,'scene',`Sessão ${s.session} iniciada — ${s.campaign.title}.`);rpgLog(s,'scene',s.scene.description);break;}
  case 'scene':{rpgGmOnly(s,id);if(s.phase!=='playing')throw Error('Inicie a campanha primeiro.');const r=rpgRegion(a.region);if(!r)throw Error('Região inválida.');s.scene={region:r.id,description:rpgSanitize(a.description,420)||r.description,at:Date.now()};if(!s.revealed.includes(r.id))s.revealed.push(r.id);rpgLog(s,'scene',`${r.name} — ${s.scene.description}`);break;}
  case 'narrate':{rpgGmOnly(s,id);let t=rpgSanitize(a.text,420);if(t.length<3)throw Error('Digite um acontecimento.');s.scene.description=t;rpgLog(s,'narration',t);break;}
  case 'action':{if(!me||!me.character||s.phase!=='playing')throw Error('Sua ficha não está pronta.');const text=rpgSanitize(a.text,320);if(text.length<2)throw Error('Descreva sua ação.');rpgLog(s,'action',`${me.character.name}: ${text}`,{actor:id});break;}
  case 'reveal':{rpgGmOnly(s,id);const r=rpgRegion(a.region);if(!r)throw Error('Região inválida.');const show=!!a.visible;s.revealed=show?[...new Set([...s.revealed,r.id])]:s.revealed.filter(x=>x!==r.id);rpgLog(s,'system',`${r.name}: ${show?'área revelada':'área ocultada'} pelo mestre.`);break;}
  case 'clue':{rpgGmOnly(s,id);const t=rpgSanitize(a.text,240),r=rpgRegion(a.region||s.scene.region);if(t.length<3)throw Error('Informe a pista.');s.clues.push({id:++s.seq,region:r?.id||null,text:t,at:Date.now()});s.clues=s.clues.slice(-45);rpgLog(s,'clue',`Pista descoberta: ${t}`);break;}
  case 'objective':{rpgGmOnly(s,id);const t=rpgSanitize(a.text,200);if(!t)throw Error('Informe o objetivo.');s.objective=t;rpgLog(s,'system',`Novo objetivo: ${t}`);break;}
  case 'chapter':{rpgGmOnly(s,id);let n=Number(a.number);if(!Number.isInteger(n)||n<1||n>3)throw Error('Capítulo inválido.');s.campaign.chapter=n;rpgLog(s,'scene',`Capítulo ${n} iniciado.`);break;}
  case 'notes':{rpgGmOnly(s,id);s.gmNotes=rpgSanitize(a.text,2000);break;}
  case 'requestRoll':{
   rpgGmOnly(s,id);const member=rpgPlayer(s,a.playerId),attribute=['corpo','mente','instinto','presenca'].includes(a.attribute)?a.attribute:null,dc=Number(a.dc);
   if(!member?.character||!attribute||!Number.isInteger(dc)||dc<5||dc>25)throw Error('Selecione personagem, atributo e dificuldade.');
   s.rollRequest={id:++s.seq,playerId:member.id,attribute,dc,label:rpgSanitize(a.label,80)||'Teste de habilidade'};
   rpgLog(s,'system',`${member.character.name} recebeu um teste de ${attribute.toUpperCase()} (DT ${dc}).`);break;
  }
  case 'roll':{
   if(!me?.character||!s.rollRequest||s.rollRequest.playerId!==id)throw Error('Não há teste pendente para você.');
   const r=s.rollRequest,dice=rpgClamp(Math.floor(rand()),1,20),bonus=me.character.stats[r.attribute]||0,total=dice+bonus,passed=total>=r.dc;
   rpgLog(s,'roll',`${me.character.name}: 🎲 ${dice} + ${bonus} = ${total} contra DT ${r.dc} — ${passed?'SUCESSO':'FALHA'} (${r.label}).`,{dice,total,passed});s.rollRequest=null;break;
  }
  case 'freeRoll':{
   if(!me?.character||s.phase!=='playing')throw Error('Inicie a campanha e crie seu personagem.');const attribute=['corpo','mente','instinto','presenca'].includes(a.attribute)?a.attribute:'mente';const dice=rpgClamp(Math.floor(rand()),1,20),bonus=me.character.stats[attribute];
   rpgLog(s,'roll',`${me.character.name}: 🎲 ${dice} + ${bonus} = ${dice+bonus} (${attribute.toUpperCase()}, teste livre).`,{dice,total:dice+bonus});break;
  }
  case 'resource':{rpgGmOnly(s,id);const target=rpgPlayer(s,a.playerId)?.character,key=['hp','focus','tension'].includes(a.key)?a.key:null,delta=Number(a.delta);if(!target||!key||!Number.isInteger(delta)||Math.abs(delta)>12)throw Error('Ajuste inválido.');target[key]=rpgClamp(target[key]+delta,0,key==='hp'?target.maxHp:key==='focus'?target.maxFocus:10);rpgLog(s,'system',`${target.name}: ${key==='hp'?'Vida':key==='focus'?'Foco':'Tensão'} ${delta>0?'+':''}${delta}.`);break;}
  case 'item':{rpgGmOnly(s,id);const char=rpgPlayer(s,a.playerId)?.character,item=rpgSanitize(a.item,60);if(!char||!item||char.inventory.length>=18)throw Error('Item inválido ou inventário cheio.');char.inventory.push(item);rpgLog(s,'item',`${char.name} recebeu ${item}.`);break;}
  case 'npc':{rpgGmOnly(s,id);let name=rpgSanitize(a.name,40),hp=Number(a.hp);if(!name||!Number.isInteger(hp)||hp<1||hp>70||s.npcs.length>=12)throw Error('NPC inválido.');s.npcs.push({id:++s.seq,name,hp,maxHp:hp});rpgLog(s,'scene',`Uma nova presença surgiu: ${name}.`);break;}
  case 'npcHp':{rpgGmOnly(s,id);let npc=s.npcs.find(x=>x.id===Number(a.id)),delta=Number(a.delta);if(!npc||!Number.isInteger(delta)||Math.abs(delta)>20)throw Error('Ajuste inválido.');npc.hp=rpgClamp(npc.hp+delta,0,npc.maxHp);rpgLog(s,'system',`${npc.name}: ${delta>0?'+':''}${delta} de Vida.`);break;}
  case 'initiative':{rpgGmOnly(s,id);const ranks=s.players.filter(p=>p.character).map(p=>({id:p.id,name:p.character.name,roll:rpgClamp(Math.floor(rand()),1,20)+p.character.stats.instinto})).sort((a,b)=>b.roll-a.roll);s.initiative=ranks;rpgLog(s,'system','Iniciativa: '+ranks.map(x=>`${x.name} ${x.roll}`).join(' · '));break;}
  case 'newSession':{rpgGmOnly(s,id);s.session++;s.initiative=[];rpgLog(s,'scene',`Sessão ${s.session} iniciada. O progresso anterior foi mantido.`);break;}
  default:throw Error('Ação desconhecida.');
 }
}
