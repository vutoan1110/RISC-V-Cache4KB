import json, os, re, sys
def last_state(run, upto=None):
    steps = sorted((d for d in os.listdir(run) if re.match(r"^\d+-", d)), key=lambda d: int(d.split("-")[0]))
    best = None
    for d in steps:
        if upto and re.search(upto, d):
            p = os.path.join(run, d, "state_out.json")
            if os.path.exists(p):
                return d, json.load(open(p))["metrics"]
        p = os.path.join(run, d, "state_out.json")
        if os.path.exists(p):
            best = (d, p)
    return best[0], json.load(open(best[1]))["metrics"]
runs = sys.argv[1].split(",")
upto = sys.argv[2] if len(sys.argv) > 2 else None
data = {}
for r in runs:
    d, m = last_state(r, upto)
    data[r] = m
    print(f"# {r}: {d}")
pat = re.compile(r"^(design__instance__(area|count)(__stdcell|__class:.*|__hold_buffer|__setup_buffer)?$|power__(total|internal__total|switching__total|leakage__total)$|route__wirelength$|design__die__area$|design__instance__utilization__stdcell$)")
keys = sorted({k for m in data.values() for k in m if pat.match(k)})
print(f"{'metric':52s}" + "".join(f"{r:>14s}" for r in runs))
for k in keys:
    print(f"{k:52s}" + "".join(f"{data[r].get(k, float('nan')):14.5g}" if isinstance(data[r].get(k), (int, float)) else f"{'-':>14s}" for r in runs))
