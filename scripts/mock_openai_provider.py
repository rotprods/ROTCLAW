#!/usr/bin/env python3
import json,time,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
LOG=os.environ.get('ROT_MOCK_LOG','')
def log(obj):
    if LOG:
        with open(LOG,'a',encoding='utf-8') as f: f.write(json.dumps(obj,ensure_ascii=False)+'\n')
def has_tool_result(messages): return any(isinstance(m,dict) and m.get('role')=='tool' for m in messages)
def wants_tool(messages): return any(isinstance(m,dict) and 'ROT_TOOL_TEST' in str(m.get('content','')) for m in messages)
def exec_tool(req):
    tools=req.get('tools',[]) or []
    for t in tools:
        fn=t.get('function',{}) if isinstance(t,dict) else {}
        if fn.get('name')=='exec': return 'exec'
    for t in tools:
        fn=t.get('function',{}) if isinstance(t,dict) else {}
        if 'exec' in str(fn.get('name','')).lower(): return fn.get('name')
    return None
def send_sse(h,chunks):
    h.send_response(200); h.send_header('content-type','text/event-stream'); h.send_header('cache-control','no-cache'); h.end_headers()
    for c in chunks: h.wfile.write(('data: '+json.dumps(c)+'\n\n').encode()); h.wfile.flush()
    h.wfile.write(b'data: [DONE]\n\n'); h.wfile.flush()
class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path.endswith('/models'):
            b=json.dumps({'object':'list','data':[{'id':'deepseek-v4-flash','object':'model'}]}).encode(); self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        n=int(self.headers.get('content-length','0')); req=json.loads(self.rfile.read(n) or b'{}'); log({'path':self.path,'request':req})
        model=req.get('model','deepseek-v4-flash'); created=int(time.time()); messages=req.get('messages',[]) or []; tool_mode=wants_tool(messages); tool_name=exec_tool(req)
        if not self.path.endswith('/chat/completions'): self.send_response(404); self.end_headers(); return
        if tool_mode and not has_tool_result(messages) and tool_name:
            args=json.dumps({'command':'printf ROT_SANDBOX_TOOL_OK > /tmp/rotclaw-tool-proof && cat /tmp/rotclaw-tool-proof','host':'sandbox','timeoutSeconds':10})
            if req.get('stream'):
                send_sse(self,[{'id':'chatcmpl-tool','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{'role':'assistant','tool_calls':[{'index':0,'id':'call_rot_exec','type':'function','function':{'name':tool_name,'arguments':args}}]},'finish_reason':None}]},{'id':'chatcmpl-tool','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{},'finish_reason':'tool_calls'}]}]); return
            out={'id':'chatcmpl-tool','object':'chat.completion','created':created,'model':model,'choices':[{'index':0,'message':{'role':'assistant','content':None,'tool_calls':[{'id':'call_rot_exec','type':'function','function':{'name':tool_name,'arguments':args}}]},'finish_reason':'tool_calls'}]}
        else:
            final='ROT_TOOL_OK' if tool_mode and has_tool_result(messages) else 'ROT_OK'
            if req.get('stream'):
                send_sse(self,[{'id':'chatcmpl-rotmock','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{'role':'assistant','content':final},'finish_reason':None}]},{'id':'chatcmpl-rotmock','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]}]); return
            out={'id':'chatcmpl-rotmock','object':'chat.completion','created':created,'model':model,'choices':[{'index':0,'message':{'role':'assistant','content':final},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
        b=json.dumps(out).encode(); self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b)
if __name__=='__main__': ThreadingHTTPServer(('127.0.0.1',8899),H).serve_forever()
