#!/usr/bin/env python3
import json,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

class H(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        if self.path.endswith('/models'):
            b=json.dumps({'object':'list','data':[{'id':'deepseek-v4-flash','object':'model'}]}).encode()
            self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        n=int(self.headers.get('content-length','0')); req=json.loads(self.rfile.read(n) or b'{}')
        model=req.get('model','deepseek-v4-flash'); created=int(time.time())
        if self.path.endswith('/chat/completions'):
            if req.get('stream'):
                self.send_response(200); self.send_header('content-type','text/event-stream'); self.send_header('cache-control','no-cache'); self.end_headers()
                chunks=[
                    {'id':'chatcmpl-rotmock','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{'role':'assistant','content':'ROT_OK'},'finish_reason':None}]},
                    {'id':'chatcmpl-rotmock','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]},
                ]
                for c in chunks:
                    self.wfile.write(('data: '+json.dumps(c)+'\n\n').encode()); self.wfile.flush()
                self.wfile.write(b'data: [DONE]\n\n'); self.wfile.flush(); return
            out={'id':'chatcmpl-rotmock','object':'chat.completion','created':created,'model':model,'choices':[{'index':0,'message':{'role':'assistant','content':'ROT_OK'},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
            b=json.dumps(out).encode(); self.send_response(200); self.send_header('content-type','application/json'); self.send_header('content-length',str(len(b))); self.end_headers(); self.wfile.write(b); return
        self.send_response(404); self.end_headers()

if __name__=='__main__':
    ThreadingHTTPServer(('127.0.0.1',8899),H).serve_forever()
