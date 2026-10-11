"""토익 리스닝 일일 MP3 생성기.

content/dayNNN.json 을 읽어 audio/dayNNN/ 에 챕터별 MP3와 전체 MP3를 만든다.
사용법:  tools\\python\\python.exe build_audio.py 1      (Day 1)
"""
import asyncio
import hashlib
import json
import struct
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).parent
CACHE = ROOT / "cache"

KO = "ko-KR-SunHiNeural"          # 안내 / 해석
NARR = "en-US-AriaNeural"         # 영어 문제 낭독
VOICES = {                        # 토익처럼 미국/영국/호주/캐나다 발음
    "US": {"M": "en-US-GuyNeural", "W": "en-US-JennyNeural"},
    "GB": {"M": "en-GB-RyanNeural", "W": "en-GB-SoniaNeural"},
    "AU": {"M": "en-AU-WilliamMultilingualNeural", "W": "en-AU-NatashaNeural"},
    "CA": {"M": "en-CA-LiamNeural", "W": "en-CA-ClaraNeural"},
}
SECOND = {"US": "CA", "GB": "AU", "AU": "US", "CA": "GB"}  # 3인 대화의 두 번째 남/여
LETTERS = "ABCD"

# edge-tts 출력 포맷(MPEG-2 Layer III, 24kHz, 48kbps, mono)과 같은 무음 프레임 (24ms)
SILENT_FRAME = bytes([0xFF, 0xF3, 0x64, 0xC4]) + bytes(140)
FRAME_SEC = 576 / 24000


def voice(accent, spk):
    if spk.endswith("2"):
        return VOICES[SECOND[accent]][spk[0]]
    return VOICES[accent][spk]


class Track:
    def __init__(self, title):
        self.title = title
        self.short = title.split(" ", 4)[-1]  # "Day 1 - 01 Part 2 ..." -> "Part 2 ..."
        self.items = []  # (voice, text) 또는 float(무음 초)

    def say(self, v, text, pause=0.6):
        self.items.append((v, text))
        if pause:
            self.items.append(pause)

    def ko(self, text, pause=0.6):
        self.say(KO, text, pause)

    def wait(self, sec):
        self.items.append(sec)


def read_question(t, n, q):
    t.say(NARR, f"Question {n}. {q['en']}", 1.0)
    for i, opt in enumerate(q["options"]):
        t.say(NARR, f"{LETTERS[i]}. {opt}", 0.7)
    t.wait(1.5)


def answer_question(t, n, q):
    idx = LETTERS.index(q["answer"])
    t.ko(f"{n}번. {q['ko']} 정답은 {q['answer']}.", 0.4)
    t.say(NARR, q["options"][idx], 0.4)
    t.ko(q["answer_ko"], 1.0)


def build_tracks(day):
    d = day["day"]
    tracks = []

    # ---------- Part 2 ----------
    t = Track(f"Day {d} - 01 Part 2 응답 고르기")
    t.ko(f"토익 리스닝 데이 {d}를 시작합니다. 오늘은 파트 2, 파트 3, 파트 4, 오늘의 단어, "
         "그리고 영어 뉴스 순서로 진행됩니다. 화면은 보지 마시고 소리에만 집중하세요. 안전 운전하세요.", 1.5)
    t.ko("파트 2. 질문을 듣고 가장 알맞은 응답을 고르세요.", 1.5)
    for n, it in enumerate(day["part2"], 1):
        qv = voice(it["accent"], it["spk"])
        av = voice(it["accent"], "W" if it["spk"] == "M" else "M")
        t.ko(f"{n}번.", 0.5)
        t.say(qv, it["q"]["en"], 1.0)
        for i, opt in enumerate(it["options"]):
            t.say(av, f"{LETTERS[i]}. {opt['en']}", 0.8)
        t.wait(3.0)
        t.ko(f"정답은 {it['answer']}입니다. 다시 듣고 해석합니다.", 0.8)
        t.say(qv, it["q"]["en"], 0.4)
        t.ko(it["q"]["ko"], 0.8)
        for i, opt in enumerate(it["options"]):
            mark = " 정답." if LETTERS[i] == it["answer"] else ""
            t.say(av, f"{LETTERS[i]}. {opt['en']}", 0.4)
            t.ko(f"{opt['ko']}{mark}", 0.7)
        t.wait(1.5)
    tracks.append(t)

    # ---------- Part 3 / Part 4 ----------
    for part, key, label in ((3, "part3", "대화"), (4, "part4", "담화")):
        t = Track(f"Day {d} - 0{part - 1} Part {part} 짧은 {label}")
        t.ko(f"파트 {part}. 짧은 {label}를 듣고 세 개의 질문에 답하세요.", 1.5)
        qn = 1
        for s, st in enumerate(day[key], 1):
            acc = st["accent"]
            kind = "conversation" if part == 3 else st["type_en"]
            t.ko(f"파트 {part}, {s}번째 세트.", 0.6)
            t.say(NARR, f"Questions {qn} through {qn + 2} refer to the following {kind}.", 1.0)
            if part == 3:
                segs = [(voice(acc, ln["spk"]), ln) for ln in st["lines"]]
            else:
                segs = [(voice(acc, st["spk"]), p) for p in st["paragraphs"]]
            for v, seg in segs:
                t.say(v, seg["en"], 0.5)
            t.wait(1.5)
            for i, q in enumerate(st["questions"]):
                read_question(t, qn + i, q)
            t.wait(4.0)
            t.ko("정답을 확인합니다.", 0.8)
            for i, q in enumerate(st["questions"]):
                answer_question(t, qn + i, q)
            unit = "한 사람씩" if part == 3 else "한 문단씩"
            t.ko(f"이제 {label}를 {unit} 다시 듣고 해석합니다.", 1.0)
            for v, seg in segs:
                t.say(v, seg["en"], 0.4)
                t.ko(seg["ko"], 1.0)
            t.wait(2.0)
            qn += 3
        tracks.append(t)

    # ---------- 단어 ----------
    t = Track(f"Day {d} - 04 오늘의 단어")
    t.ko(f"오늘의 단어입니다. 단어, 뜻, 스펠링, 그리고 다시 단어와 뜻 순서로 들려드립니다.", 1.5)
    for n, w in enumerate(day["vocab"], 1):
        t.ko(f"{n}번.", 0.4)
        t.say(NARR, w["word"], 0.5)
        t.ko(w["ko"], 0.6)
        t.say(NARR, ", ".join(w["word"].upper().replace(" ", "")), 0.6)
        t.say(NARR, w["word"], 0.5)
        t.ko(w["ko"], 1.5)
    tracks.append(t)

    # ---------- 뉴스 ----------
    t = Track(f"Day {d} - 05 영어 뉴스")
    t.ko("영어 뉴스 시간입니다. 한국 관련 기사를 먼저 끝까지 듣고, 다시 한 문단씩 해석합니다. "
         "기사는 해외 언론 보도를 바탕으로 학습용으로 다시 쓴 내용입니다.", 1.5)
    for n, a in enumerate(day["news"], 1):
        t.ko(f"뉴스 {n}. {a['title_ko']}", 1.0)
        t.say(NARR, a["title_en"], 1.0)
        for p in a["paragraphs"]:
            t.say(NARR, p["en"], 0.8)
        t.wait(2.0)
        t.ko("이제 한 문단씩 다시 듣고 해석합니다.", 1.0)
        for p in a["paragraphs"]:
            t.say(NARR, p["en"], 0.5)
            t.ko(p["ko"], 1.2)
        t.wait(2.0)
    t.ko(f"데이 {d} 학습을 모두 마쳤습니다. 수고하셨습니다.", 1.0)
    tracks.append(t)
    return tracks


async def synth(sem, v, text):
    path = CACHE / (hashlib.sha1(f"{v}|{text}".encode()).hexdigest() + ".mp3")
    if path.exists() and path.stat().st_size:
        return path
    async with sem:
        for attempt in range(4):
            try:
                tmp = path.with_suffix(".tmp")
                await edge_tts.Communicate(text, v).save(str(tmp))
                tmp.replace(path)
                return path
            except Exception as e:  # 네트워크 오류 시 재시도
                if attempt == 3:
                    raise
                print(f"  재시도 ({e}): {text[:40]}")
                await asyncio.sleep(2 + attempt * 3)


def id3(title, album, track_no):
    def frame(fid, text):
        data = b"\x01" + text.encode("utf-16") + b"\x00\x00"
        return fid.encode() + struct.pack(">I", len(data)) + b"\x00\x00" + data

    body = (frame("TIT2", title) + frame("TALB", album) +
            frame("TPE1", "TOEIC 800 Listening") + frame("TRCK", str(track_no)))
    size = len(body)
    syncsafe = bytes([(size >> 21) & 0x7F, (size >> 14) & 0x7F, (size >> 7) & 0x7F, size & 0x7F])
    return b"ID3\x03\x00\x00" + syncsafe + body


def strip_id3(b):
    if b[:3] == b"ID3":
        s = b[6:10]
        return b[10 + ((s[0] << 21) | (s[1] << 14) | (s[2] << 7) | s[3]):]
    return b


async def main(day_no):
    day = json.loads((ROOT / "content" / f"day{day_no:03d}.json").read_text(encoding="utf-8"))
    tracks = build_tracks(day)
    CACHE.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(6)
    unique = {it for t in tracks for it in t.items if isinstance(it, tuple)}
    print(f"음성 조각 {len(unique)}개 생성 중...")
    paths = dict(zip(unique, await asyncio.gather(*(synth(sem, v, x) for v, x in unique))))

    out = ROOT / "docs" / "audio" / f"day{day_no:03d}"   # 앱(GitHub Pages)에 올라가는 트랙별 파일
    local = ROOT / "audio"                                  # 전체 1개 파일은 로컬 전용 (용량 때문에 업로드 안 함)
    out.mkdir(parents=True, exist_ok=True)
    local.mkdir(exist_ok=True)
    album = f"TOEIC Day {day_no}"
    full, total, listing = bytearray(), 0.0, []
    for n, t in enumerate(tracks, 1):
        audio = bytearray()
        for it in t.items:
            if isinstance(it, tuple):
                audio += strip_id3(paths[it].read_bytes())
            else:
                audio += SILENT_FRAME * round(it / FRAME_SEC)
        sec = len(audio) / 6000  # 48kbps CBR = 6000 bytes/s
        total += sec
        (out / f"day{day_no:03d}_{n:02d}.mp3").write_bytes(id3(t.title, album, n) + audio)
        full += audio
        listing.append({"t": t.short, "m": round(sec / 60, 1)})
        print(f"  {n:02d} {t.title}: {sec / 60:.1f}분")
    (local / f"day{day_no:03d}_full.mp3").write_bytes(id3(f"Day {day_no} 전체", album, 0) + full)

    days_file = ROOT / "docs" / "days.json"
    days = json.loads(days_file.read_text(encoding="utf-8"))["days"] if days_file.exists() else []
    days = sorted([d for d in days if d["day"] != day_no] + [{"day": day_no, "tracks": listing}], key=lambda d: d["day"])
    days_file.write_text(json.dumps({"days": days}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"총 {total / 60:.1f}분 -> {out} (days.json 갱신)")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 1))
