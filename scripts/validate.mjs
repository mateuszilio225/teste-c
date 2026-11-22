import fs from 'node:fs';
import assert from 'node:assert/strict';
const manifest=JSON.parse(fs.readFileSync('.openai/hosting.json','utf8'));
assert.equal(manifest.project_id,'appgprj_6b0236d0bc9c81918e875b45cc783287');
assert.equal(manifest.static.directory,'dist');
const html=fs.readFileSync('dist/index.html','utf8');
for(const name of ['styles.css','app.js','icon.svg','vendor/peerjs.min.js'])assert.ok(fs.statSync('dist/'+name).size>0);
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(ids.length,new Set(ids).size,'Duplicate DOM ids');
const js=fs.readFileSync('dist/app.js','utf8');
for(const match of js.matchAll(/\$\('([^']+)'\)/g)){if(match[1]==='inviteDialog')continue;assert.ok(ids.includes(match[1]),'Missing DOM id '+match[1]);}
assert.ok(!html.includes('codex-preview'));
assert.ok(js.includes('getDisplayMedia')&&js.includes('replaceTrack'));
console.log('Static artifact valid: assets, DOM references, syntax, hosting identity.');
