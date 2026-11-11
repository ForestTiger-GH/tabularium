#!/usr/bin/env python3
"""Development-only comparison of two confirmed FNS coverage/code breaks."""
import csv
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

BASE=Path("flakes/organizations/legal-entity-population")
OUT=Path("_mw/work/fns-1yur-series-audit-2026-11-11")
OUT.mkdir(parents=True,exist_ok=True)
BG="#0b1122";AX="#142038";FG="#e8f1fa";MUTED="#a4b3c8"
plt.rcParams.update({"font.family":"DejaVu Sans","figure.facecolor":BG,
                     "axes.facecolor":AX,"savefig.facecolor":BG,
                     "text.color":FG,"axes.labelcolor":FG,
                     "xtick.color":MUTED,"ytick.color":MUTED,
                     "axes.edgecolor":"#33435b","grid.color":"#33435b"})
def load(day):
 path=BASE/day[:4]/(day+"_1-YUR.csv")
 with path.open("r",encoding="utf-8",newline="") as f:
  items=list(csv.DictReader(f))
  header=list(items[0])
 return header,items
def month_dates(startyear,startmonth,endyear,endmonth):
 for y in range(startyear,endyear+1):
  for m in range(1,13):
   if (y,m)<(startyear,startmonth) or (y,m)>(endyear,endmonth):continue
   yield f"{y}-{m:02d}-01"
def national(rows,key):
 r=[x for x in rows if x["region_name"].strip()=="Российская Федерация"]
 assert len(r)==1
 return int(r[0][key])
def fstyle(ax):
 ax.grid(alpha=.55);ax.set_axisbelow(True);ax.tick_params(length=0)
 for sp in ax.spines.values():sp.set_visible(False)
 ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
 ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%Y"))
 ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_:f"{y/1e6:.3f} M" if y>1e6 else f"{y/1e3:.0f} k"))
fig,ax=plt.subplots(2,1,figsize=(16.6,10.7),dpi=155)

dates=[];reported=[];adjusted=[]
for d in month_dates(2022,8,2023,9):
 header,rows=load(d)
 level=national(rows,"le_not_ceased__all")
 newcomers=[r for r in rows if r["region_code"] in ("90","93","94","95")]
 amount=sum(int(r["le_not_ceased__all"]) for r in newcomers)
 if d=="2023-02-01":assert len(newcomers)==4 and amount==31805
 dates.append(datetime.strptime(d,"%Y-%m-%d"))
 reported.append(level)
 adjusted.append(level-amount)
ax[0].plot(dates,reported,color="#71d2ee",lw=2.8,marker="o",markersize=3,
           label="Publisher's Russian Federation total")
ax[0].plot(dates,adjusted,color="#ffc47b",ls="--",lw=2.3,
           label="Derived: national total excluding four additional territories")
ax[0].axvline(datetime(2023,2,1),color="#ff7a8b",ls=":",lw=1.3)
ax[0].annotate("February 2023: +4 territorial rows / 31,805 entities",
 xy=(datetime(2023,2,1),3227373),xytext=(datetime(2022,8,1),3243000),
 arrowprops={"arrowstyle":"->","color":"#f4d1a3"},color="#f4d1a3",
 fontsize=11)
ax[0].set_title("2023: change in published territorial perimeter",loc="left",fontsize=18,pad=16)
ax[0].legend(facecolor=AX,labelcolor=FG,fontsize=9,loc="lower right")
fstyle(ax[0])
ax[0].text(.005,.02,"January: 3,197,542; February: 3,227,373 (+29,831); excluding new rows: -1,974.",
 transform=ax[0].transAxes,color=MUTED,fontsize=9.5)

ds1=[];vs1=[];ds2=[];vs2=[]
for day in month_dates(2018,10,2019,8):
 header,rows=load(day)
 key="le_ceased_bankruptcy_liquidation__all"
 v=national(rows,key)
 if day < "2019-03-01":
  ds1.append(datetime.strptime(day,"%Y-%m-%d"));vs1.append(v)
 else:
  ds2.append(datetime.strptime(day,"%Y-%m-%d"));vs2.append(v)
assert vs1[-1]==249949 and vs2[0]==227557
ax[1].plot(ds1,vs1,color="#72dfba",lw=2.8,marker="o",markersize=4,label="Original edition: c11_1010")
ax[1].plot(ds2,vs2,color="#77b1ff",lw=2.8,marker="o",markersize=4,label="Next edition: c12_1000")
ax[1].axvline(datetime(2019,3,1),color="#ff7a8b",ls=":",lw=1.3)
ax[1].annotate("Source code change: 249,949 → 227,557 (-8.96%)",
 xy=(datetime(2019,3,1),227557),xytext=(datetime(2018,12,1),237000),
 arrowprops={"arrowstyle":"->","color":"#f4d1a3"},color="#f4d1a3",fontsize=10)
ax[1].set_title("2019: bankruptcy cessation source-code discontinuity",
                loc="left",fontsize=17,pad=16)
ax[1].legend(facecolor=AX,labelcolor=FG,fontsize=9,loc="lower right")
fstyle(ax[1])
fig.suptitle("Two source breaks that cannot be treated as economic shocks",
             fontsize=20,x=.07,ha="left",weight="bold")
fig.text(.07,.023,
 "The 2023 dashed series is an explicit analytical subtraction, not a reported FNS observation.",
 color=MUTED,fontsize=10)
fig.subplots_adjust(left=.075,right=.985,top=.91,bottom=.085,hspace=.31)
fig.savefig(OUT/"06_confirmed_source_breaks.png",dpi=155,facecolor=BG)
plt.close(fig)
print("FNS_BROKEN_SERIES_QA_OK: 2023 territorial +31805, national +29831; 2019 bankruptcy 249949 -> 227557")
