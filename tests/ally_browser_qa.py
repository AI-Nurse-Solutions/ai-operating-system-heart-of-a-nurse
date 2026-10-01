"""Local real-Chrome QA. Requires Playwright; no site publication or runtime install.
Run: python3 tests/ally_browser_qa.py --evidence /path/to/active-profile/scratch/ally-evidence
The HTTP server binds loopback on an ephemeral port and shuts down on exit.
"""
import argparse, functools, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,format,*args): pass

def run(out):
    out.mkdir(parents=True,exist_ok=True)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    log=[]; errors=[]
    def record(name): log.append(name);print('PASS:',name)
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True)
        context=browser.new_context(accept_downloads=True,viewport={'width':1280,'height':900})
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        base=f'http://127.0.0.1:{server.server_port}/'
        page.goto(base+'ally-soul-quiz.html')
        page.locator('button[type=submit]').click();assert page.locator('#result').is_hidden()
        record('blank quiz blocked')
        selects=['role','management','business','focus','steward','style','service','partnership']
        options={s:page.locator('#'+s+' option').evaluate_all('(es)=>es.map(e=>e.value).filter(Boolean)') for s in selects}
        for s in selects:page.select_option('#'+s,options[s][0])
        page.locator('button[type=submit]').click();assert page.locator('#result').is_hidden();record('quiz acknowledgment gate')
        for s in ['credentials','responsible','safe']:page.check('#'+s)
        combinations=0
        for role in options['role']:
          for management in options['management']:
            for business in options['business']:
              for s,v in [('role',role),('management',management),('business',business)]:page.select_option('#'+s,v)
              page.locator('button[type=submit]').click()
              assert page.locator('#result').is_visible()
              draft=page.input_value('#draft')
              for s in selects:
                text=page.locator('#'+s+' option:checked').inner_text();assert '- '+s+': '+text in draft
              assert 'qualified human review' in draft and 'A0 / no action' in draft
              if management=='none':assert 'No management authority is claimed' in draft
              if business=='none':assert 'No business ownership is claimed' in draft
              combinations+=1
        record(f'{combinations} role/management/business combinations reflect selected answers')
        for s in ['focus','steward','style','service','partnership']:
          for value in options[s]:
            page.select_option('#'+s,value);page.locator('button[type=submit]').click()
            assert '- '+s+': '+page.locator('#'+s+' option:checked').inner_text() in page.input_value('#draft')
            if s=='steward' and value=='private':assert 'No shared contribution or publication is authorized' in page.input_value('#draft')
        record('all use/support/contribution/style choices reflected')
        draft=page.input_value('#draft')
        with page.expect_download() as event:page.click('#download')
        d=event.value;d.save_as(out/'soul-draft.md');assert (out/'soul-draft.md').read_text()==draft
        record('SOUL download exact bytes')
        page.select_option('#role',options['role'][0]);assert page.locator('#result').is_hidden() and page.input_value('#draft')==''
        page.locator('button[type=submit]').click();page.locator('button[type=reset]').click()
        assert page.locator('#result').is_hidden() and page.input_value('#role')=='' and not page.is_checked('#safe')
        record('quiz edit invalidation and reset')
        page.goto(base+'ally-setup.html')
        with page.expect_download() as event:page.locator('a[href="downloads/ally-starter-package.zip"]').first.click()
        event.value.save_as(out/'downloaded-starter.zip');assert (out/'downloaded-starter.zip').read_bytes()==(ROOT/'downloads/ally-starter-package.zip').read_bytes()
        record('starter ZIP browser download exact bytes')
        for route in ['ally-stewardship.html','ally-starter/stewardship-ceremony.html']:
          page.goto(base+route)
          page.locator('#ceremony-form button[type=submit]').click();assert page.locator('#certificate').is_hidden()
          page.check('#pledge');page.fill('#accepted-date','');page.locator('#ceremony-form button[type=submit]').click();assert page.locator('#certificate').is_hidden()
          page.fill('#accepted-date','2026-09-30')
          literal='<img src=x onerror=alert(1)> & Ally'
          page.fill('#recipient',literal);page.locator('#ceremony-form button[type=submit]').click()
          assert page.locator('#certificate-name').inner_text()==literal and page.locator('#certificate-name img').count()==0
          with page.expect_download() as event:page.click('#save-certificate')
          target=out/('offline-keepsake.html' if '/' in route else 'keepsake.html');event.value.save_as(target)
          s=target.read_text();assert '&lt;img' in s and '<script' not in s and 'Commemorative only' in s and 'Non-Nurse Ally' in s
          page.evaluate('() => {window.printCalls=0;window.print=()=>{window.printCalls+=1};}')
          page.click('#print-certificate');assert page.evaluate('window.printCalls')==1, page.evaluate('({calls:window.printCalls,hidden:document.getElementById("certificate").hidden})')
          page.fill('#recipient','Edited');assert page.locator('#certificate').is_hidden()
          page.locator('#ceremony-form button[type=submit]').click();page.locator('#ceremony-form button[type=reset]').click();assert page.locator('#certificate').is_hidden() and page.input_value('#recipient')==''
          page.fill('#accepted-date','2026-09-30');page.check('#pledge');page.locator('#ceremony-form button[type=submit]').click()
          assert page.locator('#certificate-name').inner_text()=='A steward of good'
          page.reload();assert page.locator('#certificate').is_hidden() and not page.is_checked('#pledge')
          record(route+': acknowledgment/date gate, literal name, inert download, print handler, edit/reset/reload')
        page.goto(base+'ally-stewardship.html');page.fill('#recipient','A community steward');page.check('#pledge');page.locator('#ceremony-form button[type=submit]').click()
        page.screenshot(path=str(out/'certificate-1280.png'),full_page=True)
        page.pdf(path=str(out/'certificate.pdf'),format='A4',print_background=True)
        record('sample certificate PDF generated (page count checked separately)')
        for route in ['dashboard.html','mission-control.html','stewardship-ceremony.html']:
          offline=context.new_page();requests=[];offline.on('request',lambda req:requests.append(req.url) if req.url.startswith(('http:','https:','ws:','wss:')) else None);offline.on('pageerror',lambda e:errors.append(str(e)))
          offline.goto((ROOT/'ally-starter'/route).as_uri());requests.clear()
          if route!='stewardship-ceremony.html':
            field=offline.locator('textarea').first;field.fill('Synthetic ally project')
            with offline.expect_download() as event:offline.click('#export')
            target=out/(route+'.md');event.value.save_as(target);assert 'Synthetic ally project' in target.read_text()
            assert 'not verified execution' in target.read_text()
            offline.reload();assert offline.locator('textarea').first.input_value()==''
          else:
            offline.fill('#recipient','Offline ally');offline.check('#pledge');offline.locator('#ceremony-form button[type=submit]').click()
            with offline.expect_download() as event:offline.click('#save-certificate')
            event.value.save_as(out/'file-offline-keepsake.html')
          assert not requests,requests
          assert offline.evaluate('localStorage.length')==0 and offline.evaluate('sessionStorage.length')==0
          offline.close();record(route+': file-offline export, no network requests or automatic storage')
        geometry=[]
        routes=['ally.html','ally-soul-quiz.html','ally-setup.html','ally-stewardship.html','ally-starter/dashboard.html','ally-starter/mission-control.html','ally-starter/stewardship-ceremony.html']
        for width in [375,1280]:
          page.set_viewport_size({'width':width,'height':900})
          for route in routes:
            page.goto(base+route)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route)
            controls=page.locator('button,select,input[type=text],input[type=date],nav a').evaluate_all('(es)=>es.filter(e=>e.getClientRects().length).map(e=>({tag:e.tagName,height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width}))')
            assert all(x['height']>=44 and x['width']>=44 for x in controls),(width,route,controls)
            page.keyboard.press('Tab');focus=page.evaluate('getComputedStyle(document.activeElement).outlineStyle');assert focus!='none',(route,focus)
            contrast=page.evaluate('''() => {
              const rgb=s=>s.match(/[\\d.]+/g).slice(0,3).map(Number);
              const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
              const items=[];
              for(const e of document.querySelectorAll('p,h1,h2,h3,a,button,label,legend,li,summary')){
                if(!e.getClientRects().length || !e.textContent.trim())continue;
                let bg=e;while(bg && getComputedStyle(bg).backgroundColor==='rgba(0, 0, 0, 0)')bg=bg.parentElement;
                const c=getComputedStyle(e),a=lum(rgb(c.color)),b=lum(rgb(bg?getComputedStyle(bg).backgroundColor:'rgb(255,255,255)'));
                items.push({tag:e.tagName,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)});
              }
              return items;
            }''')
            assert all(x['ratio']>=4.5 for x in contrast),(route,contrast)
            checkbox_labels=page.locator('label:has(input[type=checkbox])').evaluate_all('(es)=>es.map(e=>({height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width}))')
            assert all(x['height']>=44 and x['width']>=44 for x in checkbox_labels)
            geometry.append({'width':width,'route':route,'controls':len(controls),'overflow':False,'focusOutline':focus,'minimumTextContrast':min(x['ratio'] for x in contrast),'checkboxLabels':checkbox_labels})
            if route in ['ally.html','ally-soul-quiz.html','ally-setup.html','ally-stewardship.html']:page.screenshot(path=str(out/(route.removesuffix('.html')+f'-{width}.png')),full_page=True)
        record('7 pages × 2 viewports: no overflow, measured controls >=44px, visible keyboard focus')
        assert not errors,errors;record('no JavaScript page errors')
        (out/'browser-results.json').write_text(json.dumps({'checks':log,'errors':errors,'geometry':geometry},indent=2))
        browser.close()
    finally:
      server.shutdown();server.server_close();thread.join()
    return log
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();run(a.evidence)
