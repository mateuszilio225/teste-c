from pathlib import Path
import subprocess,json,numpy as np
R=Path(__file__).parent;P=json.loads((R/'project.json').read_text());SR=48000
log=open(R/'audio-encode.log','w');enc=subprocess.Popen(['ffmpeg','-hide_banner','-y','-f','f32le','-ar',str(SR),'-ac','2','-i','pipe:0','-af','loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json','-ar',str(SR),'-c:a','aac','-b:a','192k','-movflags','+faststart',str(R/'soundtrack.m4a')],stdin=subprocess.PIPE,stdout=log,stderr=log)
rng=np.random.default_rng(2002)
def read(path,start,duration,speed=1):
 cmd=['ffmpeg','-v','error','-threads','1','-ss',str(start),'-t',str(duration),'-i',str(path),'-vn','-ac','2','-ar',str(SR)]
 if speed!=1:cmd+=['-af',f'atempo={speed}']
 z=subprocess.check_output(cmd+['-f','f32le','pipe:1']);return np.frombuffer(z,dtype='<f4').reshape(-1,2).copy()
def bed(n):
 t=np.arange(n)/SR;v=np.zeros(n)
 for k in range(int(t[-1]/.32)+1):
  u=t-k*.32;gate=u>=0;u=np.maximum(u,0)
  if k%2==0:v+=.13*np.sin(2*np.pi*(64*u+8*(1-np.exp(-u*36))))*np.exp(-u*24)*gate
  v+=rng.normal(0,.02,n)*np.exp(-u*90)*gate
  f=[220,261.63,293.66,329.63][k%4];v+=.045*np.sin(2*np.pi*f*u)*np.exp(-u*11)*gate
 return np.stack([v,v],1)
def continuous(a,b):return a and b and a['kind']==b['kind']=='source' and a['b']==b['a'] and a['speed']==b['speed']==1 and not(a['mute_source'] or b['mute_source'])
report=[];ss=P['segments']
for i,s in enumerate(ss):
 n=s['frames']*800
 if s['kind']=='card':x=read(R/s['audio'],0,s['duration'])*3
 elif s['mute_source']:x=bed(n)
 else:x=read(R/'native-audio.m4a',s['a'],s['b']-s['a'],s['speed'])
 if len(x)<n:x=np.pad(x,((0,n-len(x)),(0,0)))
 x=x[:n];fade=min(240,len(x)//2)
 if i==0 or not continuous(ss[i-1],s):x[:fade]*=np.linspace(0,1,fade)[:,None]
 if i==len(ss)-1 or not continuous(s,ss[i+1]):x[-fade:]*=np.linspace(1,0,fade)[:,None]
 if i==len(ss)-1:x[-14400:]*=np.linspace(1,0,14400)[:,None]
 report.append(dict(id=s['id'],samples=n,rms=float(np.sqrt((x*x).mean())),peak=float(np.abs(x).max())))
 enc.stdin.write(x.astype('<f4').tobytes());print('Audio',s['id'],n,flush=True)
enc.stdin.close();assert enc.wait()==0
(R/'audio-audit.json').write_text(json.dumps(report,indent=2));print('SOUNDTRACK READY',flush=True)
