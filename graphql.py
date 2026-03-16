import re,json
def parse_query(query):
    query=query.strip()
    m=re.match(r'(query|mutation)?\s*\{(.+)\}',query,re.DOTALL)
    if not m: raise ValueError("Invalid query")
    op=m.group(1) or 'query'
    body=m.group(2).strip()
    return {'operation':op,'selections':parse_selections(body)}
def parse_selections(body):
    selections=[]; i=0; current=''
    depth=0
    for c in body:
        if c=='{': depth+=1; current+=c
        elif c=='}': depth-=1; current+=c
        elif c in '\n,' and depth==0:
            if current.strip(): selections.append(parse_field(current.strip()))
            current=''
        else: current+=c
    if current.strip(): selections.append(parse_field(current.strip()))
    return selections
def parse_field(field):
    m=re.match(r'(\w+)(?:\((.+?)\))?\s*(?:\{(.+)\})?',field,re.DOTALL)
    if not m: return {'name':field}
    result={'name':m.group(1)}
    if m.group(2):
        args={}
        for pair in m.group(2).split(','):
            k,v=pair.split(':',1); args[k.strip()]=v.strip().strip('"')
        result['args']=args
    if m.group(3): result['selections']=parse_selections(m.group(3))
    return result
def execute(query,resolvers,context=None):
    parsed=parse_query(query)
    result={}
    for sel in parsed['selections']:
        name=sel['name']
        if name in resolvers:
            val=resolvers[name](sel.get('args',{}),context)
            if 'selections' in sel and isinstance(val,dict):
                val={s['name']:val.get(s['name']) for s in sel['selections'] if s['name'] in val}
            result[name]=val
    return {'data':result}
if __name__=="__main__":
    users={1:{'id':1,'name':'Alice','email':'alice@test.com'},2:{'id':2,'name':'Bob','email':'bob@test.com'}}
    resolvers={'user':lambda args,ctx: users.get(int(args.get('id',1))),'users':lambda args,ctx: list(users.values())}
    result=execute('{ user(id: 1) { name, email } }',resolvers)
    assert result['data']['user']=={'name':'Alice','email':'alice@test.com'}
    result2=execute('{ users }',resolvers)
    assert len(result2['data']['users'])==2
    print(f"GraphQL: {json.dumps(result)}")
    print("All tests passed!")
