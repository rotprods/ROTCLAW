#!/usr/bin/env python3
"""ROTCLAW model router. stdlib-only OpenAI-compatible subset -> configurable upstream."""
import json,os,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
UPSTREAM=os.environ.get("ROT_UPSTREAM_BASE_URL","https://ollama.com/v1").rstrip("/")
TOKEN=os.environ.get("ROT_ROUTER_TOKEN","")
API_KEY=os.environ.get("OLLAMA_API_KEY","")
ALIASES={"glm":"glm-5.2","glm-5.2":"glm-5.2","minimax":"minimax-m3","minimax-m3":"minimax-m3","kimi":"kimi-k2.6","kimi-k2.6":"kimi-k2.6","deepseek":"deepseek-v4-flash","deepseek-v4-flash":"deepseek-v4-flash"}
PROFILES={"reasoning":"glm-5.2","creative":"minimax-m3","research":"kimi-k2.6","coding":"deepseek-v4-flash","fast":"deepseek-v4-flash","balanced":"deepseek-v4-flash"}
def resolve(m): return ALIASES.get(m,PROFILES.get(m,m))
class H(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def sendj(self,code,obj):
  b=json.dumps(obj).encode(); self.send_response(code); self.send_header("content-type","application/json"); self.send_header("content-length",str(len(b))); self.send_header("cache-control","no-store"); self.end_headers(); self.wfile.write(b)
 def auth(self): return bool(TOKEN) and self.headers.get("authorization","")==f"Bearer {TOKEN}"
 def do_GET(self):
  if self.path=="/healthz": return self.sendj(200,{"ok":True,"upstream":UPSTREAM,"auth_configured":bool(TOKEN),"api_key_configured":bool(API_KEY)})
  if not self.auth(): return self.sendj(401,{"error":"unauthorized"})
  if self.path=="/v1/models": return self.sendj(200,{"object":"list","data":[{"id":x,"object":"model"} for x in sorted(set(ALIASES.values()))]})
  return self.sendj(404,{"error":"not_found"})
 def do_POST(self):
  if self.path not in {"/v1/chat/completions","/v1/responses"}: return self.sendj(404,{"error":"not_found"})
  if not self.auth(): return self.sendj(401,{"error":"unauthorized"})
  if not API_KEY: return self.sendj(503,{"error":"upstream_key_not_configured"})
  try:
   n=int(self.headers.get("content-length","0"))
   if n<=0 or n>2_000_000: return self.sendj(413,{"error":"invalid_body_size"})
   data=json.loads(self.rfile.read(n)); data["model"]=resolve(data.get("model","balanced")); body=json.dumps(data).encode()
   req=urllib.request.Request(UPSTREAM+self.path,data=body,headers={"authorization":f"Bearer {API_KEY}","content-type":"application/json"},method="POST")
   with urllib.request.urlopen(req,timeout=120) as r:
    out=r.read(10_000_000); self.send_response(r.status); self.send_header("content-type",r.headers.get("content-type","application/json")); self.send_header("content-length",str(len(out))); self.send_header("cache-control","no-store"); self.end_headers(); self.wfile.write(out)
  except urllib.error.HTTPError as e: return self.sendj(e.code,{"error":"upstream_http_error","status":e.code})
  except Exception: return self.sendj(502,{"error":"upstream_unavailable"})
if __name__=="__main__":
 host=os.environ.get("ROT_ROUTER_HOST","127.0.0.1"); port=int(os.environ.get("ROT_ROUTER_PORT","8787")); ThreadingHTTPServer((host,port),H).serve_forever()
