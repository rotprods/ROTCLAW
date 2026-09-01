#!/usr/bin/env python3
import json,time,os
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
LOG=os.environ.get('ROT_MOCK_LOG','')
def safe_log(path,req):
    if not LOG:return
    msgs=req.get('messages',[]) or []
    item={'path':path,'model':req.get('model'),'roles':[m.get('role') for m in msgs if isinstance(m,dict)],'tool_names':[t.get('function',{}).get('name') for t in (req.get('tools',[]) or []) if isinstance(t,dict)],'tool_results':[str(m.get('content',''))[-2000:] for m in msgs if isinstance(m,dict) and m.get('role')=='tool']}
    with open(LOG,'a',encoding='utf-8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
def has_tool_result(ms):return any(isinstance(m,dict) and m.get('role')=='tool' for m in ms)
def mode(ms):
    blob=' '.join(str(m.get('content','')) for m in ms if isinstance(m,dict))
    if 'ROT_FAILOVER_TEST' in blob:return 'failover'
    if 'ROT_ESCAPE_TEST' in blob:return 'escape'
    if 'ROT_ISOLATION_TEST' in blob:return 'isolation'
    if 'ROT_TOOL_TEST' in blob:return 'tool'
    if 'ROT_CONCURRENCY_TEST' in blob:return 'concurrency'
    return 'plain'
def exec_tool(req):
    tools=req.get('tools',[]) or []
    for t in tools:
        fn=t.get('function',{}) if isinstance(t,dict) else {}
        if fn.get('name')=='exec':return 'exec'
    return next((t.get('function',{}).get('name') for t in tools if isinstance(t,dict) and 'exec' in str(t.get('function',{}).get('name','')).lower()),None)
def call_args(m):
    if m=='isolation':
        cmd="set +e; touch /rotclaw-root-test 2>/tmp/root.err; R=$?; curl -m 2 -sS https://example.com >/tmp/net.out 2>/tmp/net.err; N=$?; printf 'ROOT_RC=%s NET_RC=%s UID=%s USER=%s\\n' \"$R\" \"$N\" \"$(id -u)\" \"$(id -un)\""
        return {'command':cmd,'host':'sandbox','timeoutSeconds':10}
    if m=='escape':return {'command':'touch /tmp/ROTCLAW_ESCAPE_SHOULD_NOT_EXIST','host':'gateway','timeoutSeconds':10}
    return {'command':'printf ROT_SANDBOX_TOOL_OK > /tmp/rotclaw-tool-proof && cat /tmp/rotclaw-tool-proof','host':'sandbox','timeoutSeconds':10}
def final_for(m):
    return {'tool':'ROT_TOOL_OK','isolation':'ROT_ISOLATION_OK','escape':'ROT_ESCAPE_DONE','failover':'ROT_FAILOVER_OK','concurrency':'ROT_CONCURRENCY_OK'}.get(m,'ROT_OK')
def send_sse(h,chunks):
    h.send_response(200);h.send_header('content-type','text/event-stream');h.send_header('cache-control','no-cache');h.end_headers()
    for c in chunks:h.wfile.write(('data: '+json.dumps(c)+'\n\n').encode());h.wfile.flush()
    h.wfile.write(b'data: [DONE]\n\n');h.wfile.flush()
def send_json(h,code,obj):
    b=json.dumps(obj).encode();h.send_response(code);h.send_header('content-type','application/json');h.send_header('content-length',str(len(b)));h.end_headers();h.wfile.write(b)
class H(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        if self.path.endswith('/models'):
            return send_json(self,200,{'object':'list','data':[{'id':m,'object':'model'} for m in ['deepseek-v4-flash','kimi-k2.6','glm-5.2','minimax-m3']]})
        self.send_response(404);self.end_headers()
    def do_POST(self):
        n=int(self.headers.get('content-length','0'));req=json.loads(self.rfile.read(n) or b'{}');safe_log(self.path,req)
        model=req.get('model','deepseek-v4-flash');created=int(time.time());ms=req.get('messages',[]) or [];m=mode(ms);name=exec_tool(req)
        if not self.path.endswith('/chat/completions'):self.send_response(404);self.end_headers();return
        # Deterministic failover fault injection: primary DeepSeek fails, Kimi succeeds.
        if m=='failover' and model=='deepseek-v4-flash':
            return send_json(self,503,{'error':{'message':'ROT injected primary failure','type':'server_error'}})
        if m not in ('plain','failover','concurrency') and not has_tool_result(ms) and name:
            args=json.dumps(call_args(m))
            tc={'index':0,'id':'call_rot_exec','type':'function','function':{'name':name,'arguments':args}}
            if req.get('stream'):
                send_sse(self,[{'id':'chatcmpl-tool','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{'role':'assistant','tool_calls':[tc]},'finish_reason':None}]},{'id':'chatcmpl-tool','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{},'finish_reason':'tool_calls'}]}]);return
            out={'id':'chatcmpl-tool','object':'chat.completion','created':created,'model':model,'choices':[{'index':0,'message':{'role':'assistant','content':None,'tool_calls':[dict(tc,**{'index':None})]},'finish_reason':'tool_calls'}]}
        else:
            final=final_for(m)
            if req.get('stream'):
                send_sse(self,[{'id':'chatcmpl-final','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{'role':'assistant','content':final},'finish_reason':None}]},{'id':'chatcmpl-final','object':'chat.completion.chunk','created':created,'model':model,'choices':[{'index':0,'delta':{},'finish_reason':'stop'}]}]);return
            out={'id':'chatcmpl-final','object':'chat.completion','created':created,'model':model,'choices':[{'index':0,'message':{'role':'assistant','content':final},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
        send_json(self,200,out)
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8899),H).serve_forever()
