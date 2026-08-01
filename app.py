"""뚱지의 수원 맛집탐방 - Flask 웹앱."""

import os

from dotenv import load_dotenv
from flask import Flask, render_template

# .env 파일에 적어둔 값들을 환경변수로 불러온다.
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

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
    app.run(debug=True, host="127.0.0.1", port=5000)
