"""Bounded mission-language interpreter, not Python execution. No eval/exec/imports."""
import ast
import time

class MissionError(Exception):pass
class Machine:
 def __init__(self,game,level):
  self.game=game;self.level=level;self.env={};self.functions={};self.pos=[0,0];self.values=list(level.get('values',[]));self.output=[];self.trace=[{'position':self.pos.copy(),'values':self.values.copy()}];self.ticks=0;self.moves=0;self.comparisons=0;self.depth=0;self.algorithm=''
 def tick(self):
  self.ticks+=1
  if self.ticks>1000:raise MissionError('Mission instruction limit exceeded (1000).')
 def record(self):
  if len(self.trace)>256:raise MissionError('Animation step limit exceeded.')
  self.trace.append({'position':self.pos.copy(),'values':self.values.copy(),'output':self.output.copy()})
 def expression(self,n):
  self.tick()
  if isinstance(n,ast.Constant) and type(n.value) in (int,str,bool):
   if isinstance(n.value,str) and len(n.value)>30:raise MissionError('String is too long.')
   if type(n.value)==int and abs(n.value)>100000:raise MissionError('Number exceeds mission range.')
   return n.value
  if isinstance(n,ast.Name) and n.id in self.env:return self.env[n.id]
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):return not self.expression(n.operand)
  if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mod)):
   a,b=self.expression(n.left),self.expression(n.right)
   if type(a)!=int or type(b)!=int:raise MissionError('Arithmetic requires integers.')
   v=a+b if isinstance(n.op,ast.Add) else a-b if isinstance(n.op,ast.Sub) else a%b
   if abs(v)>100000:raise MissionError('Number exceeds mission range.')
   return v
  if isinstance(n,ast.Compare) and len(n.ops)==1:
   a,b=self.expression(n.left),self.expression(n.comparators[0]);op=n.ops[0]
   if isinstance(op,ast.Eq):return a==b
   if isinstance(op,ast.Lt):return a<b
   if isinstance(op,ast.Gt):return a>b
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
   args=[self.expression(a) for a in n.args];name=n.func.id
   if name=='canMove' and len(args)==1:return self.canmove(args[0])
   if name=='range' and 1<=len(args)<=2 and all(type(a)==int for a in args):
    r=range(*args)
    if len(r)>32:raise MissionError('Loops allow at most 32 iterations.')
    return list(r)
  raise MissionError('Unsupported expression. Use only the documented mission commands.')
 def canmove(self,direction):
  delta={'right':(1,0),'left':(-1,0),'up':(0,-1),'down':(0,1)}.get(direction)
  if not delta:raise MissionError('Direction must be right, left, up or down.')
  p=[self.pos[0]+delta[0],self.pos[1]+delta[1]]
  return all(0<=v<self.level.get('grid',0) for v in p) and p not in self.level.get('walls',[])
 def call(self,n):
  if not isinstance(n.func,ast.Name) or n.keywords:raise MissionError('Only named mission commands are allowed.')
  name=n.func.id;args=[self.expression(a) for a in n.args]
  if name in self.functions and not args:
   if self.depth>=8:raise MissionError('Function nesting limit exceeded.')
   self.depth+=1;self.block(self.functions[name]);self.depth-=1;return
  directions={'moveRight':'right','moveLeft':'left','moveUp':'up','moveDown':'down'}
  if self.game in ['robot','maze'] and name in directions and not args:
   d=directions[name]
   if not self.canmove(d):raise MissionError('Robot hit an obstacle or the grid boundary.')
   dx,dy={'right':(1,0),'left':(-1,0),'up':(0,-1),'down':(0,1)}[d]
   self.pos=[self.pos[0]+dx,self.pos[1]+dy];self.moves+=1;self.record();return
  if self.game=='bug' and name=='print' and len(args)==1 and type(args[0])==int:
   if len(self.output)>64:raise MissionError('Output limit exceeded.')
   self.output.append(args[0]);self.record();return
  if self.game=='defender':
   if name=='removeDivisible' and len(args)==1 and type(args[0])==int and args[0]>0:self.values=[v for v in self.values if v%args[0]]
   elif name=='removeBelow' and len(args)==1 and type(args[0])==int:self.values=[v for v in self.values if v>=args[0]]
   elif name=='reverse' and not args:self.values.reverse()
   else:raise MissionError('Use removeDivisible(n), removeBelow(n), or reverse().')
   self.record();return
  if self.game=='race' and name in ['bubbleSort','insertionSort'] and not args:
   self.algorithm=name
   for i in range(len(self.values)):
    positions=range(len(self.values)-i-1) if name=='bubbleSort' else range(i-1,-1,-1)
    for j in positions:
     self.comparisons+=1
     if self.values[j]>self.values[j+1]:self.values[j],self.values[j+1]=self.values[j+1],self.values[j];self.record()
     elif name=='insertionSort':break
   return
  raise MissionError('Unknown command for this mission: '+name)
 def block(self,nodes):
  for n in nodes:
   self.tick()
   if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call):self.call(n.value)
   elif isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):self.env[n.targets[0].id]=self.expression(n.value)
   elif isinstance(n,ast.For) and isinstance(n.target,ast.Name) and not n.orelse:
    values=self.expression(n.iter)
    if not isinstance(values,list):raise MissionError('Use range() for loops.')
    for value in values:self.env[n.target.id]=value;self.block(n.body)
   elif isinstance(n,ast.If):self.block(n.body if self.expression(n.test) else n.orelse)
   elif isinstance(n,ast.FunctionDef) and not (n.args.args or n.args.vararg or n.args.kwarg or n.args.kwonlyargs or n.args.posonlyargs or n.decorator_list or n.returns):self.functions[n.name]=n.body
   elif isinstance(n,ast.Pass):pass
   else:raise MissionError('Allowed syntax: commands, assignments, for/range, if/else, and functions without arguments.')

def evaluate(game,level,code):
 start=time.perf_counter();m=Machine(game,level)
 try:
  tree=ast.parse(code)
  if len(list(ast.walk(tree)))>400:raise MissionError('Mission program is too large.')
  m.block(tree.body)
  if game in ['robot','maze']:
   accepted=m.pos==level['goal'] and m.moves<=level.get('maxMoves',128)
   if level.get('requires'):accepted=accepted and any(type(n).__name__==level['requires'] for n in ast.walk(tree))
  elif game=='bug':accepted=m.output==level['expected']
  elif game=='race':accepted=m.values==sorted(level['values']) and bool(m.algorithm) and (not level.get('requiresAlgorithm') or m.algorithm==level['requiresAlgorithm'])
  else:accepted=m.values==level['expected']
  status='Accepted' if accepted else 'Wrong Answer';message='Mission complete.' if accepted else 'Objective not yet met. Check the mission instructions and trace.'
 except (SyntaxError,MissionError,ZeroDivisionError,TypeError,ValueError,RecursionError) as e:
  accepted=False;status='Compilation Error' if isinstance(e,SyntaxError) else 'Runtime Error';message=str(e)[:300]
 return dict(status=status,accepted=accepted,trace=m.trace,output=m.output,steps=m.moves or m.comparisons or m.ticks,executionTime=round((time.perf_counter()-start)*1000,3),memory=None,message=message,efficiencyBonus=20 if accepted and level.get('efficiency') and m.moves<=level['efficiency'] else 0)
