"""Eclipse Pact integration: actual maze controls, allies, bosses and saved progress.

Tower fixtures position the player at objectives and arenas. Every maze route
uses browser key/touch events and an independent breadth-first path finder.
"""
import os, shutil, threading
from collections import deque
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def route(grid,start,goal):
    q=deque([(start,[])]);seen={start}
    while q:
        (x,y),path=q.popleft()
        if (x,y)==goal:return path
        for key,dx,dy in [('ArrowRight',1,0),('ArrowLeft',-1,0),('ArrowDown',0,1),('ArrowUp',0,-1)]:
            xx,yy=x+dx,y+dy
            if 0<=yy<len(grid) and 0<=xx<len(grid[0]) and grid[yy][xx]==0 and (xx,yy) not in seen:
                seen.add((xx,yy));q.append(((xx,yy),path+[key]))
    raise AssertionError('Unreachable maze objective')

def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None)
            ctx=browser.new_context(viewport={'width':1440,'height':1100})
            ctx.add_init_script('window.requestAnimationFrame=()=>0')
            page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            url=f'http://127.0.0.1:{server.server_port}';page.goto(url)
            def tick(n=1):page.evaluate('(n)=>{for(let i=0;i<n;i++){clock+=1/60;update(1/60)}render(clock)}',n)
            def key(k,n=1):page.keyboard.down(k);tick(n);page.keyboard.up(k)
            def place(x,f):page.evaluate('''({x,f})=>{Object.assign(game.player,{x,y:floorY(f),vx:0,vy:0,fallStart:floorY(f),checkpoint:{x,floor:f},grounded:true,lift:null,traversal:null});camera=clamp(floorY(f)-240,0,floorY(game.floors-1)-H+76);render(clock)}''',{'x':x,'f':f})
            def finish(guide=False):
                if guide:
                    page.click('#solutionBtn')
                    while page.locator('#guideForm').is_visible():
                        page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'))
                        page.locator('#guideAnswer').press('Enter')
                else:page.locator('.answer').nth(page.evaluate('challengeDoor.challenge.correct')).click()
                page.click('#challengeContinue');tick()
            def walk(goal):
                m=page.evaluate('game.labyrinth');path=route(m['grid'],(m['x'],m['y']),tuple(goal))
                tick(18)
                for k in path:key(k);tick(12)
            def unlock_first_three(level):
                page.evaluate('(n)=>startGame(n)',level);tick()
                for i in range(3):
                    place(**page.evaluate('(i)=>({x:game.files[i].x,f:game.files[i].floor})',i));key('e');finish()

            assert page.locator('#levelSelect optgroup').count()==5
            assert page.locator('#levelSelect optgroup[label="ECLIPSE PACT"] option').count()==18
            layouts=set()
            for level in range(61,79):
                page.evaluate('(n)=>startGame(n)',level);tick()
                assert not page.evaluate('game.ally.ready')
                assert page.evaluate('game.boss.maxHp')==12+2*((level-61)//6)
                assert page.evaluate('game.files[3].floor===game.floors-3')
                assert page.evaluate('game.files.every(f=>!isGap(f.x))')
                key('b');assert page.evaluate('game.ally.cooldown')==0
                for i in range(5):
                    if i==4:
                        floor=page.evaluate('game.boss.floor');place(495,floor)
                        page.evaluate('game.player.facing=1;game.weapon=0;game.ownedWeapons.push(0);game.player.invulnerable=100;game.guards=game.guards.filter(g=>g.isBoss);game.cloak=0')
                        key('x',1800);assert page.evaluate('game.boss.defeated'),level
                    place(**page.evaluate('(i)=>({x:game.files[i].x,f:game.files[i].floor})',i));key('e')
                    if i==3:
                        assert page.evaluate('game.labyrinth.active') and page.evaluate('state')=='playing'
                        m=page.evaluate('game.labyrinth');layouts.add(str(m['grid']))
                        assert not page.evaluate('game.files[3].collected')
                        page.evaluate('game.player.invulnerable=100')
                        walk((m['sigil']['x'],m['sigil']['y']));assert page.evaluate('game.labyrinth.hasSigil')
                        walk((m['exit']['x'],m['exit']['y']));assert page.evaluate('game.labyrinth.cleared && !game.labyrinth.active')
                        key('e')
                    assert page.evaluate('state')=='challenge',(level,i)
                    before=page.evaluate('[game.time,game.lives,game.ally.cooldown,game.boss.phaseTime]')
                    tick(240);assert page.evaluate('[game.time,game.lives,game.ally.cooldown,game.boss.phaseTime]')==before
                    finish(guide=(i in [0,4]))
                    if i==1:
                        assert page.evaluate('game.ally.ready && game.ownedWeapons.includes(ALLIES[game.ally.id].gift)')
                        key('b');assert page.evaluate('game.ally.cooldown')>13
                place(230,page.evaluate('game.floors-1'));tick();assert page.evaluate('game.escape!==null')
                key('ArrowUp');page.evaluate('game.escape.drive.completed=2;game.escape.distance=game.escape.target-2');tick(4)
                assert page.evaluate('state')=='won'
            assert len(layouts)>=12, len(layouts)
            assert 'Campaign complete!' not in page.locator('#resultText').inner_text()
            page.click('#nextBtn');assert page.evaluate('game.mission')==79
            print('PASS: 18 missions / 90 maths gates, 18 actual maze routes, gifts, support, all villains, escapes and transition to operation 79',flush=True)

            # Every ally has a distinct usable effect and a real cooldown.
            for level,ally in [(61,'nova'),(62,'ibis'),(63,'rook')]:
                unlock_first_three(level);place(510,page.evaluate('game.boss.floor'))
                page.evaluate('game.energy=10;game.player.invulnerable=0;game.ally.cooldown=0;game.boss.phase="recover";game.boss.phaseTime=5')
                hp=page.evaluate('game.boss.hp');key('b')
                assert page.evaluate('game.ally.cooldown')>13
                if ally=='nova':assert page.evaluate('game.energy>=55&&game.player.invulnerable>4')
                if ally=='ibis':assert page.evaluate('game.cloak>5&&game.labyrinth.scan>5')
                if ally=='rook':assert page.evaluate('game.boss.hp')==hp-3
                cooldown=page.evaluate('game.ally.cooldown');key('b');assert page.evaluate('game.ally.cooldown')<cooldown
                page.evaluate('saveCheckpoint()');gift=page.evaluate('game.weapon');page.reload();page.click('#startBtn')
                assert page.evaluate('game.ally.ready&&game.ally.cooldown>13')
                assert page.evaluate('game.weapon')==gift
            print('PASS: Nova shield/recharge, Ibis cloak/scan, Rook covering damage, cooldown and supplied-weapon saves',flush=True)

            # Genuine telegraphs, phase-specific defenses, low-health acceleration and floor blasts.
            for level,style in [(61,'warden'),(62,'hunter'),(63,'saboteur')]:
                unlock_first_three(level);place(510,page.evaluate('game.boss.floor'))
                page.evaluate('game.guards=[game.boss];game.player.invulnerable=100;game.cloak=0')
                tick(76);assert page.evaluate('game.boss.phase')=='aim'
                if style=='warden':
                    hp=page.evaluate('game.boss.hp');page.evaluate('hitBoss(game.boss,3)');assert page.evaluate('game.boss.hp')==hp
                start=page.evaluate('game.boss.x');tick(68);assert page.evaluate('game.boss.phase')=='attack'
                if style=='warden':assert page.evaluate('game.bullets.some(b=>b.owner==="guard"&&b.y===game.boss.y-9)')
                if style=='hunter':assert page.evaluate('game.boss.x')<start
                if style=='saboteur':
                    assert page.evaluate('game.bossTraps.length')==3
                    b=page.evaluate('game.bossTraps[1]');place(b['x'],b['floor']);page.evaluate('game.player.invulnerable=0')
                    tick(35);assert page.evaluate('game.lives')==3
                    key('Space');tick(28);assert page.evaluate('game.lives')==3
                    place(b['x'],b['floor']);tick(14);assert page.evaluate('game.lives')==2
                tick(10 if style=='saboteur' else 50);assert page.evaluate('game.boss.phase')=='recover'
                page.evaluate('game.boss.hp=game.boss.maxHp/2');tick();assert page.evaluate('game.boss.enraged')
                tick(160);assert page.evaluate('game.bossTraps.length<=3')
            print('PASS: shield timing, low shockwaves, charge telegraph, delayed bombs, jump clearance and overdrive',flush=True)

            # Maze backtracking, collisions, firing, pauses, reload and continuation preserve objectives.
            unlock_first_three(62);place(**page.evaluate('({x:game.files[3].x,f:game.files[3].floor})'));key('e');tick(20)
            key('ArrowLeft');assert page.evaluate('game.labyrinth.x===1&&game.labyrinth.y===1')
            key('Space');assert not page.evaluate('game.labyrinth.active')
            key('e');assert page.evaluate('game.labyrinth.active')
            page.evaluate('game.player.invulnerable=100');m=page.evaluate('game.labyrinth');walk((m['sigil']['x'],m['sigil']['y']))
            page.evaluate('saveCheckpoint()');pos=page.evaluate('[game.labyrinth.x,game.labyrinth.y]')
            page.reload();page.click('#startBtn');assert page.evaluate('game.labyrinth.active&&game.labyrinth.hasSigil')
            assert page.evaluate('[game.labyrinth.x,game.labyrinth.y]')==pos
            key('p');before=page.evaluate('JSON.stringify(game.labyrinth)');tick(300);assert page.evaluate('JSON.stringify(game.labyrinth)')==before;page.click('#resumeBtn')
            page.evaluate('const g=game.labyrinth.guards[0];game.labyrinth.x=g.path[g.index].x;game.labyrinth.y=g.path[g.index].y;game.player.invulnerable=0;game.cloak=0;g.timer=1')
            key('x');assert page.evaluate('game.labyrinth.guards[0].stun>4&&game.lives===3')
            page.evaluate('game.labyrinth.guards[0].stun=0;game.labyrinth.guards[0].timer=1;game.player.invulnerable=0;game.lives=1');tick()
            assert page.evaluate('state')=='lost';page.click('#nextBtn')
            assert page.evaluate('game.labyrinth.active&&game.labyrinth.hasSigil&&game.labyrinth.x===1&&game.lives===3')
            m=page.evaluate('game.labyrinth');walk((m['exit']['x'],m['exit']['y']));assert page.evaluate('game.labyrinth.cleared')
            page.evaluate('saveCheckpoint()');page.reload();page.click('#startBtn');key('e');assert page.evaluate('state')=='challenge'
            print('PASS: maze walls, return route, sentinel stun/damage, pause, mid-maze reload, sigil persistence and continuation',flush=True)

            for level in [61,64,67,70,73,76]:
                page.evaluate('(n)=>startGame(n)',level);place(500,3);tick();page.locator('#stage').screenshot(path=f'/tmp/eclipse-{level}.png')
            unlock_first_three(78);place(**page.evaluate('({x:game.files[3].x,f:game.files[3].floor})'));key('e');key('b');tick()
            page.locator('#stage').screenshot(path='/tmp/eclipse-maze.png')
            ctx.close()

            for width in [320,390,768]:
                ctx=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True)
                ctx.add_init_script('window.requestAnimationFrame=()=>0');page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url)
                page.evaluate('startGame(62);game.files.slice(0,3).forEach(f=>{f.collected=true;studyFor(f).solved=true});recruitAlly();game.player.x=game.files[3].x;game.player.y=floorY(game.files[3].floor);game.player.fallStart=game.player.y;enterLabyrinth()')
                tick();page.locator('#allyTray').tap();tick();assert page.evaluate('game.labyrinth.scan')>5
                m=page.evaluate('game.labyrinth');k=route(m['grid'],(1,1),(m['sigil']['x'],m['sigil']['y']))[0]
                tick(20);page.locator('[data-key="'+{'ArrowRight':'right','ArrowLeft':'left','ArrowDown':'down','ArrowUp':'up'}[k]+'"]').tap();tick()
                assert page.evaluate('game.labyrinth.x!==1||game.labyrinth.y!==1')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                if width==390:page.locator('#stage').scroll_into_view_if_needed();page.screenshot(path='/tmp/eclipse-mobile-maze.png')
                for level in [61,63,74,78]:
                    page.evaluate('(n)=>{startGame(n);openChallenge(game.files[0])}',level);page.locator('#solutionBtn').tap()
                    while page.locator('#guideForm').is_visible():
                        page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'));page.locator('#guideCheck').tap()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    page.locator('#challengeContinue').tap()
                ctx.close()
            assert not errors,errors
            print('PASS: 320/390/768px maze movement/support, geometry diagrams, exact radical and inequality guides; no browser errors',flush=True)
            browser.close()
    finally:server.shutdown()
if __name__=='__main__':run()
