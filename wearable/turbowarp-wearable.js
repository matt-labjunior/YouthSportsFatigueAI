(function(Scratch){
'use strict';
if(!Scratch.extensions.unsandboxed)throw Error('Wearable demo requires Run without sandbox.');
class Wearable {
 constructor(){this.timer=null;this.token='';this.url='';this.last='';this.busy=false;this.message='Stopped';this.generation=0;Scratch.vm.runtime.on('PROJECT_STOP_ALL',()=>this.stop());}
 getInfo(){return {id:'youthwearable',name:'Simulated Wearable',color1:'#0866de',blocks:[{opcode:'start',blockType:Scratch.BlockType.COMMAND,text:'start streaming to [URL]',arguments:{URL:{type:Scratch.ArgumentType.STRING,defaultValue:'https://your-relay.example'}}},{opcode:'stop',blockType:Scratch.BlockType.COMMAND,text:'stop streaming'},{opcode:'status',blockType:Scratch.BlockType.REPORTER,text:'stream status'}]};}
 value(name){const v=Scratch.vm.runtime.getTargetForStage().lookupVariableByNameAndType(name,'');if(!v)throw Error('Missing stage variable '+name);return v.value;}
 start(args){this.stop();try{const u=new URL(String(args.URL));if(u.protocol!=='https:'||u.username||u.password||u.search||u.hash)throw Error('Use a plain HTTPS relay address');const token=window.prompt('Relay bearer token (session only; do not put it in Scratch variables):');if(!token){this.message='Cancelled';return;}this.token=token;this.url=u.origin+u.pathname.replace(/\/$/,'');this.last='';this.message='Waiting for a new simulated reading';this.timer=setInterval(()=>this.tick(),1000);this.tick();}catch(e){this.message=e.message;}}
 async tick(){if(this.busy)return;const generation=this.generation;try{const id=String(this.value('AthleteID')),seq=Number(this.value('ReadingSeq'));if(!Number.isFinite(seq)||seq<1)return;if(!/^[A-Za-z0-9_-]{1,40}$/.test(id))throw Error('Invalid AthleteID');const signature=String(seq);if(signature===this.last)return;const row={athleteId:id,simulated:true,heart_rate:Number(this.value('HeartRate')),sleep_hours:Number(this.value('SleepHours')),activity_minutes:Number(this.value('ActivityMin')),soreness:Number(this.value('Soreness')),energy:Number(this.value('Energy'))};this.busy=true;const response=await Scratch.fetch(this.url+'/readings/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+this.token},body:JSON.stringify(row)});if(!response.ok)throw Error('Relay HTTP '+response.status);if(generation!==this.generation)return;this.last=signature;this.message='Sent SIMULATED '+id+' #'+seq;}catch(e){if(generation===this.generation)this.message='Not sent: '+e.message;}finally{this.busy=false;}}
 stop(){if(this.timer)clearInterval(this.timer);this.timer=null;this.token='';this.generation++;this.message='Stopped';}
 status(){return this.message;}
}
Scratch.extensions.register(new Wearable());
})(Scratch);
