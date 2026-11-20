from pathlib import Path
import json,shutil,math,csv
R=Path(__file__).parent;OLD=R.parent/'lol-partida';p0=json.loads((OLD/'project.json').read_text());A=R/'assets';(A/'avatars').mkdir(parents=True,exist_ok=True)
for f in ['Bard-icon.png','Viego-passive.png']:
 shutil.copy2(OLD/'assets'/f,A/f)
for name in ['overlays','rune-card']:
 shutil.copytree(OLD/'assets'/name,A/name,dirs_exist_ok=True)
shutil.copy2('/workspace/generated_images/exec-9d2a22de-3a01-4e39-8526-44f2fd1f2122.png',R/'anime-original.png')
for name in ['source-original.mp4','native-audio.m4a']:
 dst=R/name
 if not dst.exists():dst.symlink_to(OLD/name)
P=dict(title='Viego — gameplay completa do draft ao fim',version=2,status='rendering chronological gameplay',source='source-original.mp4',fps=60,width=1280,height=720,source_duration=2150.005,segments=[],cues=[],avatar_note='One decorative anime avatar for every caption. No speaker identities, portraits or names.',chronology='All source time covered exactly once in increasing order. No future hook, repeats or disconnected highlight selection.',source_end_note='Original recording ends after exit/reconnect; victory/defeat not captured.')
for q in p0['cues']:
 q=dict(q);q['who']='anime';P['cues'].append(q)
# All pictures and actions remain chronological, including the setup between fights.
# Three brief jungle passages are accelerated; none of their video intervals is omitted.
boosts=[(505,518),(568,594),(1584,1606)]
points=sorted(set([0,403,2150]+list(range(60,2150,60))+[t for ab in boosts for t in ab]))
effects=[e for s in p0['segments'] if s['kind']=='source' and s['label']!='hook' for e in s.get('effects',[])]
zoom=[w for s in p0['segments'] if s['kind']=='source' and s['label']!='hook' for w in s.get('zoom_windows',[])]
start=0;source_count=0
for a,b in zip(points,points[1:]):
 speed=2 if any(x<=a and b<=y for x,y in boosts) else 1
 frames=round((b-a)/speed*60);dur=frames/60
 s=dict(id=f'{len(P["segments"]):02d}-source-{a:04d}',label=f'source_{a}',kind='source',a=a,b=b,speed=speed,layout='full',frames=frames,duration=dur,start=round(start,6),reason='Continuous chronological gameplay',mute_source=(1584<=a<1606),effects=[e for e in effects if e['a']<b and e['b']>a],zoom_windows=[w for w in zoom if w[0]>=a and w[1]<=b]);P['segments'].append(s);start+=dur;source_count+=b-a
 if b==403:
  P['segments'].append(dict(id=f'{len(P["segments"]):02d}-runes',label='runes',kind='card',a=0,b=5.4,speed=1,layout='card',frames=324,duration=5.4,start=round(start,6),media='assets/rune-card/runes-animated.mp4',audio='assets/rune-card/stinger.wav',mute_source=False,effects=[],reason='Runes before gameplay; source resumes at the same point'))
  start+=5.4
P['duration']=round(start,6);P['source_coverage_seconds']=source_count
assert source_count==2150 and abs(start-2124.9)<.01
(R/'project.json').write_text(json.dumps(P,ensure_ascii=False,indent=2))
with (R/'cut-list.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['segment','source_start','source_end','speed','output_start','output_duration'])
 for s in P['segments']:w.writerow([s['id'],s['a'],s['b'],s['speed'],s['start'],s['duration']])
# Reuse the proven native-resolution renderer, now with only the full gameplay layout.
t=(OLD/'render_edit.py').read_text();t=t.replace("PREVIEW='--proxy' in sys.argv;SOURCE=R/(P['proxy'] if PREVIEW else P['source']);", "PREVIEW=False;SOURCE=R/P['source'];")
# All source intervals have the same universal anime icon; no camera identity cards.
(R/'render_edit.py').write_text(t)
print('Chronological source coverage:',source_count,'seconds; output:',round(start,3),'seconds;',len(P['segments']),'segments')
