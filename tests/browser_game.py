"""Chromium integration: actual controls, full mission, guided learning, equipment, escapes and saves."""
import os, shutil, threading
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def run():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None)
   context=browser.new_context(viewport={'width':1440,'height':1100})
   # Drive the real fixed-step simulator deterministically; controls still go through browser events.
   context.add_init_script('window.requestAnimationFrame = () => 0')
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(f'http://127.0.0.1:{server.server_port}')
   def tick(n=1):page.evaluate('(n)=>{for(let i=0;i<n;i++){clock+=1/60;update(1/60);}render(clock)}',n)
   def key(k,n=1):
    page.keyboard.down(k);tick(n);page.keyboard.up(k)
   def move(x):
    cur=page.evaluate('game.player.x');k='ArrowRight' if x>cur else 'ArrowLeft'
    page.keyboard.down('x');page.keyboard.down(k)
    page.evaluate('''({x,dir})=>{for(let i=0;i<500;i++){if((game.player.x-x)*dir>=0)break;clock+=1/60;update(1/60);if(state!=='playing')throw Error('Movement interrupted: '+state)}render(clock)}''',{'x':x,'dir':1 if x>cur else -1})
    page.keyboard.up(k);page.keyboard.up('x');assert abs(page.evaluate('game.player.x')-x)<5
   def ride(f):
    y=156+f*126;k='ArrowDown' if y>page.evaluate('game.player.y') else 'ArrowUp'
    page.keyboard.down(k)
    page.evaluate('''(y)=>{for(let i=0;i<1300;i++){clock+=1/60;update(1/60);if(Math.abs(game.player.y-y)<2)break;if(state!=='playing')throw Error('Lift interrupted: '+state)}render(clock)}''',y)
    page.keyboard.up(k);assert abs(page.evaluate('game.player.y')-y)<3
   def finish():
    while page.locator('#guideForm').is_visible():
     ans=page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer')
     page.locator('#guideAnswer').fill(ans);page.locator('#guideAnswer').press('Enter')
    assert page.locator('#challengeContinue').is_visible();page.click('#challengeContinue');tick()
   # Structural checks across every mission, without editing any content.
   data=page.evaluate('''()=>MathEngine.campaign.map(s=>{newGame(s.level);return {n:s.level,f:game.floors,locks:game.files.every(f=>f.challenge?.source),stairs:game.stairs.every(s=>!isGap(s.x)&&!isGap(s.endX)),items:game.files.every(f=>!isGap(f.x)&&f.floor<game.floors),theme:game.theme,escape:game.escapeKind}})''')
   assert len(data)==60 and all(v['locks'] and v['stairs'] and v['items'] for v in data)
   assert data[23]['f']==24 and len(set(v['escape'] for v in data))==5
   page.evaluate('toLobby()');page.click('#startBtn');tick();move(290);key('e')
   assert page.evaluate("state==='challenge'")
   before=page.evaluate('[game.time,game.lives]');tick(300);assert page.evaluate('[game.time,game.lives]')==before
   wrong=page.evaluate('(challengeDoor.challenge.correct+1)%challengeDoor.challenge.answers.length');page.locator('.answer').nth(wrong).click()
   assert page.evaluate('game.lives')==3 and page.locator('#challengeContinue').is_hidden()
   page.click('#solutionBtn');assert page.locator('#answers').is_hidden()
   page.locator('#guideAnswer').fill('999999');page.locator('#guideAnswer').press('Enter');assert page.evaluate('studyFor(challengeDoor).guideAnswers.length')==0
   assert page.locator('#challengeFeedback').inner_text()==''
   for _ in range(2):
    answer=page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer');page.locator('#guideAnswer').fill(answer);page.locator('#guideAnswer').press('Enter')
   page.reload();page.click('#startBtn');move(290);key('e');assert page.evaluate('studyFor(challengeDoor).guideAnswers.length')==2
   finish();assert page.evaluate('game.files[0].collected')
   print('PASS: maths from first level, action freeze, harmless retries, checked steps, saved working and gated collection',flush=True)
   # Full level with stairs, grapple, lifts and every case reached using keyboard movement.
   move(110);key('ArrowDown');tick(70);assert page.evaluate('floorAt(game.player.y)')==1
   key('v');key('v');key('g');tick(45);assert page.evaluate('floorAt(game.player.y)')==0
   move(392);ride(2);move(180);key('e');page.click('#solutionBtn');finish()
   move(392);ride(6);move(600);key('e');page.locator('.answer').nth(page.evaluate('challengeDoor.challenge.correct')).click();page.click('#challengeContinue')
   move(490);key('ArrowDown');tick(200);move(392);ride(7);move(250)
   assert page.evaluate('game.escape?.kind')=='motorcycle'
   key('ArrowUp');key('x',30);key('ArrowRight',30);assert page.evaluate('game.escape.x')>.6
   key('p');before=page.evaluate('game.escape.distance');tick(120);assert page.evaluate('game.escape.distance')==before;page.click('#resumeBtn')
   # Survive by steering toward a clear edge, shooting and using continuations if required.
   for _ in range(100):
    if page.evaluate('state')=='won':break
    if page.evaluate('Boolean(driveTask())'):
     correct=page.evaluate('driveTask().challenge.correct')
     page.locator('.drive-lane').nth(correct).click();page.click('#driveCommit')
    if page.evaluate('state')=='lost':page.click('#nextBtn');key('ArrowUp')
    e=page.evaluate('({x:game.escape.x,obs:game.escape.obstacles})');near=[o for o in e['obs'] if .35<o['y']<.85 and o['kind']!='beacon']
    if near:
     target=.15 if near[0]['x']>.5 else .85
     if abs(e['x']-target)>.07:key('ArrowLeft' if target<e['x'] else 'ArrowRight',15)
    key('x',30)
   assert page.evaluate('state')=='won';assert page.evaluate('practice.completed.includes(1)')
   page.click('#nextBtn');assert page.evaluate('game.mission')==2
   print('PASS: complete mission through real controls, stairs, grapple, lifts, all maths locks, vehicle escape and next operation',flush=True)
   # Focused combat fixtures isolate collision mechanics; no production cheats are exposed.
   for weapon,count in [(0,1),(1,3),(2,1)]:
    page.evaluate('(w)=>{startGame(8);game.weapon=w;game.guards=[]}',weapon);key('x');assert page.evaluate('game.bullets.length')==count
   page.evaluate("startGame(8); game.guards=[{x:280,y:156,stun:0,armor:1,armorCooldown:0,dir:-1,left:90,right:330,cooldown:3,speed:0,id:100}]")
   key('c');assert page.evaluate('game.guards[0].stun')>0
   page.evaluate("startGame(8);game.player.x=680;game.player.y=floorY(3);game.player.fallStart=game.player.y;game.player.checkpoint={x:680,floor:3};game.gadget=1;game.guards=[{x:700,y:floorY(3),stun:0,armor:1,armorCooldown:0,dir:-1,left:470,right:721,cooldown:3,speed:0,id:100}]")
   key('g');assert page.evaluate('game.guards[0].stun')>0;assert page.evaluate('game.energy')<46
   page.evaluate('startGame(8);game.gadget=0');key('g');assert page.evaluate('game.cloak')>5
   page.evaluate('startGame(8);game.weapon=2;game.player.x=180;game.player.y=floorY(3);game.player.fallStart=game.player.y;game.player.facing=1;game.guards=[]');key('x',25);assert page.evaluate('game.barrels[0].burst')
   print('PASS: three projectile patterns, armored guard melee, EMP, cloak, destructible EMP barrel and recharge',flush=True)
   # Check every escape can complete, save and resume, including the parachute.
   for level in [1,2,5,8,10]:
    page.evaluate('(level)=>{startGame(level);game.files.forEach(f=>{f.collected=true;studyFor(f).solved=true});beginEscape();game.escape.distance=500;saveCheckpoint()}',level)
    kind=page.evaluate('game.escape.kind');page.reload();page.click('#startBtn');assert page.evaluate('game.escape.kind')==kind;assert page.evaluate('game.escape.distance')==500
    key('ArrowUp');page.evaluate('game.escape.drive.completed=2;game.escape.distance=game.escape.target-2');tick(4);assert page.evaluate('state')=='won'
   print('PASS: all five escape types, escape checkpoint persistence and completion',flush=True)
   # Every authored guide can be completed through the same real form.
   for temp in page.evaluate('MathEngine.templates'):
    for tier in [1,2,3]:
     page.evaluate('''({id,tier})=>{startGame(1);const f=game.files[0];f.challenge=MathEngine.make(id,tier,'form');f.lock=f.challenge.topic+':'+tier;f.study=freshStudy();openChallenge(f)}''',{'id':temp['id'],'tier':tier})
     page.click('#solutionBtn');finish()
   assert not errors,errors
   print('PASS: all 186 template/tier guided forms; no browser errors',flush=True)
   browser.close()
 finally:server.shutdown()
if __name__=='__main__':run()
