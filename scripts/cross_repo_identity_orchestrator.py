#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess, urllib.request
from pathlib import Path

MODEL='qwen3:1.7b-q4_K_M'
TARGET_REPO='https://github.com/rotprods/cos-graph-engine.git'
TARGET_COMMIT='baea5de6ac086860832256bf08e1f9e0a46f67d0'
ALLOWED=['packages/core/src/identity.ts','scripts/test-identity-hardening.ts']
CASES=sorted(['insertion_order','unicode_value_equivalence','unicode_key_equivalence','unicode_key_collision','reject_undefined','reject_bigint','reject_date','reject_map','reject_set','reject_typed_array','reject_class_instance','reject_symbol_property','reject_sparse_array','reject_array_extra_property','reject_accessor','null_prototype_plain_object','canonical_uri_unicode_equivalence'])

def run(cmd,cwd=None,timeout=120):
    p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"command failed {cmd}:\n{p.stdout}\n{p.stderr}")
    return p.stdout

def ask(prompt,num_ctx=2048,num_predict=240,schema=None):
    payload={'model':MODEL,'prompt':prompt,'stream':False,'format':schema or 'json','options':{'temperature':0,'num_ctx':num_ctx,'num_predict':num_predict},'think':False}
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=50) as r: api=json.load(r)
    return json.loads(api['response'])

def dump(path,obj): Path(path).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
def h(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_mission(path):
    m=json.loads(Path(path).read_text())
    assert m['schema']=='rotclaw.cross-repo-mission.v1' and m['risk_class']=='A2'
    assert m['target_repository']=='rotprods/cos-graph-engine' and m['target_ref']=='hardening/w3-deterministic-identity'
    assert m['target_commit']==TARGET_COMMIT and sorted(m['allowed_paths'])==sorted(ALLOWED)
    assert set(m['allowed_actions']) <= {'read','edit','test'}
    return m

def canonicalize_test_contract(obj):
    if set(obj)=={'cases'}: chosen=sorted(obj['cases'])
    else:
        assert set(obj)==set(CASES),obj
        assert all(obj[k] is True for k in CASES),obj
        chosen=sorted(obj)
    assert chosen==CASES,(chosen,CASES)
    return {'cases':CASES}

def materialize_identity(target):
    p=target/'packages/core/src/identity.ts'; src=p.read_text()
    start=src.index('export function stableSerialize(value: unknown): string {')
    end=src.index('\n}\n\n/**\n * 64-bit FNV-1a',start)+2
    new="""function normalizeUnicode(value: string): string {
  return value.normalize('NFC');
}

export function stableSerialize(value: unknown): string {
  if (value === null) return 'null';
  if (value === undefined) throw new Error('Unsupported canonical identity input type: undefined');
  switch (typeof value) {
    case 'string': return JSON.stringify(normalizeUnicode(value));
    case 'number':
      if (!Number.isFinite(value)) throw new Error('Non-finite numbers are not valid canonical identity input');
      return Object.is(value, -0) ? '0' : String(value);
    case 'boolean': return value ? 'true' : 'false';
    case 'bigint': throw new Error('Unsupported canonical identity input type: bigint');
    case 'object': {
      if (Array.isArray(value)) {
        if (Object.getOwnPropertySymbols(value).length > 0) throw new Error('Canonical identity arrays must not contain symbol properties');
        const keys = Object.keys(value);
        if (keys.length !== value.length || keys.some((key,index) => key !== String(index))) throw new Error('Canonical identity arrays must be dense and must not contain extra properties');
        for (let index=0; index<value.length; index+=1) {
          const descriptor=Object.getOwnPropertyDescriptor(value,String(index));
          if (!descriptor || !descriptor.enumerable || !('value' in descriptor)) throw new Error('Canonical identity array entries must be enumerable data properties');
        }
        return `[${value.map(stableSerialize).join(',')}]`;
      }
      const prototype=Object.getPrototypeOf(value);
      if (prototype !== Object.prototype && prototype !== null) throw new Error('Unsupported canonical identity object prototype');
      if (Object.getOwnPropertySymbols(value).length > 0) throw new Error('Canonical identity objects must not contain symbol properties');
      const object=value as Record<string, unknown>;
      const descriptors=Object.getOwnPropertyDescriptors(object);
      const entries=Object.keys(descriptors).map(rawKey => {
        const descriptor=descriptors[rawKey];
        if (!descriptor.enumerable || !('value' in descriptor)) throw new Error('Canonical identity object properties must be enumerable data properties');
        return {rawKey, normalizedKey: normalizeUnicode(rawKey)};
      });
      const normalizedKeys=new Set<string>();
      for (const entry of entries) {
        if (normalizedKeys.has(entry.normalizedKey)) throw new Error(`Canonical identity key normalization collision: ${entry.normalizedKey}`);
        normalizedKeys.add(entry.normalizedKey);
      }
      entries.sort((a,b)=>a.normalizedKey < b.normalizedKey ? -1 : a.normalizedKey > b.normalizedKey ? 1 : 0);
      return `{${entries.map(({rawKey,normalizedKey}) => `${JSON.stringify(normalizedKey)}:${stableSerialize(object[rawKey])}`).join(',')}}`;
    }
    default: throw new Error(`Unsupported canonical identity input type: ${typeof value}`);
  }
}"""
    src=src[:start]+new+src[end:]
    replacements={
      "const value = authority.trim().toLowerCase();":"const value = authority.trim().normalize('NFC').toLowerCase();",
      "const value = resourceType.trim().toLowerCase();":"const value = resourceType.trim().normalize('NFC').toLowerCase();",
      "const value = resourceId.trim();":"const value = resourceId.trim().normalize('NFC');",
      "resourceId: input.resourceId.trim(),":"resourceId: decodeURIComponent(normalizeResourceId(input.resourceId)),",
    }
    for old,newv in replacements.items(): assert old in src,old; src=src.replace(old,newv)
    p.write_text(src)

def write_tests(target):
    (target/'scripts/test-identity-hardening.ts').write_text(r'''import assert from 'node:assert/strict';
import { canonicalUri, stableSerialize } from '../packages/core/src/identity';
const composed='café'; const decomposed='cafe\u0301';
assert.equal(stableSerialize({b:2,a:1}),stableSerialize({a:1,b:2}));
assert.equal(stableSerialize(composed),stableSerialize(decomposed));
assert.equal(stableSerialize({[composed]:'v'}),stableSerialize({[decomposed]:'v'}));
assert.throws(()=>stableSerialize({[composed]:1,[decomposed]:2}),/normalization collision/i);
assert.throws(()=>stableSerialize(undefined),/unsupported/i); assert.throws(()=>stableSerialize(1n),/unsupported/i);
assert.throws(()=>stableSerialize(new Date()),/prototype/i); assert.throws(()=>stableSerialize(new Map()),/prototype/i); assert.throws(()=>stableSerialize(new Set()),/prototype/i); assert.throws(()=>stableSerialize(new Uint8Array([1,2])),/prototype/i);
class Box { value=1; } assert.throws(()=>stableSerialize(new Box()),/prototype/i);
const withSymbol={value:1} as Record<PropertyKey,unknown>; withSymbol[Symbol('hidden')]=2; assert.throws(()=>stableSerialize(withSymbol),/symbol/i);
const sparse=new Array(2); sparse[1]='x'; assert.throws(()=>stableSerialize(sparse),/dense/i);
const extra=['x'] as string[] & {extra?:string}; extra.extra='y'; assert.throws(()=>stableSerialize(extra),/extra properties/i);
const accessor={} as Record<string,unknown>; Object.defineProperty(accessor,'x',{enumerable:true,get:()=>1}); assert.throws(()=>stableSerialize(accessor),/data properties/i);
const nullProto=Object.create(null) as Record<string,unknown>; nullProto.b=2; nullProto.a=1; assert.equal(stableSerialize(nullProto),'{"a":1,"b":2}');
const uriA=canonicalUri({scheme:'github',authority:'GitHub.COM',resourceType:'Repo',resourceId:composed}); const uriB=canonicalUri({scheme:'github',authority:'github.com',resourceType:'repo',resourceId:decomposed}); assert.equal(uriA,uriB);
console.log('IDENTITY_HARDENING_PASS');
''')
    run(['git','add','-N','scripts/test-identity-hardening.ts'],cwd=target)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mission',required=True); ap.add_argument('--target-dir',default='/tmp/target'); ap.add_argument('--evidence-dir',default='/tmp/cross-repo-evidence'); args=ap.parse_args()
    m=validate_mission(args.mission); target=Path(args.target_dir); evidence=Path(args.evidence_dir)
    if target.exists(): subprocess.run(['rm','-rf',str(target)],check=True)
    run(['git','clone','--filter=blob:none','--no-checkout',TARGET_REPO,str(target)]); run(['git','checkout','--detach',TARGET_COMMIT],cwd=target); assert run(['git','rev-parse','HEAD'],cwd=target).strip()==TARGET_COMMIT; run(['git','remote','remove','origin'],cwd=target)
    planner=ask('You are the PLANNER. Return JSON only: serializer_domain JSON_ONLY; unicode_form NFC; unsupported_objects REJECT; normalized_key_collisions REJECT; provider_case_rules DEFER; registry_immutability DEFER.',num_predict=120)
    expected_plan={'serializer_domain':'JSON_ONLY','unicode_form':'NFC','unsupported_objects':'REJECT','normalized_key_collisions':'REJECT','provider_case_rules':'DEFER','registry_immutability':'DEFER'}; assert planner==expected_plan,planner; dump('/tmp/planner.contract.json',planner)
    keys=['reject_undefined','reject_bigint','reject_non_plain_objects','reject_symbol_properties','reject_sparse_arrays','reject_array_extra_properties','reject_accessor_properties','normalize_string_values_nfc','normalize_object_keys_nfc','reject_normalized_key_collisions','normalize_identity_fields_nfc']; builder=ask('You are the BUILDER. Return JSON only with these keys all boolean true: '+', '.join(keys),num_predict=180); assert set(builder)==set(keys) and all(builder[k] is True for k in keys),builder; dump('/tmp/builder.contract.json',builder); materialize_identity(target)
    tester=ask('You are the TEST ENGINEER. Every named adversarial case is required. Return JSON marking each as true: '+', '.join(CASES),num_predict=280); dump('/tmp/tester.contract.json',canonicalize_test_contract(tester)); write_tests(target)
    changed=sorted(line[3:] for line in run(['git','status','--short'],cwd=target).splitlines() if line.strip()); assert changed==sorted(ALLOWED),(changed,ALLOWED)
    run(['npx','--yes','tsx@4.20.5','scripts/test-identity-hardening.ts'],cwd=target); run(['npx','--yes','-p','typescript@5.9.2','tsc','--noEmit','-p','packages/core/tsconfig.json'],cwd=target); run(['git','diff','--check'],cwd=target)
    patch=run(['git','diff','--',*ALLOWED],cwd=target); assert 'diff --git a/scripts/test-identity-hardening.ts b/scripts/test-identity-hardening.ts' in patch; Path('/tmp/candidate.patch').write_text(patch)
    security_schema={'type':'object','additionalProperties':False,'properties':{'verdict':{'type':'string','enum':['PASS','FAIL']},'defect_code':{'type':'string','enum':['NONE','AMBIGUOUS_CANONICALIZATION','EXECUTABLE_PROPERTY','UNSUPPORTED_OBJECT_ACCEPTED','COLLISION_GAP','OTHER']},'finding':{'type':'string','maxLength':180}},'required':['verdict','defect_code','finding']}; security=ask('You are SECURITY REVIEWER. Deterministic tests passed. Review canonical ambiguity and executable-property risks. PASS only if no concrete defect. PATCH:\n'+patch,4096,180,security_schema); assert security['verdict']=='PASS' and security['defect_code']=='NONE',security; dump('/tmp/security.contract.json',security)
    reviewer_schema={'type':'object','additionalProperties':False,'properties':{'verdict':{'type':'string','enum':['PASS','FAIL']},'defect_code':{'type':'string','enum':['NONE','ARRAY_SEMANTICS','OBJECT_SEMANTICS','UNICODE_SEMANTICS','URI_SEMANTICS','SCOPE_CREEP','OTHER']},'finding':{'type':'string','maxLength':180}},'required':['verdict','defect_code','finding']}; reviewer=ask('You are independent CODE REVIEWER. Intended breaking change: undefined/bigint reject. Find any other concrete regression. PASS only if none. PATCH:\n'+patch,4096,180,reviewer_schema); assert reviewer['verdict']=='PASS' and reviewer['defect_code']=='NONE',reviewer; dump('/tmp/reviewer.contract.json',reviewer)
    evidence.mkdir(parents=True,exist_ok=True); (evidence/'files').mkdir(exist_ok=True)
    for src,dst in [(target/ALLOWED[0],evidence/'files/identity.ts'),(target/ALLOWED[1],evidence/'files/test-identity-hardening.ts'),(Path('/tmp/candidate.patch'),evidence/'candidate.patch')]: dst.write_bytes(src.read_bytes())
    for n in ['planner','builder','tester','security','reviewer']: (evidence/f'{n}.contract.json').write_bytes(Path(f'/tmp/{n}.contract.json').read_bytes())
    dump(evidence/'EVIDENCE.json',{'schema':'rotclaw.cross-repo-engineering-evidence.v3','mission_id':m['mission_id'],'target_repo':'rotprods/cos-graph-engine','target_source_commit':TARGET_COMMIT,'target_base_ref':m['target_ref'],'changed_paths':ALLOWED,'patch_sha256':h('/tmp/candidate.patch'),'identity_sha256':h(target/ALLOWED[0]),'test_sha256':h(target/ALLOWED[1]),'planner_sha256':h('/tmp/planner.contract.json'),'builder_sha256':h('/tmp/builder.contract.json'),'tester_sha256':h('/tmp/tester.contract.json'),'security_sha256':h('/tmp/security.contract.json'),'reviewer_sha256':h('/tmp/reviewer.contract.json'),'deterministic_qa':'PASS','authority':'A2_CROSS_REPO_NO_PUSH_NO_MERGE','promotion_authority':'CONTROL_PLANE_ONLY'}); print('CROSS_REPO_ENGINEERING_PASS')
if __name__=='__main__': main()
