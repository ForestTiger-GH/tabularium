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
        p=Page();p.feed(get(page_url))
        print("YEAR",year,"ROWS",len(p.rows))
        for txt,links in (p.rows[:3]+p.rows[-2:]):
            print("RELEASE",repr(txt[:160]),[(href,label.strip()) for href,label in links[:2]])
    except Exception as exc:print("YEAR_FAIL",year,type(exc).__name__,str(exc)[:200])
