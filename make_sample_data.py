"""Generates 40 realistic sample sessions (CSV + JSON) incl. boundary/edge cases."""
import csv, json, random
from datetime import date, timedelta
random.seed(7)
ACT = {"Walking":(3.5,25,70,4.5),"Running":(9,20,60,10),"Cycling":(7.5,30,120,18),
       "Swimming":(8,20,60,2),"Hiking":(6,90,240,5),"Yoga":(2.5,30,60,0),"Gym":(5,30,75,0)}
rows=[]
for i in range(36):
    a=random.choice(list(ACT)); met,lo,hi,spd=ACT[a]
    dur=random.randint(lo,hi); dist=round(spd*dur/60*random.uniform(.85,1.15),2)
    d=date.today()-timedelta(days=random.randint(0,34))
    rows.append([d.isoformat(),a,dur,dist,round(met*70*dur/60),"sample"])
rows+= [[date.today().isoformat(),"Walking",1,0,4,"boundary: min duration"],
        [date.today().isoformat(),"Hiking",600,50,2900,"boundary: max duration"],
        [(date.today()-timedelta(days=2)).isoformat(),"Walking",30,15,120,"edge: unrealistic speed"],
        [(date.today()-timedelta(days=3)).isoformat(),"Running",45,0,400,"edge: zero distance"]]
rows.sort()
h=["id","date","activity","duration_min","distance_km","calories","notes"]
rows=[[i+1,*r] for i,r in enumerate(rows)]
with open("sample_data/sample_sessions.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(h); w.writerows(rows)
json.dump([dict(zip(h,r)) for r in rows],open("sample_data/sample_sessions.json","w"),indent=2)
# bad rows for the import-error-log demo
open("sample_data/bad_rows.csv","w").write("date,activity,duration_min,distance_km,calories,notes\n"
 "2026-01-05,Walking,40,3.2,150,ok\n2099-01-01,Walking,30,2,100,future date\n"
 "2026-01-06,Dancing,30,0,100,bad activity\n2026-01-07,Running,abc,5,300,bad duration\n")
