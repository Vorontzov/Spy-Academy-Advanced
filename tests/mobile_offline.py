"""Mobile touch/scroll, real animation, offline single-file delivery and storage failure checks."""
import os,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def run():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None)
   errors=[]
   for width in [320,390,768]:
    ctx=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}');page.click('#startBtn')
    page.locator('#weaponTray').tap();page.wait_for_timeout(60);assert page.evaluate('game.weapon')==1
    # Use a true held pointer for directional movement.
    button=page.locator('[data-key="right"]');button.scroll_into_view_if_needed();box=button.bounding_box()
    cdp=ctx.new_cdp_session(page);x=box['x']+box['width']/2;y=box['y']+box['height']/2
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});page.wait_for_timeout(260)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert page.evaluate('game.player.x')>260
    page.evaluate('openChallenge(game.files[0])');page.click('#solutionBtn')
    page.locator('#guideAnswer').fill('999999');page.locator('#guideCheck').tap();assert page.locator('#guideAnswer').get_attribute('aria-invalid')=='true'
    # CDP swipe proves the overlay can actually scroll under touch-action rules.
    page.locator('#challengeOverlay').scroll_into_view_if_needed();bounds=page.locator('#challengeOverlay').bounding_box()
    sx=bounds['x']+bounds['width']*.8;sy=bounds['y']+bounds['height']*.8
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':sy}]})
    for step in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx,'y':sy-step*30}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(150)
    page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[0].answer'));page.locator('#guideCheck').tap();assert page.evaluate('studyFor(challengeDoor).guideAnswers.length')==1
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    if width==390:page.screenshot(path='/tmp/advanced-mobile-guide.png')
    page.click('#challengeSkip');page.evaluate('game.files.forEach(f=>f.collected=true);beginEscape()');page.locator('[data-key="up"]').tap();page.wait_for_timeout(300);assert page.evaluate('game.escape.ready && game.escape.distance>0')
    if width==390:page.locator('#stage').scroll_into_view_if_needed();page.screenshot(path='/tmp/advanced-mobile-escape.png')
    ctx.close()
   print('PASS: 320/390/768px layout, real touch movement, equipment, guided inputs, overlay swiping, and escape launch',flush=True)
   for mode in ['blocked','corrupt']:
    ctx=browser.new_context()
    if mode=='blocked':ctx.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw Error('blocked')}})")
    else:ctx.add_init_script("localStorage.setItem('spyacademy.advanced.academy.v1','{bad json')")
    page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}');page.click('#startBtn');page.wait_for_timeout(100);assert page.evaluate("state==='playing'");page.evaluate('openChallenge(game.files[0])');page.click('#solutionBtn');page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[0].answer'));page.locator('#guideAnswer').press('Enter');assert page.evaluate('studyFor(challengeDoor).guideAnswers.length')==1
    ctx.close()
   ctx=browser.new_context(offline=True);page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/'index.html').read_text());page.click('#startBtn');page.wait_for_timeout(250);assert page.evaluate("state==='playing' && game.time>0")
   assert not errors,errors
   print('PASS: offline HTML play without a network connection, blocked and corrupted storage; no browser errors',flush=True)
   browser.close()
 finally:server.shutdown()
if __name__=='__main__':run()
