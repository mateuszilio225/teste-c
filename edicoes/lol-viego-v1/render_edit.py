from pathlib import Path
import json,subprocess,math,concurrent.futures,sys,textwrap,shutil
from PIL import ImageFont
R=Path(__file__).parent;A=R/'assets';V=R/'render';V.mkdir(exist_ok=True);P=json.loads((R/'project.json').read_text());FPS=60;W=1280;H=720
PREVIEW='--proxy' in sys.argv;SOURCE=R/(P['proxy'] if PREVIEW else P['source']);assert SOURCE.exists(),f'Missing required media: {SOURCE}'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def run(cmd,log):
 with open(log,'w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
def tm(t):
 n=round(max(0,t)*100);h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100);return f'{h}:{m:02}:{s:02}.{n:02}'
def ev(a,b,text,layer=2):return f'Dialogue: {layer},{tm(a)},{tm(b)},Text,,0,0,0,,{text}\n'
def box(x,y,w,h):return f'm {x+14} {y} l {x+w-14} {y} b {x+w} {y} {x+w} {y} {x+w} {y+14} l {x+w} {y+h-14} b {x+w} {y+h} {x+w} {y+h} {x+w-14} {y+h} l {x+14} {y+h} b {x} {y+h} {x} {y+h} {x} {y+h-14} l {x} {y+14} b {x} {y} {x} {y} {x+14} {y}'
HEAD='''[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Text,DejaVu Sans,33,&H00FFFFFF,&H00FFFFFF,&H00100D09,&H90000000,-1,0,0,0,100,100,0,0,1,1.4,1.0,5,15,15,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
def wrap(t,size,maxwidth=535):
 font=ImageFont.truetype(FONT,size);out=[];line=''
 for word in t.split():
  trial=(line+' '+word).strip()
  if line and font.getlength(trial)>maxwidth:out.append(line);line=word
  else:line=trial
 if line:out.append(line)
 return r'\N'.join(out)
def render(s):
 out=V/f"{s['id']}.mp4";done=out.with_suffix('.done');N=s['frames'];D=N/FPS
 if out.exists() and done.exists() and done.read_text()==str(N):return out
 if s['kind']=='card':
  run(['ffmpeg','-hide_banner','-y','-i',str(R/s['media']),'-vf',f'fps={FPS},format=yuv420p,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709','-frames:v',str(N),'-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','20','-r',str(FPS),str(out)],out.with_suffix('.log'));done.write_text(str(N));print('Rendered',s['id'],D,flush=True);return out
 a=s['a'];b=s['b'];speed=s['speed'];layout=s['layout'];preroll=min(a,5);seek=a-preroll
 fg=[f'[0:v]trim=start={preroll}:duration={b-a},setpts=(PTS-STARTPTS)/{speed},fps={FPS},scale=1280:720:flags=lanczos,tpad=stop_mode=clone:stop_duration=0.20,trim=duration={D},setsar=1[scaled]']
 ass=HEAD;extra=[];idx=1
 def png(path,x,y,lo=0,hi=D,size=None,name='im'):
  nonlocal idx
  extra.extend(['-i',str(path)]);tag=f'{name}{idx}';it=f'{idx}:v'
  if size:fg.append(f'[{it}]scale={size[0]}:{size[1]}:flags=lanczos,format=rgba[{tag}]');it=tag
  nx=f'o{idx}';fg.append(f"[{base[0]}][{it}]overlay=x='{x}':y='{y}':enable='between(t,{lo:.6f},{hi:.6f})':eof_action=repeat[{nx}]");base[0]=nx;idx+=1
 windows=s.get('zoom_windows',[])
 if windows and layout=='full':
  terms=[f'if(between(in/{FPS},{(lo-a)/speed},{(hi-a)/speed}),1+0.065*sin(PI*(in/{FPS}-{(lo-a)/speed})/{(hi-lo)/speed}),1)' for lo,hi in windows]
  z='*'.join(terms);fg.append(f"[scaled]zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1280x720:fps={FPS}[punched]");fg.append('[punched]null[zoomed]');fg[0]=fg[0].replace('[scaled]','[prezoom]');fg[-2]=fg[-2].replace('[scaled]','[prezoom]');fg[-1]=fg[-1].replace('[zoomed]','[scaled]')
 if layout=='trio':
  fg.append('[scaled]split=4[bgraw][c0][c1][c2]');fg.append('[bgraw]gblur=sigma=20,eq=brightness=-0.31:saturation=0.65[back]');base=['back']
  cameras=[('geandre',(0,0,284,180)),('menta',(0,548,308,172)),('lucas',(996,508,284,212))]
  for i,(who,(x,y,w,h)) in enumerate(cameras):
   ox=45+i*402;fg.append(f'[c{i}]crop={w}:{h}:{x}:{y},scale=374:292:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,pad=374:292:(ow-iw)/2:(oh-ih)/2:color=0x0C131B,setsar=1[cam{i}]');fg.append(f"[{base[0]}][cam{i}]overlay=x={ox}:y='193+12*exp(-12*t)':shortest=1[p{i}]");base[0]=f'p{i}';fg.append(f'[{base[0]}]drawbox=x={ox-2}:y=191:w=378:h=296:color=0xC7B47A@0.45:t=2[fr{i}]');base[0]=f'fr{i}'
   png(A/'avatars'/f'{who}-60.png',str(ox+157),'505',size=(60,60),name='who')
   ass+=ev(0,D,rf'{{\an5\pos({ox+187},584)\fs17\c&HBDD0D8&\bord0}}{who.upper()}')
 else:
  fg.append('[scaled]drawbox=x=284:y=0:w=996:h=20:color=0x080D14:t=fill,drawbox=x=308:y=694:w=688:h=26:color=0x080D14:t=fill[clean]');base=['clean']
  if speed>1:ass+=ev(0,D,rf'{{\an7\pos(306,47)\fs22\c&H8EEED9&\bord2\fad(70,100)}}×{speed:g}')
 ybox=611 if layout=='trio' else 520;ytxt=ybox+45;yring=ybox+16
 for q in P['cues']:
  lo=max(a,q['a']);hi=min(b,q['b'])
  if hi-lo<.10 or speed>1:continue
  lo=(lo-a)/speed;hi=min(D,(hi-a)/speed);ass+=ev(lo,hi,rf'{{\an7\pos(0,0)\p1\bord0\shad0\c&H19120D&\alpha&H22&\fad(50,70)}}'+box(414 if q.get('who') else 330,ybox,554 if q.get('who') else 638,90),0)
  text=wrap(q['text'],q['size']);center=685 if q.get('who') else 648
  ass+=ev(lo,hi,rf"{{\pos({center},{ytxt})\fs{q['size']}\c&H{q['color']}&\fad(50,70)}}"+text)
  if q.get('who'):png(A/'avatars'/f"{q['who']}-60.png",'344',f'{yring}+2*sin(8*t)',lo,hi)
 for e in s.get('effects',[]):
  lo=max(0,(e['a']-a)/speed);hi=min(D,(e['b']-a)/speed)
  if hi<=lo:continue
  typ=e['type']
  if typ=='emoji':png(A/'overlays'/f"{e['name']}.png",'970',f'430+5*sin(7*(t-{lo}))',lo,hi)
  elif typ=='champion_reveal':png(A/'overlays/viego-pick.png',f'866+70*exp(-12*(t-{lo}))','130',lo,hi)
  elif typ=='item_focus':
   png(A/'overlays/hydra-focus.png',f'260+25*exp(-10*(t-{lo}))','193',lo,hi);png(A/'overlays/coin.png','1050',f'102+14*sin(8*(t-{lo}))',lo,hi,size=(74,74))
  elif typ=='combo_note':png(A/'overlays/jhin-combo.png','380','177',lo,hi)
  elif typ=='champion_pop':png(A/'Bard-icon.png','1080',f'100+8*sin(7*(t-{lo}))',lo,hi,size=(112,112))
  elif typ=='double_kill':ass+=ev(lo,hi,rf'{{\pos(640,189)\fs53\c&HAFE7F4&\bord3\shad2\fscx116\fscy116\t(0,220,\fscx100\fscy100)\fad(50,170)}}DUPLA!')
  elif typ=='sleep':ass+=ev(lo,hi,rf'{{\pos(681,277)\fs60\c&HFFFFFF&\bord3\frz-8\fad(60,100)}}Z z z...')
  elif typ=='reset':
   png(A/'Viego-passive.png','1050','138',lo,hi,size=(68,68));ass+=ev(lo,hi,rf'{{\pos(1085,230)\fs27\c&H8EEED9&\bord2\fad(45,80)}}RESET')
  elif typ=='exit_popup':ass+=ev(lo,hi,rf'{{\pos(640,106)\fs31\c&H8EEED9&\bord2\fad(60,100)}}15/3/5  →  RECONECTAR?')
 if PREVIEW:ass+=ev(0,D,r'{\an7\pos(324,706)\fs10\c&H9EA6AA&\bord0}PRÉVIA DE EDIÇÃO / MÍDIA LEVE')
 if s['id']==P['segments'][-1]['id']:fg.append(f'[{base[0]}]fade=t=out:st={max(0,D-.3)}:d=0.3[ending]');base[0]='ending'
 assfile=out.with_suffix('.ass');assfile.write_text(ass);fg.append(f"[{base[0]}]subtitles='{assfile}',format=yuv420p,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]");script=out.with_suffix('.ffscript');script.write_text(';\n'.join(fg))
 cmd=['ffmpeg','-hide_banner','-y','-threads','1','-ss',str(seek),'-t',str(b-seek),'-i',str(SOURCE),*extra,'-filter_complex_threads','1','-filter_complex_script',str(script),'-map','[v]','-an','-frames:v',str(N),'-c:v','libx264','-threads','2','-preset','veryfast','-crf','21','-r',str(FPS),'-pix_fmt','yuv420p','-color_range','tv','-map_metadata','-1',str(out)]
 try:run(cmd,out.with_suffix('.log'))
 except Exception:
  print(out.with_suffix('.log').read_text()[-1800:],flush=True);raise
 done.write_text(str(N));print('Rendered',s['id'],round(D,2),flush=True);return out
if __name__=='__main__':
 chosen=P['segments']
 if '--first-two' in sys.argv:chosen=chosen[:2]
 with concurrent.futures.ThreadPoolExecutor(2) as pool:
  for f in [pool.submit(render,s) for s in chosen]:f.result()
 print('SILENT RENDERS READY',flush=True)
