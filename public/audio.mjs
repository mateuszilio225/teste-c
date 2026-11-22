// Efeitos sintetizados com WebAudio; não há trilha de fundo nem arquivos externos.
let context=null,room=null,clock=()=>Date.now(),alerts=true,lastCountdown='';
try{alerts=JSON.parse(localStorage.getItem('rift-alerts')??'true');}catch{}
export const audioState=()=>({alerts});
function tone(freq,when,duration,volume=.036,type='sine'){
 if(!context||context.state!=='running')return;
 const oscillator=context.createOscillator(),gain=context.createGain();
 oscillator.type=type;oscillator.frequency.setValueAtTime(freq,when);
 gain.gain.setValueAtTime(.0001,when);
 gain.gain.exponentialRampToValueAtTime(Math.max(.001,volume),when+.012);
 gain.gain.exponentialRampToValueAtTime(.0001,when+duration);
 oscillator.connect(gain);gain.connect(context.destination);
 oscillator.start(when);oscillator.stop(when+duration+.02);
}
export async function unlockAudio(){if(!alerts)return;try{context??=new (window.AudioContext||window.webkitAudioContext)();if(context.state==='suspended')await context.resume();}catch{}}
export function setAudio(kind,value){if(kind!=='alerts')return;alerts=Boolean(value);try{localStorage.setItem('rift-alerts',JSON.stringify(alerts));}catch{}if(alerts)unlockAudio();}
export function updateAudio(state,getNow){room=state;clock=getNow;}
export function effect(name){if(!alerts||!context||context.state!=='running')return;const t=context.currentTime;
 switch(name){
 case 'bid':tone(510,t,.12,.055,'triangle');tone(760,t+.095,.15,.044,'sine');break;
 case 'rivalBid':tone(440,t,.1,.025,'triangle');tone(580,t+.11,.14,.04,'triangle');break;
 case 'outbid':tone(740,t,.15,.08,'sawtooth');tone(440,t+.14,.24,.07,'triangle');break;
 case 'choose':[261.63,329.63,392,523.25].forEach((f,i)=>tone(f,t+i*.065,.28,.035,'triangle'));break;
 case 'sold':[392,523.25,659.25].forEach((f,i)=>tone(f,t+i*.085,.27,.038,'sine'));break;
 case 'champion':[392,523.25,659.25,783.99,1046.5].forEach((f,i)=>tone(f,t+i*.12,.36,.055,'triangle'));break;
 case 'loss':tone(392,t,.20,.028,'triangle');tone(293.66,t+.16,.34,.03,'sine');break;
 case 'objective':tone(146.83,t,.47,.045,'triangle');tone(293.66,t+.05,.35,.032);break;
 case 'countdown':tone(880,t,.075,.025,'sine');break;
 }
}
setInterval(()=>{if(!context||context.state!=='running'||!room||document.hidden||room.phase!=='auction')return;
 const a=room.auction;if(!a)return;const rem=(a.ends-clock())/1000;
 if(rem<=2.8&&rem>0){const seconds=Math.ceil(rem),key=`${room.code}:${a.index}:${a.ends}:${seconds}`;if(seconds<=2&&key!==lastCountdown){lastCountdown=key;effect('countdown');}}
},110);
