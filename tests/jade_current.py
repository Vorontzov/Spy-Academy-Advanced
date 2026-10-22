"""Jade Current: real keyboard/touch room routes, progression, saves and combat.
Positioning fixtures skip tower traversal; room navigation and interactions use
browser input. Combat fixtures isolate attack timing and high-jump physics.
"""
import os, shutil, threading, json
from functools import partial
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

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
            def walk(x):
                now=page.evaluate('game.player.x');delta=x-now
                key('ArrowRight' if delta>0 else 'ArrowLeft',max(1,round(abs(delta)*60/206)))
            def first_three(level):
                page.evaluate('(n)=>startGame(n)',level);tick()
                for i in range(3):
                    place(**page.evaluate('(i)=>({x:game.files[i].x,f:game.files[i].floor})',i));key('e');finish()
            def enter():
                place(**page.evaluate('({x:game.files[3].x,f:game.files[3].floor})'));key('e');assert page.evaluate('game.interior.active')
                page.evaluate('game.player.invulnerable=100')
            def middle():
                walk(400);key('ArrowUp');assert page.evaluate('game.player.y===floorY(1)');walk(530);key('e');assert page.evaluate('state')=='challenge'
            def upper():
                walk(710);key('ArrowUp');assert page.evaluate('game.player.y===floorY(0)');walk(990);key('e');assert page.evaluate('state')=='challenge'
            def exit_room():
                walk(710);key('ArrowDown');walk(400);key('ArrowDown');walk(150);key('e');assert not page.evaluate('game.interior.active')

            assert page.locator('#levelSelect optgroup').count()==5
            assert page.locator('#levelSelect optgroup[label="JADE CURRENT"] option').count()==18
            assert page.locator('#levelSelect option').count()==96
            escapes=set()
            for level in range(79,97):
                first_three(level)
                assert page.evaluate('knows("rising jump")')
                assert page.evaluate('game.interior.stations.every(f=>f.challenge.source)')
                enter();middle()
                before=page.evaluate('[game.time,game.interior.clock,game.energy,game.lives,game.ally.cooldown]')
                tick(180);assert page.evaluate('[game.time,game.interior.clock,game.energy,game.lives,game.ally.cooldown]')==before
                finish(guide=True);upper();finish(guide=True)
                assert page.evaluate('game.interior.cleared')
                assert not page.evaluate('game.files[3].collected')
                exit_room();key('e');assert page.evaluate('state')=='challenge';finish()
                floor=page.evaluate('game.boss.floor');place(495,floor)
                page.evaluate('game.player.facing=1;game.weapon=0;game.ownedWeapons.push(0);game.player.invulnerable=100;game.guards=game.guards.filter(g=>g.isBoss);game.cloak=0')
                key('x',2300);assert page.evaluate('game.boss.defeated'),level
                place(**page.evaluate('({x:game.files[4].x,f:game.files[4].floor})'));key('e');finish()
                place(230,page.evaluate('game.floors-1'));tick();assert page.evaluate('game.escape!==null')
                escapes.add(page.evaluate('game.escape.kind'));key('ArrowUp')
                page.evaluate('game.escape.drive.completed=2;game.escape.distance=game.escape.target-2');tick(4)
                assert page.evaluate('state')=='won',level
            assert escapes=={'boat','car','motorcycle','plane','helicopter'}
            assert 'Campaign complete!' in page.locator('#resultText').inner_text()
            page.click('#nextBtn');assert page.evaluate('state')=='lobby'
            print('PASS: all 18 Jade missions / 126 maths gates, actual interior routes, villain captures, five escape roles and 96-mission finale',flush=True)

            # Skills have real physics/combat effects, are earned, and survive reloads.
            page.evaluate('practice.techniques=[]');first_three(79);assert page.evaluate('practice.techniques')==['rising jump']
            place(650,5);page.evaluate('game.guards=[];game.hazards=[];game.machines=[]')
            page.keyboard.down('ArrowUp');key('Space');page.keyboard.up('ArrowUp');tick(60)
            assert page.evaluate('game.player.y===floorY(4)&&game.player.grounded')
            key('Space');tick(45);assert page.evaluate('game.player.y===floorY(4)')
            first_three(80);assert page.evaluate('knows("spinning kick")&&!knows("aerial strike")')
            place(600,4);page.evaluate('game.guards=[makeMartial(1,520,4,"knife"),makeMartial(2,680,4,"sword")];game.melee=0;game.player.facing=1')
            key('c');assert page.evaluate('game.guards.every(g=>g.stun>0)')
            first_three(81);place(600,4);page.evaluate('game.guards=[makeMartial(1,650,4,"kungfu")];game.melee=0;game.player.facing=1')
            key('Space');tick(12);key('c');assert page.evaluate('game.guards[0].stun>0&&game.meleeStyle==="AERIAL STRIKE"')
            page.evaluate('saveCheckpoint()');page.reload();page.click('#startBtn');assert page.evaluate('practice.techniques.length')==3
            print('PASS: earned and saved rising jump to the floor above, ordinary jump, two-sided spinning kick and mid-air strike',flush=True)

            # Weapons are acquired from real caches and use their distinct reach/cooldown.
            page.evaluate('startGame(83)')
            for weapon,reach in [(5,72),(6,125),(7,104)]:
                item=page.evaluate('(w)=>game.items.find(i=>i.weapon===w)',weapon);place(item['x'],item['floor']);tick()
                assert page.evaluate('(w)=>game.ownedWeapons.includes(w)',weapon)
                while page.evaluate('game.weapon')!=weapon:key('q')
                place(600,4);page.evaluate('(reach)=>{game.guards=[makeMartial(1,600+reach-5,4,"sword")];game.player.facing=1;game.melee=0;game.player.fireCooldown=0}',reach)
                key('x');assert page.evaluate('game.guards[0].stun>0')
                assert page.evaluate('game.bullets.length')==0
                assert page.evaluate('game.melee')>0
            print('PASS: knife, sword and machete caches, Q selection and FIRE melee attacks',flush=True)

            # All four opponents warn, attack, recover, and allow a normal jump dodge.
            for kind in ['knife','sword','machete','kungfu']:
                page.evaluate('startGame(79)');place(600,4)
                page.evaluate('(kind)=>{game.guards=[makeMartial(1,650,4,kind,470,720)];game.guards[0].cooldown=0;game.player.invulnerable=0;game.hazards=[];game.machines=[];game.cloak=0}',kind)
                tick();assert page.evaluate('game.guards[0].phase')=='aim';assert page.evaluate('game.lives')==3
                wind=page.evaluate('MARTIAL[game.guards[0].kind].windup');tick(max(1,round((wind-.18)*60)))
                key('Space');tick(13);assert page.evaluate('game.guards[0].phase')=='attack';assert page.evaluate('game.lives')==3
                tick(55);assert page.evaluate('game.guards[0].phase')=='recover'
                # Deliberately stand within the active strike region.
                place(600,4);page.evaluate('game.guards[0].x=640;game.guards[0].dir=-1;game.guards[0].phase="attack";game.guards[0].phaseTime=.25;game.player.invulnerable=0');tick()
                assert page.evaluate('game.lives')==2,kind
            print('PASS: four telegraphed melee opponents, jump dodges, recovery openings and actual damage',flush=True)

            # Live factory conveyors, warning windows, press damage and shutdown.
            page.evaluate('startGame(85);game.guards=[];game.hazards=[]');place(490,1)
            page.evaluate('game.time=0');x=page.evaluate('game.player.x');tick(30);assert page.evaluate('game.player.x')>x+10
            place(560,1);page.evaluate('game.player.invulnerable=0;game.time=4.1-game.machines[0].offset');tick(15);assert page.evaluate('game.lives')==3
            page.evaluate('game.time=5.2-game.machines[0].offset');tick();assert page.evaluate('game.lives')==2
            page.evaluate('game.files[2].collected=true;game.player.invulnerable=0');tick(360);assert page.evaluate('game.lives')==2
            print('PASS: working conveyors, press warnings/damage, safety override and frozen maths clocks',flush=True)

            # In-room checked steps, scratch, exit/re-entry, continue and reload.
            first_three(85);enter();middle();page.click('#solutionBtn')
            page.locator('#guideAnswer').fill('definitely wrong');page.locator('#guideAnswer').press('Enter')
            assert page.evaluate('studyFor(challengeDoor).guideAnswers.length')==0
            assert page.locator('#challengeContinue').is_hidden()
            page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[0].answer'));page.locator('#guideAnswer').press('Enter')
            page.locator('.scratch summary').click();page.locator('#scratchpad').fill('Keep my valve calculations');page.evaluate('saveCheckpoint()');page.reload();page.click('#startBtn')
            assert page.evaluate('game.interior.active&&game.player.x===150&&game.interior.stations[0].study.guideAnswers.length===1')
            middle();assert page.locator('#scratchpad').input_value()=='Keep my valve calculations'
            while page.locator('#guideForm').is_visible():
                page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'));page.locator('#guideAnswer').press('Enter')
            page.click('#challengeContinue');tick()
            page.evaluate('game.player.invulnerable=0;game.lives=1;damage()');assert page.evaluate('state')=='lost';page.click('#nextBtn')
            assert page.evaluate('game.interior.active&&game.interior.stations[0].collected&&game.player.x===150&&game.lives===3')
            key('e');assert not page.evaluate('game.interior.active');key('e');assert page.evaluate('game.interior.active&&game.interior.stations[0].collected')
            # Saved invalid guide suffixes are discarded, not trusted.
            page.evaluate('game.interior.stations[1].study.solution=true;game.interior.stations[1].study.guideAnswers=["invalid"];saveCheckpoint()')
            page.reload();page.click('#startBtn');assert page.evaluate('game.interior.stations[1].study.guideAnswers.length')==0
            print('PASS: room freeze, gated hints, scratch/checked-step reload, safe continuation, backtracking and corrupt-prefix rejection',flush=True)

            first_three(82);enter();page.evaluate('game.player.x=500;game.gadget=2;game.energy=100');key('g');tick(42)
            assert page.evaluate('game.player.y===floorY(1)&&!game.player.traversal')
            page.evaluate('game.gadget=1;game.energy=100;game.guards=[makeMartial(1,560,1,"sword")]');key('g');assert page.evaluate('game.guards[0].stun>0')
            page.evaluate('game.ally.id="ibis";game.ally.cooldown=0');key('b');assert page.evaluate('game.interior.scan>5&&game.cloak>5')
            print('PASS: interior grapple landing, EMP and Ibis panel scan',flush=True)

            # New escape drift is physical; shields, shots and beacons still work.
            for level,kind in [(79,'boat'),(83,'helicopter'),(84,'plane')]:
                page.evaluate('(n)=>{startGame(n);game.files.forEach(f=>f.collected=true);game.boss.defeated=true;beginEscape();game.escape.ready=true;game.escape.timer=100;game.escape.distance=70;game.player.invulnerable=0}',level)
                assert page.evaluate('game.escape.kind')==kind
                x=page.evaluate('game.escape.x');tick(60);assert abs(page.evaluate('game.escape.x')-x)>.001
                key('ArrowLeft',30);assert page.evaluate('game.escape.x')<x
                page.evaluate('game.energy=100');key('g');assert page.evaluate('game.escape.shield')>3
                page.evaluate('game.escape.obstacles=[{x:game.escape.x,y:game.escape.y,kind:"barrier",dead:false}]');tick();assert page.evaluate('game.lives')==3
                page.evaluate('game.escape.shield=0;game.player.invulnerable=0;game.escape.obstacles=[{x:game.escape.x,y:game.escape.y,kind:"barrier",dead:false}]');tick();assert page.evaluate('game.lives')==2
                page.evaluate('game.escape.obstacles=[{x:game.escape.x,y:game.escape.y,kind:"beacon",dead:false}]');tick();assert page.evaluate('game.escape.beacons')==1
                key('x');assert page.evaluate('game.escape.shots.length')>0
                page.locator('#stage').screenshot(path=f'/tmp/jade-{kind}.png')
            for level in [79,82,85,88,91,94]:
                page.evaluate('(n)=>startGame(n)',level);place(500,3);tick();page.locator('#stage').screenshot(path=f'/tmp/jade-{level}.png')
            first_three(82);enter();tick();page.locator('#stage').screenshot(path='/tmp/jade-interior.png')
            print('PASS: boat currents and flight crosswinds, steering, shields, collisions, beacons and shots',flush=True)
            ctx.close()

            for width in [320,390,768]:
                ctx=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True)
                ctx.add_init_script('window.requestAnimationFrame=()=>0');page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url)
                page.evaluate('startGame(96);game.files.slice(0,3).forEach(f=>{f.collected=true;studyFor(f).solved=true});unlockTraining();recruitAlly();enterInterior()');tick()
                page.locator('[data-key="right"]').scroll_into_view_if_needed()
                box=page.locator('[data-key="right"]').bounding_box();cdp=ctx.new_cdp_session(page)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}]});tick(12)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert page.evaluate('game.player.x')>150
                page.locator('#allyTray').tap();tick();assert page.evaluate('game.ally.cooldown')>13
                page.evaluate('game.player.x=400');page.locator('[data-key="up"]').tap();tick();assert page.evaluate('game.player.y===floorY(1)')
                page.evaluate('game.player.x=530');page.locator('[data-key="up"]').tap();tick();assert page.evaluate('state')=='challenge'
                page.locator('#solutionBtn').tap()
                while page.locator('#guideForm').is_visible():
                    page.locator('#guideAnswer').fill(page.evaluate('challengeDoor.challenge.guide[studyFor(challengeDoor).guideAnswers.length].answer'));page.locator('#guideCheck').tap()
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                page.locator('#challengeContinue').tap();tick()
                if width==390:page.locator('#stage').scroll_into_view_if_needed();page.screenshot(path='/tmp/jade-mobile-room.png')
                ctx.close()
            assert not errors,errors
            print('PASS: 320/390/768px room movement, ladders, ally support, checked maths and no browser errors',flush=True)
            browser.close()
    finally:server.shutdown()
if __name__=='__main__':run()
