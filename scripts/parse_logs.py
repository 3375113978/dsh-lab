# -*- coding: utf-8 -*-
# 从录屏文件名批量解析出「场景 - 耗时 - 得分」记录。
# 命名约定：单元/[场景描述][耗时][得分].mp4
#   例：固定床/反应器超温25秒99.5.mp4
#      流化床/流化床冷态开车12分半99.99.mp4
# 用法：python scripts/parse_logs.py <录屏根目录> > data/scenarios.csv
import os
import re
import csv
import sys

CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "两": 2}


def to_num(s):
    if s in CN:
        return CN[s]
    try:
        return float(s)
    except ValueError:
        return None


def parse(name):
    # 返回 (场景, 耗时秒, 得分)，无法解析的字段为 None
    score = None
    m = re.findall(r"(\d{2,3}(?:\.\d+)?)\s*$", name)
    if m:
        score = float(m[-1])

    secs = None
    m = re.search(r"(\d+|[一二三四五六七八九十两])分半", name)
    if m:
        v = to_num(m.group(1))
        if v is not None:
            secs = v * 60 + 30
    if secs is None:
        m = re.search(r"(\d+|[一二三四五六七八九十两])分(?:钟)?(\d+)?", name)
        if m:
            v = to_num(m.group(1))
            if v is not None:
                secs = v * 60 + (float(m.group(2)) if m.group(2) else 0)
    if secs is None:
        m = re.search(r"(\d+)秒", name)
        if m:
            secs = float(m.group(1))

    scenario = re.sub(r"(\d+|[一二三四五六七八九十两])分半|\d+分\d*秒?|\d+分(?:钟)?|\d+秒", "", name)
    scenario = re.sub(r"\d{2,3}(\.\d+)?\s*$", "", scenario).strip(" _-")
    return scenario or name, secs, score


def main(root, out_path=None):
    rows = []
    for unit in sorted(os.listdir(root)):
        unit_dir = os.path.join(root, unit)
        if not os.path.isdir(unit_dir):
            continue
        for dirpath, _, files in os.walk(unit_dir):
            for f in files:
                if not f.lower().endswith((".mp4", ".avi", ".mov")):
                    continue
                scenario, secs, score = parse(os.path.splitext(f)[0])
                if secs is None or score is None:
                    continue
                rows.append([unit, scenario, int(secs), score])
    rows.sort(key=lambda r: (r[0], r[2]))

    header = ["单元", "场景", "耗时(秒)", "得分"]
    if out_path:
        with open(out_path, "w", encoding="utf-8-sig", newline="") as fp:
            w = csv.writer(fp)
            w.writerow(header)
            w.writerows(rows)
        print("written %d rows -> %s" % (len(rows), out_path))
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(newline="")
        w = csv.writer(sys.stdout)
        w.writerow(header)
        w.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/parse_logs.py <录屏根目录>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
