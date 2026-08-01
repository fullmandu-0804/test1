# Flask Hello World

Python Flask로 만든 가장 단순한 웹앱입니다.
`/` 경로에 접속하면 Bootstrap 5로 꾸민 "Hello, World!" 화면이 나옵니다.

## 폴더 구조

```
test1/
├── app.py              # 웹앱 본체 (실행 파일)
├── templates/
│   └── index.html      # 화면 디자인 (Bootstrap 5 CDN)
├── requirements.txt    # 필요한 패키지 목록
├── .gitignore          # Git에 올리지 않을 파일 목록
├── .env.example        # 환경변수 예시 파일
├── .env                # 실제 환경변수 (Git 제외)
└── README.md           # 이 문서
```

## 실행 방법

### 1. 가상환경 만들기 (한 번만)

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 준비

`.env.example` 을 복사해 `.env` 를 만들고 `SECRET_KEY` 값을 채웁니다.
(이 저장소에는 개발용 `.env` 가 이미 들어 있습니다.)

```bash
cp .env.example .env
```

### 4. 실행

```bash
python app.py
```

브라우저에서 http://127.0.0.1:5000 으로 접속하세요.

## 참고

- `debug=True` 로 실행되므로 코드를 저장하면 서버가 자동으로 다시 시작됩니다.
- 운영 환경에서는 `SECRET_KEY` 를 반드시 임의의 긴 문자열로 바꾸고 `debug` 를 끄세요.
