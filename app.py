"""뚱지의 수원 맛집탐방 - Flask 웹앱."""

import os

from dotenv import load_dotenv
from flask import Flask, render_template

# .env 파일에 적어둔 값들을 환경변수로 불러온다.
load_dotenv()

# FLASK_ENV=production 이면 운영 모드로 판단한다. (기본값은 개발 모드)
IS_PRODUCTION = os.getenv("FLASK_ENV", "development").lower() == "production"

app = Flask(__name__)

# 운영 환경에서는 SECRET_KEY 를 반드시 환경변수로 받아야 한다.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError("운영 환경에서는 SECRET_KEY 환경변수를 반드시 설정해야 합니다.")
    SECRET_KEY = "dev-secret-key"

app.config["SECRET_KEY"] = SECRET_KEY
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL")  # 추후 DB 연동용

SITE_NAME = "뚱지의 수원 맛집탐방"


@app.context_processor
def inject_site_name():
    """모든 템플릿에서 site_name 을 그냥 쓸 수 있게 해준다."""
    return {"site_name": SITE_NAME}


@app.route("/")
def index():
    """홈페이지."""
    return render_template("index.html", active_page="index")


@app.route("/about")
def about():
    """소개 페이지."""
    return render_template("about.html", active_page="about")


@app.route("/contact")
def contact():
    """연락처 페이지."""
    return render_template("contact.html", active_page="contact")


if __name__ == "__main__":
    # 이 블록은 로컬에서 `python app.py` 로 실행할 때만 동작한다.
    # 운영 환경(Render)에서는 gunicorn 이 app 객체를 직접 실행하므로 여기를 거치지 않는다.
    app.run(
        debug=not IS_PRODUCTION,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
