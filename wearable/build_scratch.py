from pathlib import Path
import json,zipfile,hashlib,itertools
root=Path(__file__).parent
values={'AthleteID':'Player-01','HeartRate':90,'SleepHours':8,'ActivityMin':0,'Soreness':1,'Energy':4,'Intensity':1,'ReadingSeq':0}
variables={k:[k,v] for k,v in values.items()};blocks={};counter=itertools.count()
def block(op,inputs=None,fields=None):
 i='b'+str(next(counter));blocks[i]={'opcode':op,'next':None,'parent':None,'inputs':inputs or {},'fields':fields or {},'shadow':False,'topLevel':False};return i
def literal(v):return [1,[4,str(v)]] if isinstance(v,(int,float)) else [1,[10,v]]
def ref(i,parent):blocks[i]['parent']=parent;return [2,i]
def variable(name):return [3,[12,name,name],[4,'0']]
def setvar(name,value):return block('data_setvariableto',{'VALUE':literal(value)},{'VARIABLE':[name,name]})
def link(ids,parent=None):
 for idx,i in enumerate(ids):blocks[i]['parent']=ids[idx-1] if idx else parent;blocks[i]['next']=ids[idx+1] if idx+1<len(ids) else None
 return ids[0]
flag=block('event_whenflagclicked');blocks[flag].update(topLevel=True,x=50,y=50)
setup=[setvar(k,v) for k,v in values.items()];reset=block('sensing_resettimer');loop=block('control_forever');link([flag]+setup+[reset,loop]);blocks[flag]['parent']=None
random=block('operator_random',{'FROM':literal(80),'TO':literal(110)})
mul=block('operator_multiply',{'NUM1':variable('Intensity'),'NUM2':literal(25)})
add=block('operator_add');blocks[add]['inputs']={'NUM1':ref(random,add),'NUM2':ref(mul,add)}
hr=setvar('HeartRate',90);blocks[hr]['inputs']['VALUE']=ref(add,hr)
timer=block('sensing_timer');divide=block('operator_divide',{'NUM2':literal(60)});blocks[divide]['inputs']['NUM1']=ref(timer,divide)
rounding=block('operator_mathop',fields={'OPERATOR':['floor',None]});blocks[rounding]['inputs']['NUM']=ref(divide,rounding)
activity=setvar('ActivityMin',0);blocks[activity]['inputs']['VALUE']=ref(rounding,activity)
seq=block('data_changevariableby',{'VALUE':literal(1)},{'VARIABLE':['ReadingSeq','ReadingSeq']});wait=block('control_wait',{'DURATION':literal(5)})
blocks[loop]['inputs']['SUBSTACK']=ref(link([hr,activity,seq,wait],loop),loop)
for n in [1,2,3]:
 event=block('event_whenkeypressed',fields={'KEY_OPTION':[str(n),None]});blocks[event].update(topLevel=True,x=560,y=50+n*120)
 action=setvar('AthleteID','Player-0'+str(n));link([event,action]);blocks[event]['parent']=None
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360"><rect width="480" height="360" fill="#edf4fb"/><rect width="480" height="74" fill="#0866de"/><text x="20" y="32" fill="white" font-size="21" font-family="Arial" font-weight="bold">Youth Sports Fatigue AI</text><text x="20" y="57" fill="white" font-size="15" font-family="Arial">SIMULATED WEARABLE • no real sensors</text><text x="20" y="275" fill="#17334b" font-family="Arial" font-size="14">Green flag: generate readings every 5 seconds.</text><text x="20" y="297" fill="#17334b" font-family="Arial" font-size="14">Keys 1 / 2 / 3: switch student. Intensity: 0 to 3.</text><text x="20" y="319" fill="#17334b" font-family="Arial" font-size="14">Sleep, soreness, energy: adjust sliders manually.</text><text x="20" y="341" fill="#17334b" font-family="Arial" font-size="14">TurboWarp extension sends readings to your relay.</text></svg>'''
asset=hashlib.md5(svg.encode()).hexdigest();monitors=[]
for idx,(k,v) in enumerate(values.items()):
 slider=k in ['SleepHours','Soreness','Energy','Intensity'];limits={'SleepHours':(0,12),'Soreness':(1,5),'Energy':(1,5),'Intensity':(0,3)}.get(k,(0,100))
 monitors.append({'id':k,'mode':'slider' if slider else 'default','opcode':'data_variable','params':{'VARIABLE':k},'spriteName':None,'value':v,'width':0,'height':0,'x':20+(idx%2)*230,'y':90+(idx//2)*38,'visible':True,'sliderMin':limits[0],'sliderMax':limits[1],'isDiscrete':k!='SleepHours'})
project={'targets':[{'isStage':True,'name':'Stage','variables':variables,'lists':{},'broadcasts':{},'blocks':blocks,'comments':{},'currentCostume':0,'costumes':[{'name':'Wearable dashboard','assetId':asset,'md5ext':asset+'.svg','dataFormat':'svg','rotationCenterX':240,'rotationCenterY':180}],'sounds':[],'volume':100,'layerOrder':0,'tempo':60,'videoTransparency':50,'videoState':'off','textToSpeechLanguage':None}], 'monitors':monitors,'extensions':[],'meta':{'semver':'3.0.0','vm':'0.2.0','agent':'Youth Sports Fatigue AI simulator'}}
with zipfile.ZipFile(root/'WearableSimulator.sb3','w',zipfile.ZIP_DEFLATED) as z:z.writestr('project.json',json.dumps(project));z.writestr(asset+'.svg',svg)
print('Created WearableSimulator.sb3')
