#!/usr/bin/env python3
"""Temporary read-only probe: official FNS 1-YUR historical links and formats."""
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit
from datetime import datetime
import re
import sys

INDEX="https://www.nalog.gov.ru/rn77/related_activities/statistics_and_analytics/forms/"
class Index(HTMLParser):
    def __init__(self):
        super().__init__();self.is_tr=False;self.href=None;self.links=[];self.txt=[];self.rows=[]
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.is_tr=True;self.links=[];self.txt=[]
        if tag=="a" and self.is_tr:self.href=dict(attrs).get("href");self.cur=[]
    def handle_data(self,data):
        if self.is_tr:self.txt.append(data)
        if self.href is not None:self.cur.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.links.append((self.href,"".join(self.cur).strip()));self.href=None
        if tag=="tr" and self.is_tr:
            self.rows.append((" ".join(self.txt),self.links[:]))
            self.is_tr=False
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.li=0;self.text=[];self.links=[];self.rows=[];self.href=None
    def handle_starttag(self,tag,attrs):
        if tag=="li":self.li+=1
        if tag=="a" and self.li and self.href is None:self.href=dict(attrs).get("href");self.curr=[]
    def handle_data(self,data):
        if self.li:self.text.append(data)
        if self.href is not None:self.curr.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:self.links.append((self.href,"".join(self.curr)));self.href=None
        if tag=="li" and self.li:
            self.li-=1
            if not self.li:
                self.rows.append((" ".join(self.text),self.links[:]))
                self.text=[];self.links=[]
def get(url):
    with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30) as r:
        data=r.read(4_000_000);print("HTTP",r.status,len(data),r.url)
    return data.decode("utf-8-sig",errors="replace")
s=Index();s.feed(get(INDEX))
rows=[x for x in s.rows if re.search(r"(?<![0-9a-z])1\s*[-–]\s*ЮР",x[0],re.I)]
print("INDEX_MATCHING_ROWS",len(rows))
for text,links in rows:
    print("INDEX_ROW",repr(text[:240]),"LINKS",len(links))
    for url,label in links:
        if re.fullmatch(r"20(1[2-9]|2[0-6])",label.strip()):
            print("YEAR_LINK",label.strip(),urljoin(INDEX,url))
for year in (2012,2013,2014,2016,2018,2020,2022,2024,2025,2026):
    url={2012:"4171842",2014:"4558837",2022:"11892431",2024:"14414858",2025:"15764462",2026:"16601803"}.get(year)
    if not url:
        # Reference the authoritative index, never fabricate annual page IDs.
        candidates=[urljoin(INDEX,href) for _,links in rows for href,label in links if label.strip()==str(year)]
        if len(candidates)!=1:print("YEAR_UNKNOWN",year,candidates);continue
        page_url=candidates[0]
    else:
        page_url=INDEX+url+"/"
    try:
        raw=get(page_url)
        for needle in ("01.01.2012", "01.12.2012", "01.11.2026", "01.01.2026"):
            i=raw.find(needle)
            if i>=0:print("HTML_DATE_SNIPPET",year,needle,repr(raw[max(0,i-180):i+350]))
        p=Page();p.feed(raw)
        print("YEAR",year,"ROWS",len(p.rows))
        for txt,links in (p.rows[:3]+p.rows[-2:]):
            print("RELEASE",repr(txt[:160]),[(href,label.strip()) for href,label in links[:2]])
    except Exception as exc:print("YEAR_FAIL",year,type(exc).__name__,str(exc)[:200])


# Source-shape reconnaissance; no corpus writes.
import io, zipfile, subprocess, tempfile, os, pathlib
import xlrd
def get_bytes(url,limit=30_000_000):
    with urlopen(Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=40) as resp:
        data=resp.read(limit+1);print("FETCH",resp.status,len(data),url[:170]);return data
for year in (2012,2013,2014,2016,2018,2020,2022,2024,2025,2026):
    yid={2012:"4171842",2013:"4161934",2014:"4558837",2016:"5953348",2018:"7243238",2020:"9558929",2022:"11892431",2024:"14414858",2025:"15764462",2026:"16601803"}[year]
    url=INDEX+yid+"/"
    try:
        q=Page();q.feed(get(url))
        choices=[]
        for label,links in q.rows:
            m=re.search(r"(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(20\d\d)",label)
            if not m:continue
            for href,a in links:
                href=href.strip()
                if re.search(r"\.(xls|rar|zip)$",href,re.I):choices.append((m.group(),urljoin(url,href)))
        print("RELEASES_YEAR",year,len(choices),[(a,b.split("/")[-1]) for a,b in choices[:2]])
        if not choices:continue
        d,asset=choices[0] if year!=2026 else next((x for x in choices if x[0]=='01.11.2026'),choices[0])
        body=get_bytes(asset)
        suff=asset.lower().split(".")[-1]
        xls=None
        if suff=="xls":xls=body;print("DIRECT_XLS",year,len(body))
        elif suff=="zip":
            with zipfile.ZipFile(io.BytesIO(body)) as z:
                names=z.namelist();print("ZIP_NAMES",year,names[:12])
                options=[n for n in names if n.lower().endswith("(1).xls")]
                if not options:options=[n for n in names if n.lower().endswith("_i.xls")]
                if len(options)==1:xls=z.read(options[0])
                elif len(names)==1 and names[0].lower().endswith('.xls'):xls=z.read(names[0])
        elif suff=="rar":
            print("RAR_HEADER",year,body[:12].hex())
            with tempfile.TemporaryDirectory() as t:
                pth=pathlib.Path(t)/"archive.rar";pth.write_bytes(body)
                try:
                    c=subprocess.run(["bsdtar","-tf",str(pth)],capture_output=True,text=True,timeout=15)
                    print("RAR_MEMBERS",year,c.returncode,c.stdout[:1000],c.stderr[:120])
                    members=[x for x in c.stdout.splitlines() if x.lower().endswith(".xls")]
                    if c.returncode==0 and len(members)==1:
                        out=subprocess.run(["bsdtar","-xOf",str(pth),members[0]],capture_output=True,timeout=20)
                        if out.returncode==0:xls=out.stdout;print("RAR_EXTRACTED",year,members[0],len(xls))
                except Exception as exc:print("RAR_TOOL_UNAVAILABLE",type(exc).__name__)
        if xls:
            if not xls.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
                print("NOT_OLE",year,xls[:20].hex());continue
            book=xlrd.open_workbook(file_contents=xls,on_demand=True)
            print("SHEET_SHAPE",year,len(book.sheet_names()),book.sheet_names()[:12],
                  "codes",[n for n in book.sheet_names() if re.fullmatch(r"[0-9]{4}",n)][:45])
            sh=book.sheet_by_name("1000") if "1000" in book.sheet_names() else book.sheet_by_index(0)
            for row in range(min(14,sh.nrows)):
                print("SHEET_HEAD",year,row+1,[str(sh.cell_value(row,c))[:70] for c in range(min(6,sh.ncols))],
                     "indicatorcols",[(i,str(sh.cell_value(row,i))[:18]) for i in (2,9,13) if i<sh.ncols])
            if year==2026:
                ns=book.sheet_by_name("Российская Федерация")
                for row in range(min(80,ns.nrows)):
                    print("NATIONAL_CATEGORY",row+1,[str(ns.cell_value(row,c))[:160] for c in range(min(4,ns.ncols))])
            book.release_resources()
    except Exception as exc:print("INSPECT_FAILED",year,type(exc).__name__,str(exc)[:250])
