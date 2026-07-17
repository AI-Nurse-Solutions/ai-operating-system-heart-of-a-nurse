#!/usr/bin/env python3
"""Compile THRIVE schemas and prove agent/delta conditions fail closed."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'wellness-services-marketing-managers/packages/thrive/Wellness-Services-Marketer-and-Manager-THRIVE-SuperPowers-Pack-v1.0/workflows/03-THRIVE-Schemas-and-Agents.md'
PATTERN=re.compile(r'^### `https://nurse-ai-os\.local/schemas/wellness_thrive/([^/]+)/1\.0\.0`\n\n\*\*Canonical SHA-256:\*\* `([0-9a-f]{64})`\n\n```json\n([^\n]+)\n```',re.M)
def rejects(v:Draft202012Validator,x:Any)->bool:return bool(list(v.iter_errors(x)))
def accepts(v:Draft202012Validator,x:Any,label:str)->None:
 e=list(v.iter_errors(x))
 if e:raise SystemExit(f'{label}: baseline rejected: {e[0].message}')

def main()->None:
 blocks=PATTERN.findall(SOURCE.read_text(encoding='utf-8'))
 if len(blocks)!=18:raise SystemExit(f'Expected 18 schemas, found {len(blocks)}')
 docs={}
 for name,digest,payload in blocks:
  if hashlib.sha256(payload.encode()).hexdigest()!=digest:raise SystemExit(f'{name}: canonical hash mismatch')
  doc=json.loads(payload);Draft202012Validator.check_schema(doc)
  if doc.get('additionalProperties') is not False or doc.get('unevaluatedProperties') is not False:raise SystemExit(f'{name}: root is not closed')
  docs[name]=doc
 agent=docs['agent_charter_trace'];fields=('permission','agent_state','one_run_authorization','tools','destinations','kill_status','record_state','approval')
 fragment={'$schema':agent['$schema'],'$defs':agent['$defs'],'type':'object','properties':{k:agent['properties'][k] for k in fields},'required':list(fields),'allOf':agent['allOf'],'additionalProperties':False}
 av=Draft202012Validator(fragment)
 p0={'permission':'PERM-P0','agent_state':'disabled','one_run_authorization':None,'tools':[],'destinations':[],'kill_status':'not_applicable','record_state':'draft','approval':None}
 p1={'permission':'PERM-P1','agent_state':'synthetic_preview','one_run_authorization':None,'tools':[],'destinations':[],'kill_status':'not_applicable','record_state':'under_review','approval':None}
 accepts(av,p0,'P0 disabled');accepts(av,p1,'P1 synthetic preview')
 negatives=[dict(p0,agent_state='synthetic_preview'),dict(p0,agent_state='one_run_approved'),dict(p1,agent_state='disabled'),dict(p1,destinations=[{'id':'dest','version':'1.0.0','partition_id':'wellness_thrive.tenant.demo','target_kind':'destination','target_sha256':'0'*64}]),dict(p1,record_state='approved_by_human')]
 if any(not rejects(av,x) for x in negatives):raise SystemExit('Agent permission/state negative case was accepted')
 receipt=docs['control_audit_receipt'];delta_fields=('expected_result','expected_action_delta','expected_data_delta','observed_result','observed_action_delta','observed_data_delta','action')
 relevant=[]
 for b in receipt['allOf']:
  then=set(b.get('then',{}).get('properties',{}))
  if then & {'expected_action_delta','expected_data_delta','observed_action_delta','observed_data_delta'}:relevant.append(b)
 rf={'$schema':receipt['$schema'],'$defs':receipt['$defs'],'type':'object','properties':{k:receipt['properties'][k] for k in delta_fields},'required':list(delta_fields),'allOf':relevant,'additionalProperties':False}
 rv=Draft202012Validator(rf)
 zero_action={'network_calls':0,'external_messages':0,'spend_amount':{'amount':'0','currency':'USD'},'official_writes':0}
 zero_data={'created_records':0,'changed_records':0,'deleted_records':0,'disclosed_fields':0,'residual_record_refs':[]}
 base={'expected_result':'blocked','expected_action_delta':zero_action,'expected_data_delta':zero_data,'observed_result':'blocked','observed_action_delta':zero_action,'observed_data_delta':zero_data,'action':'block'}
 accepts(rv,base,'blocked zero receipt')
 negative=[]
 for field,key in [('observed_action_delta','network_calls'),('observed_data_delta','created_records'),('expected_action_delta','official_writes'),('expected_data_delta','disclosed_fields')]:
  x=json.loads(json.dumps(base));x[field][key]=1;negative.append(x)
 x=json.loads(json.dumps(base));x['observed_action_delta']['spend_amount']['amount']='1.00';negative.append(x)
 if any(not rejects(rv,x) for x in negative):raise SystemExit('Blocked/unsupported/rejected receipt accepted nonzero delta')
 passed=json.loads(json.dumps(base));passed.update({'expected_result':'passed','observed_result':'passed','action':'preview'});passed['expected_action_delta']['network_calls']=1;passed['observed_action_delta']['network_calls']=1
 accepts(rv,passed,'nonzero passed preview receipt')
 print('THRIVE_SCHEMA_COMPILE=passed draft=2020-12 schemas=18 closed=18')
 print('THRIVE_AGENT_STATE=fail_closed valid_p0_p1=2 negative_cases=5')
 print('THRIVE_DELTA_CONSISTENCY=fail_closed negative_cases=5 passed_nonzero_control=1')
if __name__=='__main__':main()
