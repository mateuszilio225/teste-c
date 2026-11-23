import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import worker from '../dist/server/index.js';

test('V5 card uses the supplied image, compact hero, real local CBLOL crests and accessible picker', async()=>{
 const app=fs.readFileSync('public/app.js','utf8');
 const css=fs.readFileSync('public/styles.css','utf8');
 assert.match(app,/dynquedo-original-card/);
 assert.match(app,/dynquedo-special\.webp/);
 assert.match(css,/\.hero\.hero-v4\{height:510px/);
 assert.match(app,/team-logo-backdrop/);
 assert.match(app,/crestPicker\(selectedLogo/);
 assert.match(app,/data-club-logo/);
 for(const path of ['/dynquedo-special.webp','/clubs/FUR.webp','/clubs/PNG.webp','/clubs/LOS.webp','/clubs/RED.webp']){
  const result=await worker.fetch(new Request('https://example.test'+path),{},{});
  assert.equal(result.status,200,path);
  assert.match(result.headers.get('content-type')||'',/image\/webp/,path);
  assert.ok((await result.arrayBuffer()).byteLength>1000);
 }
});
test('V5 elo is opened without waiting for network, and badges are enlarged',()=>{
 const js=fs.readFileSync('public/app.js','utf8');
 const css=fs.readFileSync('public/styles.css','utf8');
 assert.match(js,/case'profile':profilePanel\(\);void fetchProfile\(\);break/);
 assert.match(js,/eloNav\.dataset\.action='profile'/);
 assert.match(css,/\.rank-identity>\.rank-badge-image\{width:110px/);
});
