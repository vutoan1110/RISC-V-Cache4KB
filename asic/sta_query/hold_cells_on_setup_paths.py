"""2026-10-20 ss study: how many reported setup paths of a post-PnR STA report (max.rpt, report_checks -format full)
carry hold delay cells (dlygate* / dlymetal*), and how much delay they add.
    python hold_cells_on_setup_paths.py <max.rpt> [...]"""
import re
import sys

for path in sys.argv[1:]:
    paths, cur = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("Startpoint:"):
            cur = {"dly": 0.0, "n": 0}
        m = re.match(r"\s+\d+\s+[\d.]+\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s+[v^]\s+(\S+)\s+\((\S+)\)", line)
        if cur is not None and m and ("dlygate" in m.group(3) or "dlymetal" in m.group(3)):
            cur["dly"] += float(m.group(1))
            cur["n"] += 1
        if cur is not None and "slack (" in line:
            cur["slack"] = float(line.split()[0])
            paths.append(cur)
            cur = None
    with_d = [p for p in paths if p["n"]]
    print(f"{path}: {len(paths)} paths, worst {paths[0]['slack']:.3f}, {len(with_d)} with hold delay cells "
          f"(mean {sum(p['dly'] for p in with_d) / max(1, len(with_d)):.3f} ns), on the worst path {paths[0]['dly']:.3f} ns; "
          f"worst slack without them {max(p['slack'] + p['dly'] for p in paths[:1]):.3f}")
