// 앱 화면은 네트워크 우선(새 Day 반영), 오프라인이면 캐시.
// MP3는 사용자가 '저장'한 Day만 캐시에 있고, 오디오 태그의 Range 요청에 206으로 응답한다.
const SHELL = "shell-v2";
const AUDIO = "audio-v1";
const SHELL_FILES = ["./", "index.html", "days.json", "manifest.webmanifest", "icon-192.png", "icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== SHELL && k !== AUDIO).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.endsWith(".mp3")) e.respondWith(audio(e.request));
  else e.respondWith(shell(e.request));
});

async function shell(req) {
  try {
    const res = await fetch(req);
    if (res.ok) (await caches.open(SHELL)).put(req, res.clone());
    return res;
  } catch {
    return (await caches.match(req, { ignoreSearch: true })) || caches.match("./");
  }
}

async function audio(req) {
  const cached = await (await caches.open(AUDIO)).match(req.url);
  if (!cached) return fetch(req);
  const blob = await cached.blob();
  const range = /bytes=(\d*)-(\d*)/.exec(req.headers.get("range") || "");
  if (!range) {
    return new Response(blob, { headers: { "Content-Type": "audio/mpeg", "Content-Length": blob.size, "Accept-Ranges": "bytes" } });
  }
  const start = range[1] ? +range[1] : Math.max(0, blob.size - +range[2]);
  const end = range[1] && range[2] ? Math.min(+range[2], blob.size - 1) : blob.size - 1;
  return new Response(blob.slice(start, end + 1), {
    status: 206,
    headers: {
      "Content-Type": "audio/mpeg",
      "Content-Length": end - start + 1,
      "Content-Range": `bytes ${start}-${end}/${blob.size}`,
      "Accept-Ranges": "bytes",
    },
  });
}
