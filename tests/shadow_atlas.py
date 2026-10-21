"""Shadow Atlas integration: objective gates, acquired arsenal, bosses, hazards and saves."""
import os, shutil, threading
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def run():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None)
   ctx=browser.new_context(viewport={'width':1440,'height':1100});ctx.add_init_script('window.requestAnimationFrame=()=>0')
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}')
   def tick(n=1):page.evaluate('(n)=>{for(let i=0;i<n;i++){clock+=1/60;update(1/60)}render(clock)}',n)
   def key(k,n=1):page.keyboard.down(k);tick(n);page.keyboard.up(k)
   def place(x,f):
    page.evaluate('''({x,f})=>{Object.assign(game.player,{x,y:floorY(f),vx:0,vy:0,fallStart:floorY(f),checkpoint:{x,floor:f},grounded:true,lift:null,traversal:null});camera=clamp(floorY(f)-240,0,floorY(game.floors-1)-H+76);render(clock)}''',{'x':x,'f':f})
   def finish(guide=False):
    if guide:
     page.click('#solutionBtn')
     while page.locator('#guideForm').is_visible():
      answer=page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer')
      page.locator('#guideAnswer').fill(answer);page.locator('#guideAnswer').press('Enter')
    else:page.locator('.answer').nth(page.evaluate('challengeDoor.challenge.correct')).click()
    page.click('#challengeContinue');tick()
   # Every mission's authentic maths gates, prerequisites, override and villain gate.
   for level in range(25,37):
    page.evaluate('(n)=>startGame(n)',level);tick()
    assert page.evaluate('game.files.length===5 && game.items.filter(i=>i.kind==="weapon").length===4')
    assert page.evaluate('game.items.every(i=>!isGap(i.x) && i.floor<game.floors)')
    assert page.evaluate('game.files.every((f,i)=>f.requires.every(r=>r<i))')
    assert page.evaluate('caseReady(game.files[0]) && !caseReady(game.files[1]) && !caseReady(game.files[4])')
    page.evaluate('beginEscape()');assert page.evaluate('game.escape===null')
    # Shield must also resist armor-piercing and EMP attacks before the override.
    hp=page.evaluate('game.boss.hp');page.evaluate('stunGuard(game.boss,true,3)');assert page.evaluate('game.boss.hp')==hp
    for i in range(4):
     d=page.evaluate('(i)=>({x:game.files[i].x,f:game.files[i].floor})',i);place(**d);key('e')
     assert page.evaluate('state')=='challenge',(level,i)
     before=page.evaluate('[game.time,game.boss.phaseTime,game.boss.hp]');tick(300);assert page.evaluate('[game.time,game.boss.phaseTime,game.boss.hp]')==before
     finish(guide=(i==0 and level in [25,31,36]))
     assert page.evaluate('(i)=>game.files[i].collected',i)
     if i==2:assert page.evaluate('game.hazards.every(h=>hazardState(h)==="off")')
    assert not page.evaluate('caseReady(game.files[4])')
    # Real fire inputs; the fixture positions the player in the arena to isolate combat.
    floor=page.evaluate('game.boss.floor');place(495,floor)
    page.evaluate('game.player.facing=1;game.weapon=0;game.ownedWeapons=[0];game.player.invulnerable=100;game.guards=game.guards.filter(g=>g.isBoss)')
    key('x',900);assert page.evaluate('game.boss.defeated'),level
    score=page.evaluate('game.score');page.evaluate('stunGuard(game.boss,true,3)');assert page.evaluate('game.score')==score
    place(600,floor);key('e');assert page.evaluate('state')=='challenge';finish()
    place(230,page.evaluate('game.floors-1'));tick();assert page.evaluate('game.escape!==null')
    key('ArrowUp');page.evaluate('game.escape.drive.completed=2;game.escape.distance=game.escape.target-2');tick(4);assert page.evaluate('state')=='won'
   print('PASS: all 12 operations, 60 actual maths forms, prerequisite chains, override shields, villain combat and extraction',flush=True)
   # Unarmed fire is a takedown; inventory is acquired and survives a reload.
   page.evaluate('startGame(27)');tick();assert page.evaluate('game.ownedWeapons.length')==0
   key('q');key('x');assert page.evaluate('game.bullets.length===0 && game.melee>0')
   for w in [1,3,4,2]:
    item=page.evaluate('(w)=>{const i=game.items.find(i=>i.weapon===w);return {x:i.x,f:i.floor}}',w);place(**item);tick()
    assert page.evaluate('(w)=>game.ownedWeapons.includes(w)&&game.weapon===w',w)
   owned=page.evaluate('game.ownedWeapons');page.evaluate('saveCheckpoint()');page.reload();page.click('#startBtn');tick()
   assert page.evaluate('game.ownedWeapons')==owned
   seen=set()
   for _ in owned:seen.add(page.evaluate('game.weapon'));key('q')
   assert seen==set(owned) and 0 not in seen
   # Rail penetrates multiple armored enemies in a single shot and costs energy.
   place(480,4);page.evaluate('''game.weapon=3;game.barrels=[];game.player.facing=1;game.player.fireCooldown=0;game.energy=100;game.guards=[570,650].map((x,id)=>({x,y:floorY(4),floor:4,id,kind:'armored',armor:1,stun:0,armorCooldown:0,dir:-1,left:470,right:720,cooldown:100,speed:0}))''')
   key('x');assert 91<page.evaluate('game.energy')<93;tick(22);assert page.evaluate('game.guards.every(g=>g.stun>0)')
   # Disc rebounds; exhausted energy doesn't create a shot.
   place(1040,4);page.evaluate('game.guards=[];game.bullets=[];game.weapon=4;game.player.fireCooldown=0;game.player.facing=1');key('x');tick(12)
   assert page.evaluate('game.bullets.some(b=>b.disc&&b.returned&&b.vx<0)')
   page.evaluate('game.bullets=[];game.energy=0;game.player.fireCooldown=0');key('x');assert page.evaluate('game.bullets.length')==0
   print('PASS: unarmed takedown, four acquired caches, inventory reload, owned-only cycling, rail piercing, ricochet and energy limits',flush=True)
   # Three visible boss phases/attacks and bounded engineer reinforcements.
   for level,style in [(25,'ranger'),(27,'duelist'),(30,'engineer')]:
    page.evaluate('(n)=>startGame(n)',level);place(510,page.evaluate('game.boss.floor'))
    page.evaluate('game.guards=[game.boss];game.player.invulnerable=100')
    tick(76);assert page.evaluate('game.boss.phase')=='aim';oldx=page.evaluate('game.boss.x')
    tick(58 if style=='duelist' else 77);assert page.evaluate('game.boss.phase')=='attack'
    if style=='duelist':assert page.evaluate('game.boss.x')<oldx
    else:assert page.evaluate('game.bullets.filter(b=>b.owner==="guard").length')==3
    tick(36);assert page.evaluate('game.boss.phase')=='recover'
    if style=='engineer':
     tick(1600);assert page.evaluate('game.guards.filter(g=>g.summoned).length')==2
     page.evaluate('game.guards.filter(g=>g.summoned).forEach(g=>stunGuard(g,true))');tick(300)
     assert page.evaluate('game.guards.filter(g=>g.summoned).length')<=2
   # Brawler warning gives time to evade; no projectile attack.
   page.evaluate('startGame(27)');place(560,1)
   page.evaluate('''game.guards=[{id:700,x:610,y:floorY(1),kind:'brawler',left:470,right:720,speed:80,dir:-1,stun:0,armor:0,armorCooldown:0,cooldown:0,windup:0,attack:0}];game.player.invulnerable=0''')
   tick();assert page.evaluate('game.guards[0].windup>0 && game.lives===3');tick(48);assert page.evaluate('game.lives')==2;assert page.evaluate('game.bullets.length')==0
   print('PASS: telegraphed ranged/charging/summoning villains, recovery windows, bounded reinforcements and unarmed attackers',flush=True)
   # Hazard schedule, jump clearance, damage and override; ice has braking distance.
   page.evaluate('startGame(25);game.guards=[]');h=page.evaluate('({x:game.hazards[0].x,f:game.hazards[0].floor})');place(**h)
   page.evaluate('game.time=3.2-game.hazards[0].offset;game.player.invulnerable=0');tick();assert page.evaluate('hazardState(game.hazards[0])==="warning" && game.lives===3')
   page.evaluate('game.time=3.6-game.hazards[0].offset');key('Space');tick(8);assert page.evaluate('game.lives')==3
   place(**h);page.evaluate('game.time=3.8-game.hazards[0].offset;game.player.invulnerable=0');tick();assert page.evaluate('game.lives')==2
   page.evaluate('game.files[2].collected=true;game.player.invulnerable=0');tick(100);assert page.evaluate('game.lives===2 && hazardState(game.hazards[0])==="off"')
   place(470,0);key('ArrowRight',15);x=page.evaluate('game.player.x');tick(15);assert page.evaluate('game.player.x')>x+10
   # Boss damage, cache ownership and a partially completed guide persist together.
   page.evaluate('startGame(36);game.files.slice(0,4).forEach(f=>{f.collected=true;studyFor(f).solved=true});game.items.filter(i=>i.kind==="weapon").forEach(i=>i.collected=true);game.ownedWeapons=[0,1,3,4,2];game.weapon=3;hitBoss(game.boss,3)')
   hp=page.evaluate('game.boss.hp');page.evaluate('saveCheckpoint()');page.reload();page.click('#startBtn');assert page.evaluate('game.boss.hp')==hp;assert page.evaluate('game.weapon')==3
   page.evaluate('game.boss.hitCooldown=0;hitBoss(game.boss,100)');place(600,page.evaluate('game.boss.floor'));key('e');page.click('#solutionBtn')
   for _ in range(2):
    page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'));page.locator('#guideAnswer').press('Enter')
   page.reload();page.click('#startBtn');key('e');assert page.evaluate('game.boss.defeated && studyFor(challengeDoor).guideAnswers.length===2');assert page.locator('#answers').is_hidden()
   # Snapshot review of each new environment and the boss encounter.
   for level in [25,27,29,31,33,35]:
    page.evaluate('(n)=>startGame(n)',level);place(500,3);tick();page.locator('#stage').screenshot(path=f'/tmp/shadow-{level}.png')
   page.evaluate('startGame(36);game.files[2].collected=true');place(510,page.evaluate('game.boss.floor'));tick(80);page.locator('#stage').screenshot(path='/tmp/shadow-boss.png')
   assert not errors,errors
   print('PASS: hazard warning/jumping/damage/override, ice braking, villain HP and checked-guide persistence; no browser errors',flush=True)
   browser.close()
 finally:server.shutdown()
if __name__=='__main__':run()
