"""Demo-only authenticated Scratch/TurboWarp to App Inventor relay. No dependencies."""
import os,json,re,math,hmac,ssl,threading
from datetime import datetime,timezone
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
TOKEN=os.environ.get('RELAY_TOKEN','')
readings={};lock=threading.Lock()
def auth_diagnostic(headers):
 # Report structure only. Never echo a credential or its prefix/suffix.
 values=headers.get_all('Authorization',[]) or []
 raw=values[0] if values else ''
 bearer=raw.startswith('Bearer ')
 candidate=raw[7:] if bearer else ''
 if not TOKEN:reason='server_token_missing'
 elif len(values)>1:reason='multiple_authorization_headers'
 elif not raw:reason='missing_authorization_header'
 elif not bearer:reason='unexpected_authorization_format'
 elif not candidate:reason='empty_bearer_token'
 elif hmac.compare_digest(raw.encode('utf-8'),('Bearer '+TOKEN).encode('utf-8')):reason='accepted'
 else:reason='token_mismatch'
 return {'auth_status':reason,'authorization_header_count':len(values),'bearer_format':bearer,'received_token_length':len(candidate),'credential_has_outer_whitespace':candidate!=candidate.strip(),'credential_contains_quotes':any(c in candidate for c in ['"',"'"])}
def validate(data,athlete):
 if data.get('athleteId')!=athlete or data.get('simulated') is not True:raise ValueError('Matching athleteId and simulated:true are required')
 limits={'heart_rate':(30,250,True),'sleep_hours':(0,24,False),'activity_minutes':(0,1440,True),'soreness':(1,5,True),'energy':(1,5,True)}
 out={'athleteId':athlete,'simulated':True}
 for field,(low,high,integer) in limits.items():
  value=data.get(field)
  if type(value) not in (float,int) or not math.isfinite(value) or not low<=value<=high or (integer and not float(value).is_integer()):raise ValueError('Invalid '+field)
  out[field]=value
 out['timestamp']=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
 return out
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def respond(self,code,data=None):
  body=json.dumps(data).encode() if data is not None else b''
  self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
  self.send_header('Access-Control-Allow-Origin','https://turbowarp.org');self.send_header('Vary','Origin');self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type');self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS');self.end_headers();self.wfile.write(body)
 def do_OPTIONS(self):self.respond(204)
 def identity(self):
  diagnostic=auth_diagnostic(self.headers)
  if diagnostic['auth_status']!='accepted':
   print(json.dumps({'event':'relay_auth_rejected','method':self.command,**diagnostic}),flush=True)
   self.respond(401,{'error':'Unauthorized','relay_version':'diagnostics-1',**diagnostic});return None
  match=re.fullmatch(r'/readings/([A-Za-z0-9_-]{1,40})',self.path)
  if not match:self.respond(404,{'error':'Use /readings/{athleteId}'});return None
  return match[1]
 def do_GET(self):
  athlete=self.identity()
  if athlete is None:return
  with lock:row=readings.get(athlete)
  self.respond(200 if row else 404,row or {'error':'No reading for this athlete yet'})
 def do_POST(self):
  athlete=self.identity()
  if athlete is None:return
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=8192:raise ValueError('Invalid body size')
   data=validate(json.loads(self.rfile.read(length)),athlete)
   with lock:
    if athlete not in readings and len(readings)>=1000:raise ValueError('Demo roster limit reached')
    readings[athlete]=data
   self.respond(200,{'saved':athlete,'timestamp':data['timestamp'],'simulated':True})
  except (ValueError,TypeError,AttributeError):self.respond(400,{'error':'Invalid simulated reading'})
def main():
 if len(TOKEN)<24:raise SystemExit('Set RELAY_TOKEN to a random secret of at least 24 characters.')
 server=ThreadingHTTPServer((os.environ.get('RELAY_HOST','127.0.0.1'),int(os.environ.get('PORT','8080'))),Handler)
 cert,key=os.environ.get('TLS_CERT'),os.environ.get('TLS_KEY')
 if cert and key:
  context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key);server.socket=context.wrap_socket(server.socket,server_side=True)
 print('Relay diagnostics-1 listening. Authentication enforced; credentials are never logged. Records are simulated and held in memory.',flush=True)
 server.serve_forever()
if __name__=='__main__':main()
