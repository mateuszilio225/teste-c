import fs from 'node:fs';
fs.mkdirSync('dist',{recursive:true});
for(const path of ['index.html','styles.css','app.js','icon.svg'])fs.copyFileSync(path,'dist/'+path);
for(const path of ['fonts','vendor'])fs.cpSync(path,'dist/'+path,{recursive:true});
console.log('Static app built in dist/.');
