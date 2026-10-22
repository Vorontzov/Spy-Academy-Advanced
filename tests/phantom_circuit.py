"""Phantom Circuit: 120 gates, taller towers, new saves, finale and phone guides.

Objective/combat fixtures position the player to isolate gates; the separate
30-floor traversal uses actual movement, stair and lift controls.
"""
import os, shutil, threading
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def run():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None)
            ctx = browser.new_context(viewport={'width':1440, 'height':1100})
            ctx.add_init_script('window.requestAnimationFrame=()=>0')
            page = ctx.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            url = f'http://127.0.0.1:{server.server_port}'
            page.goto(url)

            def tick(n=1):
                page.evaluate('(n)=>{for(let i=0;i<n;i++){clock+=1/60;update(1/60)}render(clock)}', n)
            def key(k, n=1):
                page.keyboard.down(k); tick(n); page.keyboard.up(k)
            def place(x, f):
                page.evaluate('''({x,f})=>{Object.assign(game.player,{x,y:floorY(f),vx:0,vy:0,fallStart:floorY(f),checkpoint:{x,floor:f},grounded:true,lift:null,traversal:null});camera=clamp(floorY(f)-240,0,floorY(game.floors-1)-H+76);render(clock)}''', {'x':x,'f':f})
            def step():
                page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'))
                page.locator('#guideAnswer').press('Enter')
            def finish(guide=False):
                if guide:
                    page.click('#solutionBtn')
                    while page.locator('#guideForm').is_visible(): step()
                else:
                    page.locator('.answer').nth(page.evaluate('challengeDoor.challenge.correct')).click()
                page.click('#challengeContinue'); tick()

            assert page.locator('#levelSelect option').count() == 96
            assert page.locator('#levelSelect optgroup').count() == 5
            assert page.locator('#levelSelect optgroup[label="PHANTOM CIRCUIT"] option').count() == 24
            page.select_option('#levelSelect', '60')
            assert 'PHANTOM CIRCUIT' in page.locator('.classified').inner_text()
            assert '30 floors' in page.locator('#lessonBrief').inner_text()
            for level in range(37, 61):
                page.evaluate('(n)=>startGame(n)', level); tick()
                assert page.evaluate('game.files.length===5 && game.files.every(f=>f.challenge.source)')
                assert page.evaluate('game.items.every(i=>!isGap(i.x)&&i.floor<game.floors)')
                assert page.evaluate('game.files.every((f,i)=>!isGap(f.x)&&f.requires.every(r=>r<i))')
                assert page.evaluate('game.boss.maxHp') == 10 + 2*((level-37)//8)
                assert page.evaluate('game.ownedWeapons.length===0') == (level in [37,44,49,56])
                assert page.evaluate('[0,2,4].map(i=>game.files[i].challenge.tier)') == [1,2,3]
                assert page.evaluate('new Set([0,2,4].map(i=>game.files[i].challenge.templateId)).size') == 1
                page.evaluate('beginEscape()'); assert page.evaluate('game.escape===null')
                hp = page.evaluate('game.boss.hp')
                page.evaluate('stunGuard(game.boss,true,3)'); assert page.evaluate('game.boss.hp') == hp
                for i in range(4):
                    d = page.evaluate('(i)=>({x:game.files[i].x,f:game.files[i].floor})', i)
                    place(**d); key('e'); assert page.evaluate('state') == 'challenge', (level,i)
                    before = page.evaluate('[game.time,game.lives,game.boss.hp]')
                    tick(180); assert page.evaluate('[game.time,game.lives,game.boss.hp]') == before
                    finish(guide=(i==0))
                    assert page.evaluate('(i)=>game.files[i].collected', i)
                    if i == 2: assert page.evaluate('game.hazards.every(h=>hazardState(h)==="off")')
                assert not page.evaluate('caseReady(game.files[4])')
                floor = page.evaluate('game.boss.floor'); place(495, floor)
                page.evaluate('game.player.facing=1;game.weapon=0;game.ownedWeapons=[0];game.player.invulnerable=100;game.guards=game.guards.filter(g=>g.isBoss)')
                key('x', 1200); assert page.evaluate('game.boss.defeated'), level
                place(600, floor); key('e'); finish()
                place(230, page.evaluate('game.floors-1')); tick()
                assert page.evaluate('game.escape!==null')
                key('ArrowUp')
                page.evaluate('game.escape.drive.completed=2;game.escape.distance=game.escape.target-2')
                tick(4); assert page.evaluate('state') == 'won'
            assert 'The next operation is ready.' in page.locator('#resultText').inner_text()
            page.click('#nextBtn'); assert page.evaluate('game.mission') == 61
            page.evaluate('toLobby()')
            assert page.locator('#levelSelect option').count() == 96
            print('PASS: all 24 missions, 120 actual maths gates, three-tier progression, unarmed starts, override/boss gates and transition to Eclipse Pact', flush=True)

            # A tall tower is reachable via real controls, independent of combat fixtures.
            page.evaluate('startGame(60);game.guards=[];game.hazards=[]')
            def move(x):
                direction = 1 if x > page.evaluate('game.player.x') else -1
                k = 'ArrowRight' if direction == 1 else 'ArrowLeft'
                page.keyboard.down(k)
                page.evaluate('''({x,d})=>{for(let i=0;i<500;i++){if((game.player.x-x)*d>=0)break;clock+=1/60;update(1/60)}render(clock)}''', {'x':x,'d':direction})
                page.keyboard.up(k)
                assert abs(page.evaluate('game.player.x')-x) < 5
            move(110); key('ArrowDown'); tick(65)
            assert page.evaluate('floorAt(game.player.y)') == 1
            key('ArrowUp'); tick(65); assert page.evaluate('floorAt(game.player.y)') == 0
            move(392); page.keyboard.down('ArrowDown')
            page.evaluate('''()=>{for(let i=0;i<5000;i++){clock+=1/60;update(1/60);if(Math.abs(game.player.y-floorY(29))<2)break;}render(clock)}''')
            page.keyboard.up('ArrowDown')
            assert abs(page.evaluate('game.player.y-floorY(29)')) < 3
            assert page.evaluate('camera>3000 && state==="playing"')
            move(250); assert page.evaluate('game.escape===null')
            print('PASS: real stair round trip, lift descent through 30 floors, camera tracking and locked extraction', flush=True)

            # New systems and fractional guides keep only the verified prefix across reload.
            for level in [55,58,60]:
                page.evaluate('(n)=>startGame(n)', level); tick()
                d = page.evaluate('({x:game.files[0].x,f:game.files[0].floor})'); place(**d); key('e')
                qid = page.evaluate('challengeDoor.challenge.id')
                page.click('#solutionBtn'); step(); step()
                page.locator('#guideAnswer').fill('999999'); page.locator('#guideAnswer').press('Enter')
                assert page.evaluate('studyFor(challengeDoor).guideAnswers.length') == 2
                assert page.locator('#answers').is_hidden() and page.locator('#challengeContinue').is_hidden()
                page.reload(); page.click('#startBtn'); key('e')
                assert page.evaluate('challengeDoor.challenge.id') == qid
                assert page.evaluate('studyFor(challengeDoor).guideAnswers.length') == 2
                assert page.locator('#answers').is_hidden()
                while page.locator('#guideForm').is_visible(): step()
                page.click('#challengeContinue')
                assert page.evaluate('game.files[0].collected')
            for level in [37,40,43,46,49,52,55,58]:
                page.evaluate('(n)=>startGame(n)', level); place(500,3); tick()
                page.locator('#stage').screenshot(path=f'/tmp/phantom-{level}.png')
            page.evaluate('startGame(60);game.files[2].collected=true')
            place(510,page.evaluate('game.boss.floor')); tick(80)
            page.locator('#stage').screenshot(path='/tmp/phantom-boss.png')
            print('PASS: fraction/system/radical saved working, hidden future steps and eight environments render', flush=True)
            ctx.close()

            for width in [320,390,768]:
                ctx = browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True)
                page = ctx.new_page(); page.on('pageerror',lambda e:errors.append(str(e))); page.goto(url)
                for level in [56,58,60]:
                    page.evaluate('(n)=>{startGame(n);openChallenge(game.files[0])}',level)
                    page.locator('#solutionBtn').tap()
                    while page.locator('#guideForm').is_visible():
                        page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'))
                        page.locator('#guideCheck').tap()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,level)
                    if width==390 and level==58: page.screenshot(path='/tmp/phantom-mobile-guide.png')
                    page.locator('#challengeContinue').tap()
                page.evaluate('startGame(60);game.player.x=510;game.player.y=floorY(game.boss.floor);game.player.fallStart=game.player.y;camera=game.player.y-240;game.files[2].collected=true')
                page.wait_for_timeout(100)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                if width==390:
                    page.locator('#stage').scroll_into_view_if_needed();page.screenshot(path='/tmp/phantom-mobile-boss.png')
                ctx.close()
            assert not errors, errors
            print('PASS: 320/390/768px touch guides for literal equations, systems and radicals; final boss layout; no browser errors', flush=True)
            browser.close()
    finally:
        server.shutdown()

if __name__=='__main__': run()
