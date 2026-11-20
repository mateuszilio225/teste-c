from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).parent;P=json.loads((R/'project.json').read_text());fps=P['fps'];tot=0;checks=[]
for s in P['segments']:
 f=R/'render'/f"{s['id']}.mp4";j=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(f)]))['streams'][0]
 assert int(j['nb_frames'])==s['frames'],(s['id'],j,s['frames']);assert j['width']==1280 and j['height']==720 and j['r_frame_rate']=='60/1';tot+=int(j['nb_frames']);checks.append(dict(id=s['id'],frames=int(j['nb_frames'])))
assert tot==54801,(tot,P['duration']);(R/'render-audit.json').write_text(json.dumps(dict(frames=tot,duration=tot/fps,segments=checks),indent=2))
(R/'concat.txt').write_text(''.join(f"file '{R/'render'/s['id']}.mp4'\n" for s in P['segments']))
cmd=['ffmpeg','-hide_banner','-y','-f','concat','-safe','0','-i',str(R/'concat.txt'),'-i',str(R/'soundtrack.m4a'),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str(tot/fps),'-movflags','+faststart','-map_metadata','-1','-metadata','title=Viego - gameplay e zoeira',str(R/'lol-viego-gameplay-zueira-v1.mp4')]
with open(R/'final-mux.log','w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
f=R/'lol-viego-gameplay-zueira-v1.mp4';h=hashlib.sha256()
with f.open('rb') as fp:
 while b:=fp.read(2**20):h.update(b)
(R/'delivery.json').write_text(json.dumps(dict(file=f.name,sha256=h.hexdigest(),bytes=f.stat().st_size,duration=tot/fps,width=1280,height=720,fps=60),indent=2));print('FINAL READY',tot/fps,f.stat().st_size,flush=True)
with open(R/'final-decode-check.log','w') as log:subprocess.run(['ffmpeg','-v','error','-xerror','-threads','2','-i',str(f),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
print('FULL DECODE PASSED',flush=True)
