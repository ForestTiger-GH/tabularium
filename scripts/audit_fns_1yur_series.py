#!/usr/bin/env python3
"""Reproducible development-layer visual QA for 2012-2026 FNS 1-YUR evidence."""
from collections import defaultdict, Counter
import csv
from datetime import datetime
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import fns_1yur_semantics as semantic

BASE=Path("scrolls/russia/authorities/federal-tax-service/legal-entity-registration")
OUT=Path("_mw/work/fns-1yur-series-audit-2026-11-11")
OUT.mkdir(parents=True,exist_ok=True)
REGIONS=[
 ("77","Moscow"),("78","Saint Petersburg"),("50","Moscow Oblast"),
 ("23","Krasnodar Krai"),("16","Tatarstan"),("66","Sverdlovsk Oblast"),
 ("02","Bashkortostan"),("52","Nizhny Novgorod Oblast"),("54","Novosibirsk Oblast"),
 ("61","Rostov Oblast"),("24","Krasnoyarsk Krai"),("63","Samara Oblast")]
COLUMNS={
 "total":("le_not_ceased__all",),
 "status":("le_bankruptcy_proceedings__all",),
 "ceased":("le_ceased_bankruptcy_liquidation__all",)}
TITLES={
 "total":"Legal entities with no registered cessation",
 "status":"Legal entities in bankruptcy proceedings",
 "ceased":"Legal entities ceased through bankruptcy"}
COLORS={"total":"#69d1e8","status":"#ffbb72","ceased":"#70dfbb"}
BG="#0b1122";PANEL="#142038";INK="#e8f1fa";MUTED="#9bacc3";GRID="#34445b"
plt.rcParams.update({"font.family":"DejaVu Sans","figure.facecolor":BG,
 "axes.facecolor":PANEL,"savefig.facecolor":BG,"text.color":INK,
 "axes.labelcolor":INK,"xtick.color":MUTED,"ytick.color":MUTED,
 "axes.edgecolor":GRID,"font.size":10,"grid.color":GRID})

def month_index(d):return d.year*12+d.month
def file_rows(path):
 with path.open("r",encoding="utf-8",newline="") as stream:
  reader=csv.DictReader(stream);header=reader.fieldnames;rows=list(reader)
 if header[:2]!=["region_code","region_name"]:raise ValueError("SCHEMA:"+str(path))
 return header,rows
def choose(rows,code):
 matches=[r for r in rows if r["region_code"]==code]
 if code=="":
  matches=[r for r in matches if r["region_name"].strip().casefold()=="российская федерация"]
 if code=="50":
  matches=[r for r in matches if r["region_name"].strip().casefold()=="московская область"]
 if len(matches)!=1:raise ValueError("GEOGRAPHIC_SCOPE:"+code+":"+str(len(matches)))
 return matches[0]
def exact_number(row,key):
 if key is None:return None
 raw=row[key]
 if raw is None or raw=="":return None
 if not raw.isdecimal():raise ValueError("NON_NUMERIC:"+key+":"+raw)
 return int(raw)
series=[]
for path in sorted(BASE.glob("*/*_1-YUR.csv")):
 header,rows=file_rows(path)
 day=datetime.strptime(path.name[:10],"%Y-%m-%d")
 keys={}
 for metric,candidates in COLUMNS.items():
  found=[candidate for candidate in candidates if candidate in header]
  if len(found)>1:raise ValueError("MULTIPLE_TOTAL_FIELDS:"+str(path)+":"+str(found))
  keys[metric]=found[0] if found else None
 if keys["total"] is None or keys["ceased"] is None:
  raise ValueError("MISSING_SOURCE_TOTAL:"+str(path))
 geos={"RU":choose(rows,"")}
 for code,label in REGIONS:geos[code]=choose(rows,code)
 vals={key:{metric:exact_number(row,field) for metric,field in keys.items()}
       for key,row in geos.items()}
 series.append({"date":day,"reference_date":day.strftime("%Y-%m-%d"),
  "epoch":semantic.epoch(day.date()),
  "fields":keys,"values":vals,"rows":len(rows),
  "geographic_names":{code:row["region_name"] for code,row in geos.items()}})
if len(series)!=178:raise ValueError("UNEXPECTED_MONTH_COUNT:"+str(len(series)))
D=[s["date"] for s in series]

def segments(code,metric):
 result=[];current=[];prev_field=None;prev_epoch=None;prev_month=None
 for i,s in enumerate(series):
  field=s["fields"][metric];v=s["values"][code][metric];month=month_index(s["date"])
  national_boundary=(code=="RU" and s["reference_date"]=="2023-02-01")
  if (v is None or field!=prev_field or s["epoch"]!=prev_epoch or
      national_boundary or (prev_month is not None and month!=prev_month+1)):
   if current:result.append(current);current=[]
  if v is not None:current.append((s["date"],v))
  prev_field=field;prev_epoch=s["epoch"]
  prev_month=month if v is not None else None
 if current:result.append(current)
 return result

def format_axis(ax):
 ax.grid(True,linewidth=.6,alpha=.55);ax.set_axisbelow(True)
 for spine in ax.spines.values():spine.set_visible(False)
 ax.tick_params(length=0,labelsize=8)
 ax.xaxis.set_major_locator(mdates.YearLocator(3))
 ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
 ax.set_xlim(datetime(2011,11,1),datetime(2027,1,1))
 ax.yaxis.set_major_formatter(FuncFormatter(
  lambda y,_:("{:.1f} M".format(y/1e6) if y>=1e6 else
              "{:.0f} k".format(y/1e3) if y>=10000 else "{:.0f}".format(y))))
 ax.margins(y=.08)
def source_boundaries(ax,metric):
 prior=None
 for s in series:
  key=(s["epoch"],s["fields"][metric])
  if prior is not None and key!=prior:
   ax.axvline(s["date"],lw=.75,ls="--",alpha=.65,color="#fb7c91")
  prior=key
def chart(metric,path):
 fig,axes=plt.subplots(4,3,figsize=(17.5,15.2),dpi=145)
 for ax,(code,label) in zip(axes.flat,REGIONS):
  for seg in segments(code,metric):
   xx=[a for a,b in seg];yy=[b for a,b in seg]
   if len(seg)==1:ax.scatter(xx,yy,s=16,color=COLORS[metric])
   else:ax.plot(xx,yy,lw=1.8,color=COLORS[metric])
  source_boundaries(ax,metric)
  ax.set_title(label,loc="left",fontweight="bold",fontsize=12,pad=10)
  format_axis(ax)
 subtitles={
  "total":"Historical 1010 / modern 1000 is a reported-value alias, not proof of identical methodology.",
  "status":"Only published status values are shown; missing is not zero.",
  "ceased":"FNS Part I bankruptcy cessation stock; original indicator numbers varied."}
 fig.suptitle(TITLES[metric],fontsize=23,x=.048,y=.991,ha="left",fontweight="bold")
 fig.text(.048,.968,subtitles[metric],color=MUTED,fontsize=10.5,ha="left")
 fig.text(.048,.015,"Pink dashed lines mark source-method epochs; lines are not connected across methodological boundaries.",
          fontsize=9,color=MUTED)
 fig.subplots_adjust(top=.927,bottom=.065,left=.052,right=.988,hspace=.38,wspace=.22)
 fig.savefig(OUT/path,dpi=145,facecolor=BG);plt.close(fig)
chart("total","01_legal_entities_regions.png")
chart("status","02_bankruptcy_status_regions.png")
chart("ceased","03_bankruptcy_cessation_regions.png")

# Only same published field, consecutive months: analytical month-on-month QA.
matrix=np.full((len(REGIONS),len(series)),np.nan)
changes=[]
for code,label in [("RU","Russia")]+REGIONS:
 for metric in ("total","status","ceased"):
  for i in range(1,len(series)):
   a,b=series[i-1],series[i]
   av=a["values"][code][metric];bv=b["values"][code][metric]
   same_field=(a["fields"][metric]==b["fields"][metric] and
               a["epoch"]==b["epoch"])
   contiguous=month_index(b["date"])==month_index(a["date"])+1
   if av is not None and av>0 and bv is not None and same_field and contiguous:
    pct=100*(bv/av-1)
    row={"region":label,"code":code,"metric":metric,"field":b["fields"][metric],
         "date":b["reference_date"],"previous":av,"current":bv,
         "monthly_change_pct":round(pct,3)}
    changes.append(row)
    if metric=="total" and code!="RU":
     k=next(k for k,r in enumerate(REGIONS) if r[0]==code)
     matrix[k,i]=pct
fig,ax=plt.subplots(figsize=(19,7.5),dpi=150)
cmap=plt.get_cmap("coolwarm").copy();cmap.set_bad(color="#26354a")
heat=ax.imshow(np.ma.masked_invalid(matrix),vmin=-7,vmax=7,
               cmap=cmap,aspect="auto",interpolation="nearest")
ax.set_yticks(range(len(REGIONS)))
ax.set_yticklabels([n for c,n in REGIONS],fontsize=11)
xticks=[i for i,s in enumerate(series) if s["date"].month==1]
ax.set_xticks(xticks);ax.set_xticklabels([series[i]["date"].strftime("%Y") for i in xticks])
for i in xticks:ax.axvline(i-.5,color=INK,linewidth=.5,alpha=.19)
ax.set_title("Month-on-month change in legal entities, %",fontsize=22,loc="left",pad=18)
ax.set_xlabel("Grey cells: missing month or source epoch boundary",color=MUTED,labelpad=10)
bar=fig.colorbar(heat,ax=ax,orientation="horizontal",fraction=.052,pad=.14,aspect=55)
bar.set_label("Month-on-month change, visualization capped at ±7%")
fig.subplots_adjust(left=.16,right=.987,top=.9,bottom=.14)
fig.savefig(OUT/"04_mom_changes_heatmap.png",dpi=150,facecolor=BG);plt.close(fig)

fig,axes=plt.subplots(2,1,figsize=(17,9),dpi=150)
for ax,metric in zip(axes,("total","ceased")):
 for seg in segments("RU",metric):
  if len(seg)>1:ax.plot(*zip(*seg),lw=2.3,color=COLORS[metric])
 source_boundaries(ax,metric)
 ax.axvline(datetime(2023,2,1),color="#ffd067",ls=":",lw=1.4)
 ax.set_title("Российская Федерация: "+TITLES[metric],loc="left",fontsize=15,pad=12)
 format_axis(ax)
 ax.xaxis.set_major_locator(mdates.YearLocator(1))
fig.suptitle("Reported Russian Federation total rows",fontsize=22,ha="left",x=.07)
fig.text(.07,.023,"The national total is the publisher's row; no territorial sums were substituted.",
         color=MUTED,fontsize=10)
fig.subplots_adjust(left=.07,right=.98,top=.89,bottom=.08,hspace=.28)
fig.savefig(OUT/"05_russia_totals.png",dpi=150,facecolor=BG);plt.close(fig)

shocks=sorted((x for x in changes if abs(x["monthly_change_pct"])>=
               {"total":3,"status":18,"ceased":7}[x["metric"]]),
              key=lambda x:-abs(x["monthly_change_pct"]))
descents=[x for x in changes if x["metric"]=="ceased" and x["monthly_change_pct"]<0]
transitions=defaultdict(list)
for metric in COLUMNS:
 prior=None
 for s in series:
  field=(s["epoch"],s["fields"][metric])
  if field!=prior:
   transitions[metric].append([s["reference_date"],"epoch "+field[0]+": "+str(field[1])])
   prior=field
levels={}
for code,label in REGIONS:
 levels[label]={}
 for metric in COLUMNS:
  found=[(s["reference_date"],s["values"][code][metric]) for s in series
         if s["values"][code][metric] is not None]
  levels[label][metric]={"first":found[0] if found else None,
                         "last":found[-1] if found else None,
                         "observations":len(found)}
qa={"source_releases":len(series),"geographic_rows":sum(s["rows"] for s in series),
    "metric_field_transitions":transitions,"monthly_shocks":shocks,
    "bankruptcy_cessation_declines":descents,
    "major_region_levels":levels,"source_months_per_year":dict(
     sorted(Counter(s["date"].year for s in series).items()))}
(OUT/"qa_observations.json").write_text(
 json.dumps(qa,ensure_ascii=False,indent=2),encoding="utf-8")
report=[
 "# FNS 1-YUR: monthly 2012–2026 regional series QA",
 "",
 "Development-layer, exploratory observation; not a replacement or correction of source evidence.",
 "178 dated source CSVs. The missing July 2015 publication is not imputed.",
 "All source values are unchanged; metric-code crosswalk is an analytical interpretation only.",
 "",
 "## Plots",
 "",
 "- [Major regions: non-ceased legal entities](01_legal_entities_regions.png)",
 "- [Major regions: bankruptcy proceedings](02_bankruptcy_status_regions.png)",
 "- [Major regions: ceased via bankruptcy](03_bankruptcy_cessation_regions.png)",
 "- [Monthly stock changes (heatmap)](04_mom_changes_heatmap.png)",
 "- [Russian Federation: original national rows](05_russia_totals.png)",
 "- [Confirmed 2019 and 2023 source-break checks](06_confirmed_source_breaks.png)",
 "",
 "## Source-methodology epoch transitions",
 ""]
for metric,groups in transitions.items():
 report.append("- "+metric+": "+", ".join(date+": "+str(field) for date,field in groups))
report+=["",
 "## Known changes in source coverage",
 "",
 "2023-02: the FNS geographic perimeter changes from 93 to 97 rows. The"
 " new source codes 90, 93, 94 and 95 report 31,805 legal entities combined."
 " The national level changes 3,197,542 to 3,227,373 (+29,831);"
 " excluding the four newly appearing territory rows gives -1,974."
 " This is a derived perimeter check, not a source-adjusted series.",
 "",
 "2019-03: source classification changes from c01_1010 to c01_1000,"
 " and bankruptcy cessation changes from c11_1010 (249,949) to"
 " c12_1000 (227,557), a nominal -8.96% discontinuity."
 " This cannot be interpreted as the actual disappearance of past bankruptcies.",
 ""]
report+=["","## Largest within-source monthly shocks",
 "", "| Region | Metric | Date | Before | After | Change |",
 "| --- | --- | --- | ---: | ---: | ---: |"]
for x in shocks[:45]:
 report.append("| {region} | {field} | {date} | {previous:,} | {current:,} | {monthly_change_pct:+.2f}% |".format(**x))
report+=["",
 "## Interpretation boundaries",
 "",
 "- Canonical aliases do not prove uniform economic constructs across A, B, C1, C2 and C3 source-method epochs. The source column lineage remains in field-provenance.json.",
 "- In 2019-06, only complete overall-kind categories are retained; missing category fields are absent, not zero.",
 "- Moscow Oblast uses the uncombined row, not the source line including Baikonur.",
 "- A gap in source bankruptcy-status reporting is not a zero. Some historical kinds have no bankruptcy columns.",
 "- Changes in the geographic source name do not automatically establish changed territorial perimeter.",
 "- Source national/district rows are not summed with constituent subjects.",
 "- Only month-on-month changes within the same source-method epoch are ranked; jumps across epoch boundaries are excluded.",
 ""]
(OUT/"README.md").write_text("\n".join(report),encoding="utf-8")
print("FNS_SERIES_AUDIT_SUMMARY",json.dumps({
 "dates":len(series),"rows":qa["geographic_rows"],
 "all_metric_transitions":transitions,"biggest_shocks":shocks[:14],
 "source_cessation_declines":len(descents),
 "plots":sorted(x.name for x in OUT.glob("*.png"))
},ensure_ascii=False))
