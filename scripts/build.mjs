import fs from 'node:fs';
fs.rmSync('dist',{recursive:true,force:true});fs.mkdirSync('dist/server',{recursive:true});fs.mkdirSync('dist/.openai',{recursive:true});
const WORLDS_DRAFTS=JSON.parse(fs.readFileSync('data/worlds-drafts.json','utf8'));
const CBLOL_DRAFTS=JSON.parse(fs.readFileSync('data/cblol-drafts.json','utf8'));
const data=JSON.parse(fs.readFileSync('data/players.json','utf8'));
const MC_PLAYERS=JSON.parse(fs.readFileSync('data/mc-roster.json','utf8'));
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.jpg':'image/jpeg','.ttf':'font/ttf','.webp':'image/webp','.png':'image/png'};
const assets={};function addFiles(dir,prefix=''){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const full=dir+'/'+entry.name,key=prefix+'/'+entry.name;if(entry.isDirectory()){addFiles(full,key);continue;}const ext='.'+entry.name.split('.').pop();assets[key]={type:types[ext]||'application/octet-stream',base64:fs.readFileSync(full).toString('base64')};}}addFiles('public');
assets['/players.json']={type:types['.json'],base64:Buffer.from(JSON.stringify(data)).toString('base64')};
// app.js imports this JSON as an ES module; missing it prevents the entire UI from starting.
assets['/mc-roster.json']={type:types['.json'],base64:Buffer.from(JSON.stringify(MC_PLAYERS)).toString('base64')};
assets['/champion-stats.json']={type:types['.json'],base64:fs.readFileSync('data/champion-stats.json').toString('base64')};
const strip=s=>s.replace(/^import .+;\r?\n/gm,'').replace(/^export \{.+\};?\r?\n/gm,'').replace(/\bexport (?=(const|function|async|class)\b)/g,'');
const mechanical=strip(fs.readFileSync('worker/mechanical.mjs','utf8'));
const engine=strip(fs.readFileSync('worker/engine.mjs','utf8')),champ=strip(fs.readFileSync('data/champions.mjs','utf8'));const api=strip(fs.readFileSync('worker/api.mjs','utf8'));
const browserEngine=`const PLAYERS=${JSON.stringify(data)};\nconst WORLDS_DRAFTS=${JSON.stringify(WORLDS_DRAFTS)};\nconst CBLOL_DRAFTS=${JSON.stringify(CBLOL_DRAFTS)};\n${champ}\n${mechanical}\n${engine}\nexport {PLAYERS,ROLES,CHAMPIONS,STYLES,createRoom,person,action,tick,publicState,catalog,maxBid,power,compBonus,DEFAULT_CONFIG,marketSize,standings,setConfig,chemistry,TEAM_EMBLEMS,TACTICAL_ITEMS,TACTICAL_STANCES,TACTICAL_SITES};`;
assets['/engine.mjs']={type:types['.mjs'],base64:Buffer.from(browserEngine).toString('base64')};
const mcEngine=strip(fs.readFileSync('worker/mc-engine.mjs','utf8'));
const mcApi=strip(fs.readFileSync('worker/mc-api.mjs','utf8'));
const rpgEngine=strip(fs.readFileSync('worker/rpg-engine.mjs','utf8'));
const rpgApiSrc=strip(fs.readFileSync('worker/rpg-api.mjs','utf8'));

const src=`const MC_PLAYERS=${JSON.stringify(MC_PLAYERS)};
${mcEngine}
${mcApi}
${rpgEngine}
${rpgApiSrc}
const PLAYERS=${JSON.stringify(data)};\nconst WORLDS_DRAFTS=${JSON.stringify(WORLDS_DRAFTS)};\nconst CBLOL_DRAFTS=${JSON.stringify(CBLOL_DRAFTS)};\n${champ}\n${mechanical}\n${engine}\n${api}\nconst ASSETS=${JSON.stringify(assets)};\nexport default {async fetch(request,env,ctx){const url=new URL(request.url);if(url.pathname.startsWith('/api/mc/'))return mcApi(request,env);if(url.pathname.startsWith('/api/rpg/'))return rpgApi(request,env);if(url.pathname.startsWith('/api/'))return api(request,env);if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405});const file=ASSETS[url.pathname==='/'?'/index.html':url.pathname];if(!file)return new Response('Not found',{status:404});const bytes=Uint8Array.from(atob(file.base64),c=>c.charCodeAt(0));return new Response(request.method==='HEAD'?null:bytes,{headers:{'Content-Type':file.type,'Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin','Permissions-Policy':'camera=(), microphone=()','Content-Security-Policy':\"default-src 'self'; img-src 'self' data: https://ddragon.leagueoflegends.com https://pub-6326bb4814464b359a735b2c18ca4125.r2.dev; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'self' https://chatgpt.com\"}});}};`;
fs.writeFileSync('dist/server/index.js',src);if(fs.existsSync('.openai/hosting.json'))fs.copyFileSync('.openai/hosting.json','dist/.openai/hosting.json');fs.cpSync('drizzle','dist/.openai/drizzle',{recursive:true});
fs.writeFileSync('dist/server/wrangler.json',JSON.stringify({name:'rift-draft',main:'index.js',compatibility_date:'2026-01-01',d1_databases:[{binding:'DB',database_name:'rift-draft',database_id:'00000000-0000-0000-0000-000000000000',migrations_dir:'../.openai/drizzle'}]},null,2));
console.log('Worker built:',Buffer.byteLength(src),'bytes');
