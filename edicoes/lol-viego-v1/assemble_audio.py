from pathlib import Path
import subprocess,json,numpy as np
R=Path(__file__).parent;P=json.loads((R/'project.json').read_text());SR=48000
out=R/'soundtrack.m4a';log=open(R/'audio-encode.log','w')
enc=subprocess.Popen(['ffmpeg','-hide_banner','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','pipe:0','-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-ar',str(SR),'-c:a','aac','-b:a','192k','-movflags','+faststart',str(out)],stdin=subprocess.PIPE,stdout=log,stderr=log)
rng=np.random.default_rng(2002)
def read(path,start,duration):
 z=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-ss',str(start),'-i',str(path),'-t',str(duration),'-vn','-ac','2','-ar',str(SR),'-f','f32le','pipe:1']);return np.frombuffer(z,dtype='<f4').reshape(-1,2).copy()
def bed(n):
 t=np.arange(n)/SR;v=np.zeros(n);beat=.32
 for k in range(int(t[-1]/beat)+1):
  u=t-k*beat;gate=(u>=0);u=np.maximum(u,0)
  if k%2==0:v+=.16*np.sin(2*np.pi*(64*u+8*(1-np.exp(-u*36))))*np.exp(-u*24)*gate
  v+=rng.normal(0,.025,n)*np.exp(-u*90)*gate
  f=[220,261.63,293.66,329.63][k%4];v+=.055*np.sin(2*np.pi*f*u)*np.exp(-u*11)*gate
 return np.stack([v,v],1)
report=[]
for s in P['segments']:
 n=s['frames']*800
 if s['kind']=='card':x=read(R/s['audio'],0,s['duration'])*3
 elif s['mute_source']:x=bed(n)
 else:x=read(R/'native-audio.m4a',s['a'],s['b']-s['a'])
 if len(x)<n:x=np.pad(x,((0,n-len(x)),(0,0)))
 x=x[:n];fade=min(240,len(x)//2);x[:fade]*=np.linspace(0,1,fade)[:,None];x[-fade:]*=np.linspace(1,0,fade)[:,None]
 if s==P['segments'][-1]:x[-14400:]*=np.linspace(1,0,14400)[:,None]
 report.append(dict(id=s['id'],samples=n,rms=float(np.sqrt((x*x).mean())),peak=float(np.abs(x).max())))
 enc.stdin.write(x.astype('<f4').tobytes());print('Audio',s['id'],n,flush=True)
enc.stdin.close();assert enc.wait()==0
(R/'audio-audit.json').write_text(json.dumps(report,indent=2));print('SOUNDTRACK READY',flush=True)
