"""content/dayNNN.json 형식 검사. 문제가 있으면 목록을 출력하고 종료 코드 1.
사용법: python check_content.py 2
"""
import json
import re
import sys
from pathlib import Path

ACCENTS = {"US", "GB", "AU", "CA"}
SPK = {"M", "W", "M2", "W2"}


def check(day_no):
    path = Path(__file__).parent / "content" / f"day{day_no:03d}.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    err = []

    def need(cond, msg):
        if not cond:
            err.append(msg)

    def text(obj, where, *keys):
        for k in keys:
            need(isinstance(obj.get(k), str) and obj[k].strip(), f"{where}: '{k}' 비어 있음")

    need(d.get("day") == day_no, f"day 값이 {day_no}가 아님")
    need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.get("date", "")), "date가 YYYY-MM-DD 형식이 아님")

    for i, it in enumerate(d.get("part2", []), 1):
        w = f"part2[{i}]"
        need(it.get("accent") in ACCENTS and it.get("spk") in {"M", "W"}, f"{w}: accent/spk")
        text(it.get("q", {}), w + ".q", "en", "ko")
        opts = it.get("options", [])
        need(len(opts) == 3, f"{w}: 보기는 3개")
        for o in opts:
            text(o, w + ".option", "en", "ko")
        need(it.get("answer") in "ABC" and it.get("answer"), f"{w}: answer는 A/B/C")

    for key, unit in (("part3", "lines"), ("part4", "paragraphs")):
        for i, st in enumerate(d.get(key, []), 1):
            w = f"{key}[{i}]"
            need(st.get("accent") in ACCENTS, f"{w}: accent")
            if key == "part4":
                need(st.get("spk") in {"M", "W"}, f"{w}: spk")
                text(st, w, "type_en")
            segs = st.get(unit, [])
            need(len(segs) >= 3, f"{w}: {unit} 3개 이상")
            for s in segs:
                text(s, f"{w}.{unit}", "en", "ko")
                if key == "part3":
                    need(s.get("spk") in SPK, f"{w}: spk {s.get('spk')}")
            qs = st.get("questions", [])
            need(len(qs) == 3, f"{w}: 문제는 3개")
            for q in qs:
                text(q, w + ".question", "en", "ko", "answer_ko")
                need(len(q.get("options", [])) == 4, f"{w}: 보기는 4개")
                need(q.get("answer") in "ABCD" and q.get("answer"), f"{w}: answer는 A~D")

    for v in d.get("vocab", []):
        text(v, "vocab", "word", "ko")
        need(re.fullmatch(r"[a-z][a-z \-]*", v.get("word", "")), f"vocab: '{v.get('word')}' 소문자 영어만")
    for i, a in enumerate(d.get("news", []), 1):
        text(a, f"news[{i}]", "title_en", "title_ko")
        need(len(a.get("paragraphs", [])) >= 3, f"news[{i}]: 문단 3개 이상")
        for p in a.get("paragraphs", []):
            text(p, f"news[{i}].paragraph", "en", "ko")

    counts = {k: len(d.get(k, [])) for k in ("part2", "part3", "part4", "vocab", "news")}
    need(counts["part2"] >= 12 and counts["part3"] >= 4 and counts["part4"] >= 3
         and counts["vocab"] >= 20 and counts["news"] >= 2, f"분량 부족: {counts}")
    return err, counts


if __name__ == "__main__":
    n = int(sys.argv[1])
    errors, counts = check(n)
    print(f"Day {n}: {counts}")
    for e in errors:
        print("  X", e)
    print("OK" if not errors else f"{len(errors)}개 문제")
    sys.exit(1 if errors else 0)
