"""Third-order Taylor remainder diagnostic for the DH boundary (Python 3)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import mpmath as mp

def dh(s):
    c=(mp.sqrt(10-2*mp.sqrt(5))-2)/(mp.sqrt(5)-1); a=[1,c,-c,-1,0]
    return 5**(-s)*sum(a[r-1]*mp.zeta(s,mp.mpf(r)/5) for r in range(1,6))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args(); mp.mp.dps=60
    src=json.loads(args.input.read_text(encoding='utf-8')); rows=[]
    for row in src['segments']:
        z=mp.mpc(mp.mpf(row['centre'][0]),mp.mpf(row['centre'][1])); h=mp.mpf(row['half_length']); f=dh(z)
        d1=mp.diff(dh,z); d2=mp.diff(dh,z,2); d3=mp.diff(dh,z,3)
        radius=abs(d1)*h+mp.mpf('.5')*abs(d2)*h*h+abs(d3)*h**3/mp.mpf(6)
        rows.append({'index':row['index'],'centre_abs':float(abs(f)),'d1_abs':float(abs(d1)),'d2_abs':float(abs(d2)),'d3_abs':float(abs(d3)),'radius':float(radius),'lower':float(abs(f)-radius),'phase_eps':float(mp.asin(min(mp.mpf('.999999999'),radius/abs(f))))})
    phase=2*sum(r['phase_eps'] for r in rows)
    result={'status':'NONCERTIFIED_THIRD_ORDER_TAYLOR_DIAGNOSTIC','input':str(args.input),'segments':len(rows),'positive_lower':sum(r['lower']>0 for r in rows),'minimum_lower':min(r['lower'] for r in rows),'phase_uncertainty_radius':float(phase),'winding_interval':[float(1-phase/(2*mp.pi)),float(1+phase/(2*mp.pi))],'interpretation':'Third-order centre Taylor radius is evaluated with sampled high-precision derivatives. The third derivative supremum and remainder are not interval-certified.','segments_detail':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':result['status'],'positive_lower':result['positive_lower'],'minimum_lower':result['minimum_lower'],'winding_interval':result['winding_interval'],'output':str(args.output)},ensure_ascii=False))
if __name__=='__main__': main()
