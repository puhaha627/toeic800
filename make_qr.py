"""설치용 QR 코드 생성: docs/qr.png (앱 주소를 담음)
사용법: tools\\python\\python.exe make_qr.py https://<user>.github.io/<repo>/
"""
import sys
from pathlib import Path

import qrcode

url = sys.argv[1]
img = qrcode.make(url, box_size=12, border=2)
out = Path(__file__).parent / "docs" / "qr.png"
img.save(out)
print(f"{out} <- {url}")
