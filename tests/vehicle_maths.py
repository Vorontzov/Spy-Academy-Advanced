"""Vehicle maths uses steering/valves, checked guides, safe retries and persistent checkpoints."""
import os, shutil, threading
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def run():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None)
   ctx=browser.new_context(viewport={'width':1440,'height':1100});ctx.add_init_script('window.requestAnimationFrame=()=>0')
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}')
   def tick(n=1):page.evaluate('(n)=>{for(let i=0;i<n;i++){clock+=1/60;update(1/60)}render(clock)}',n)
   def key(k,n=1):page.keyboard.down(k);tick(n);page.keyboard.up(k)
   def start(level):
    page.evaluate('''(level)=>{startGame(level);game.files.forEach(f=>{f.collected=true;studyFor(f).solved=true});if(game.boss){game.boss.hp=0;game.boss.defeated=true;}beginEscape();game.player.invulnerable=100;}''',level);key('ArrowUp')
   def commit():
    if page.evaluate('game.escape.kind')=='car':
     value=int(page.evaluate('driveTask().challenge.answer'));valve=page.locator('#fuelValve');valve.focus();valve.press('Home')
     for _ in range(value):valve.press('ArrowRight')
     assert page.evaluate('driveTask().value')==value
    else:
     target=page.evaluate('driveTask().challenge.correct');lane=page.evaluate('driveTask().lane');page.locator('#stage').focus()
     for _ in range(abs(target-lane)):key('ArrowRight' if target>lane else 'ArrowLeft')
     assert page.evaluate('driveTask().lane')==target
    page.click('#driveCommit');tick();assert page.evaluate('!driveTask() && game.escape.turbo>5 && game.escape.shield>3')
   cases=page.evaluate('''()=>['car','motorcycle'].flatMap(kind=>[[1,6],[7,16],[17,36]].map(([lo,hi])=>MathEngine.campaign.find(s=>s.level>=lo&&s.level<=hi&&s.escape===kind).level))''')
   families=set()
   for level in cases:
    start(level);page.evaluate('game.escape.distance=game.escape.target/3-1');tick(2)
    assert page.locator('#driveOverlay').is_visible();families.add(page.evaluate('driveTask().challenge.templateId'))
    before=page.evaluate('[game.time,game.escape.distance,game.lives,game.escape.obstacles]');tick(600);assert page.evaluate('[game.time,game.escape.distance,game.lives,game.escape.obstacles]')==before
    if page.evaluate('game.escape.kind')=='motorcycle':page.locator('.drive-lane').nth(page.evaluate('(driveTask().challenge.correct+1)%driveTask().challenge.answers.length')).click()
    page.click('#driveCommit');assert page.evaluate('Boolean(driveTask()) && game.lives===3');assert page.locator('#driveFeedback').inner_text()
    # Guidance conceals the interactive choices and requires every calculation.
    page.click('#driveGuideBtn');assert page.locator('#driveControls').is_hidden();assert page.locator('#driveGuideResult').is_hidden()
    page.locator('#driveStepAnswer').fill('999999');page.locator('#driveStepAnswer').press('Enter');assert page.evaluate('driveTask().study.guideAnswers.length')==0
    answer=page.evaluate('driveTask().challenge.guide[0].answer');page.locator('#driveStepAnswer').fill(answer);page.locator('#driveStepAnswer').press('Enter')
    qid=page.evaluate('driveTask().challenge.id');page.reload();page.click('#startBtn');tick()
    assert page.evaluate('driveTask().challenge.id')==qid and page.evaluate('driveTask().study.guideAnswers.length')==1
    assert page.locator('#driveOverlay').is_visible() and page.locator('#driveControls').is_hidden()
    while page.locator('#driveGuideForm').is_visible():
     answer=page.evaluate('driveTask().challenge.guide[driveTask().study.guideAnswers.length].answer');page.locator('#driveStepAnswer').fill(answer);page.locator('#driveStepAnswer').press('Enter')
    assert page.locator('#driveGuideResult').is_visible();kind=page.evaluate('game.escape.kind');page.locator('#stage').screenshot(path=f'/tmp/vehicle-{kind}.png')
    # Pausing cannot overlay or continue the road task.
    page.locator('#stage').focus();key('p');assert page.locator('#driveOverlay').is_hidden();assert page.locator('#pauseOverlay').is_visible();page.click('#resumeBtn');tick();assert page.locator('#driveOverlay').is_visible()
    commit();assert page.evaluate('game.escape.drive.completed')==1;assert not page.evaluate('practice.history.at(-1).independent')
    page.evaluate('saveCheckpoint()');page.reload();page.click('#startBtn');assert page.evaluate('game.escape.drive.completed')==1
    key('ArrowUp');page.evaluate('game.escape.distance=game.escape.target*2/3-1');tick(2);assert page.locator('#driveOverlay').is_visible()
    commit();assert page.evaluate('game.escape.drive.completed')==2;assert page.evaluate('practice.history.at(-1).independent')
    page.evaluate('game.escape.distance=game.escape.target-2');tick(4);assert page.evaluate('state')=='won'
   assert len(families)==6,families
   print('PASS: six progressive vehicle families, steering and valve controls, safe retries, action freeze, checked guides, saves, practice records and two checkpoints per escape',flush=True)
   # Pre-update escape saves skip junctions already passed, without inventing practice credit.
   start(1);page.evaluate('game.escape.distance=game.escape.target*.75;saveDrive=()=>undefined;saveCheckpoint()')
   page.reload();page.click('#startBtn');assert page.evaluate('game.escape.drive.completed')==2
   # A corrupt guided prefix cannot unlock later calculation steps.
   start(2);page.evaluate('game.escape.distance=game.escape.target/3');tick();page.click('#driveGuideBtn')
   page.evaluate('driveTask().study.guideAnswers=["999999","1"];saveCheckpoint()');page.reload();page.click('#startBtn');assert page.evaluate('driveTask().study.guideAnswers.length')==0
   # Phone layouts and actual touch on the two distinct interaction surfaces.
   for width in [320,390,768]:
    mob=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True);mob.add_init_script('window.requestAnimationFrame=()=>0')
    p=mob.new_page();p.on('pageerror',lambda e:errors.append(str(e)));p.goto(f'http://127.0.0.1:{server.server_port}')
    for level in [1,2]:
     p.evaluate('''(n)=>{startGame(n);game.files.forEach(f=>{f.collected=true;studyFor(f).solved=true});beginEscape();game.escape.ready=true;game.escape.distance=game.escape.target/3;update(1/60);render(clock)}''',level)
     assert p.locator('#driveOverlay').is_visible();assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
     if level==1:
      p.locator('.drive-lane').nth(p.evaluate('driveTask().challenge.correct')).tap();p.locator('#driveCommit').tap();assert p.evaluate('game.escape.drive.completed')==1
     else:
      slider=p.locator('#fuelValve');slider.scroll_into_view_if_needed();box=slider.bounding_box();p.touchscreen.tap(box['x']+box['width']*.7,box['y']+box['height']/2)
      assert p.evaluate('driveTask().value')>0
      p.locator('#driveGuideBtn').tap();p.locator('#driveStepAnswer').fill(p.evaluate('driveTask().challenge.guide[0].answer'));p.locator('#driveGuideForm button').tap();assert p.evaluate('driveTask().study.guideAnswers.length')==1
     if width==390 and level==2:p.screenshot(path='/tmp/vehicle-mobile.png')
    mob.close()
   assert not errors,errors
   print('PASS: legacy escape saves, corrupt guide recovery, mobile lane taps and fuel slider at 320/390/768px; no browser errors',flush=True)
   browser.close()
 finally:server.shutdown()
if __name__=='__main__':run()
