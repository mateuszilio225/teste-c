import {DatabaseSync} from 'node:sqlite';
import fs from 'node:fs';
export function database(path=':memory:'){
 const db=new DatabaseSync(path);const version=db.prepare('PRAGMA user_version').get().user_version;
 if(version===0){db.exec(fs.readFileSync(new URL('../drizzle/0000_rooms.sql',import.meta.url),'utf8').replaceAll('--> statement-breakpoint',''));db.exec('PRAGMA user_version = 1');}
 if(version<2){db.exec(fs.readFileSync(new URL('../drizzle/0001_profiles_presets.sql',import.meta.url),'utf8').replaceAll('--> statement-breakpoint',''));db.exec('PRAGMA user_version = 2');}
 if(version<3){db.exec(fs.readFileSync(new URL('../drizzle/0002_rating_default_revision.sql',import.meta.url),'utf8').replaceAll('--> statement-breakpoint',''));db.exec('PRAGMA user_version = 3');}
 return {prepare(sql){return {bind(...params){return {async first(){return db.prepare(sql).get(...params)||null;},async run(){const r=db.prepare(sql).run(...params);return {success:true,meta:{changes:Number(r.changes)}};},async all(){return {results:db.prepare(sql).all(...params)};}};}};},close(){db.close();}};
}
