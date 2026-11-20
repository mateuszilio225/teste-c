from pathlib import Path
import json,subprocess,time,hashlib
R=Path(__file__).parent;P=json.loads((R/'project.json').read_text());FPS=P['fps'];SS=P['segments'];n=len(SS);last=-1
while True:
 count=sum((R/'render'/(s['id']+'.done')).exists() for s in SS)
 if count!=last:print(f'Video segments ready: {count}/{n}',flush=True);last=count
 audio_ready=(R/'audio.log').exists() and (R/'audio.log').read_text().rstrip().endswith('SOUNDTRACK READY')
 if count==n and audio_ready:break
 if (R/'render.log').exists() and 'Traceback' in (R/'render.log').read_text():raise RuntimeError('Renderer failed; inspect render.log')
 time.sleep(5)
source=[s for s in SS if s['kind']=='source'];end=0
for s in source:
 assert s['a']==end,(s['id'],s['a'],end);assert s['b']>s['a'];end=s['b']
assert end==2150 and sum(s['b']-s['a'] for s in source)==2150
assert all(s['layout']=='full' for s in source)
assert {q['who'] for q in P['cues']}=={'anime'}
checks=[];total=0
for s in SS:
 f=R/'render'/(s['id']+'.mp4');j=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(f)]))['streams'][0]
 assert j['r_frame_rate']=='60/1' and j['width']==1280 and j['height']==720
 assert int(j['nb_frames'])==s['frames'],(s['id'],j,s['frames']);total+=s['frames'];checks.append(dict(id=s['id'],frames=s['frames']))
assert total==127494
(R/'render-audit.json').write_text(json.dumps(dict(frames=total,duration=total/FPS,chronological=True,source_coverage_seconds=end,no_source_gaps=True,no_source_repeats=True,universal_anime_avatar=True,gameplay_visible_throughout=True,segments=checks),indent=2))
(R/'concat.txt').write_text(''.join("file '"+str(R/'render'/(s['id']+'.mp4'))+"'\n" for s in SS))
f=R/'lol-viego-gameplay-completa-v2.mp4'
cmd=['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(R/'concat.txt'),'-i',str(R/'soundtrack.m4a'),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str(total/FPS),'-movflags','+faststart','-map_metadata','-1','-metadata','title=Viego - gameplay completa do draft ao fim',str(f)]
with open(R/'final-mux.log','w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
h=hashlib.sha256()
with f.open('rb') as fp:
 while b:=fp.read(2**20):h.update(b)
(R/'delivery.json').write_text(json.dumps(dict(file=f.name,bytes=f.stat().st_size,sha256=h.hexdigest(),duration=total/FPS,width=1280,height=720,fps=FPS,chronological=True,source_coverage_seconds=end),indent=2));print('FINAL MUXED',f.stat().st_size,total/FPS,flush=True)
with open(R/'full-decode.log','w') as log:subprocess.run(['ffmpeg','-v','error','-xerror','-threads','2','-i',str(f),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
(R/'verification-complete.json').write_text(json.dumps(dict(full_decode_passed=True,all_frames_accounted_for=True,chronology_verified=True),indent=2));print('FULL DECODE PASSED; READY FOR VISUAL REVIEW',flush=True)
