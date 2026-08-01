"""뚱지의 수원 맛집탐방 - Flask 웹앱."""

import os
import secrets
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

from models import Place, db

# .env 파일에 적어둔 값들을 환경변수로 불러온다.
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

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

# 관리 화면 비밀번호. 비어 있으면 로컬 개발에서만 무인증으로 통과시킨다.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def resolve_database_url():
    """DATABASE_URL 이 있으면 PostgreSQL, 없으면 로컬 SQLite 를 쓴다."""
    url = (os.getenv("DATABASE_URL") or "").strip()

    if not url:
        # 로컬 개발용: 프로젝트 폴더에 local.db 파일 하나로 동작한다.
        sqlite_path = os.path.join(BASE_DIR, "local.db").replace("\\", "/")
        return f"sqlite:///{sqlite_path}"

    # Render/Heroku 는 postgres:// 형식으로 주는데
    # SQLAlchemy 는 postgresql:// 형식만 인식하므로 바꿔준다.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


app.config["SQLALCHEMY_DATABASE_URI"] = resolve_database_url()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# DB와 마이그레이션(설계도 변경 이력) 기능을 앱에 연결한다.
db.init_app(app)
migrate = Migrate(app, db)

SITE_NAME = "뚱지의 수원 맛집탐방"


@app.context_processor
def inject_globals():
    """모든 템플릿에서 공통으로 쓰는 값들."""
    return {
        "site_name": SITE_NAME,
        "is_admin": bool(session.get("is_admin")) or not ADMIN_PASSWORD,
    }


# --------------------------------------------------------------------------
# 공개 페이지
# --------------------------------------------------------------------------


@app.route("/")
def index():
    """홈페이지."""
    return render_template("index.html", active_page="index")


@app.route("/places")
def places():
    """맛집 목록 페이지. DB에서 읽어와 평점 높은 순으로 보여준다."""
    items, db_ready = load_places()
    return render_template(
        "places.html",
        active_page="places",
        places=items,
        db_ready=db_ready,
    )


@app.route("/about")
def about():
    """소개 페이지."""
    return render_template("about.html", active_page="about")


@app.route("/contact")
def contact():
    """연락처 페이지."""
    return render_template("contact.html", active_page="contact")


def load_places():
    """맛집 목록을 읽어온다. 표가 아직 없으면 빈 목록을 돌려준다."""
    try:
        return Place.query.order_by(Place.rating.desc(), Place.id).all(), True
    except SQLAlchemyError:
        # 아직 표(테이블)가 만들어지지 않은 경우에도 페이지가 깨지지 않도록 한다.
        db.session.rollback()
        return [], False


# --------------------------------------------------------------------------
# 관리 화면 (비밀번호 잠금)
# --------------------------------------------------------------------------


def admin_required(view):
    """관리 화면 접근을 막는 문지기."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not ADMIN_PASSWORD:
            if IS_PRODUCTION:
                # 운영 환경에서 비밀번호가 없으면 아예 열지 않는다.
                abort(503)
            # 로컬 개발에서는 편의를 위해 그냥 통과시킨다.
            return view(*args, **kwargs)

        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))

        return view(*args, **kwargs)

    return wrapper


def safe_next_path(value):
    """외부 사이트로 튕겨나가지 않도록 이동 경로를 검사한다."""
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return url_for("admin_list")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """관리자 로그인."""
    if not ADMIN_PASSWORD:
        return redirect(url_for("admin_list"))

    if request.method == "POST":
        entered = request.form.get("password", "")
        # 한글 등 ASCII 밖의 문자도 비교할 수 있도록 바이트로 변환한다.
        # compare_digest 는 비교 시간을 일정하게 유지해 비밀번호 추측을 어렵게 한다.
        if secrets.compare_digest(entered.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8")):
            session["is_admin"] = True
            flash("로그인되었습니다.", "success")
            return redirect(safe_next_path(request.args.get("next")))
        flash("비밀번호가 올바르지 않습니다.", "danger")

    return render_template("admin_login.html", active_page="admin")


@app.route("/admin/logout")
def admin_logout():
    """로그아웃."""
    session.pop("is_admin", None)
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("places"))


@app.route("/admin")
@admin_required
def admin_list():
    """관리용 맛집 목록."""
    items, db_ready = load_places()
    return render_template(
        "admin_list.html",
        active_page="admin",
        places=items,
        db_ready=db_ready,
    )


def read_place_form(form):
    """폼에 입력된 값을 검사해서 (값, 오류목록) 으로 돌려준다."""
    data = {
        "name": (form.get("name") or "").strip(),
        "district": (form.get("district") or "").strip(),
        "category": (form.get("category") or "").strip(),
        "one_liner": (form.get("one_liner") or "").strip(),
        "rating": 0.0,
    }
    errors = []

    if not data["name"]:
        errors.append("가게 이름을 입력해 주세요.")
    if not data["district"]:
        errors.append("동네를 입력해 주세요.")

    raw_rating = (form.get("rating") or "").strip()
    if raw_rating:
        try:
            data["rating"] = float(raw_rating)
        except ValueError:
            errors.append("평점은 숫자로 입력해 주세요. (예: 4.5)")

    if not 0 <= data["rating"] <= 5:
        errors.append("평점은 0 이상 5 이하로 입력해 주세요.")

    return data, errors


@app.route("/admin/new", methods=["GET", "POST"])
@admin_required
def admin_new():
    """맛집 등록."""
    if request.method == "POST":
        data, errors = read_place_form(request.form)
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "admin_form.html",
                active_page="admin",
                place=data,
                form_title="맛집 등록",
                action_url=url_for("admin_new"),
            )

        db.session.add(Place(**data))
        db.session.commit()
        flash(f"'{data['name']}' 을(를) 등록했습니다.", "success")
        return redirect(url_for("admin_list"))

    return render_template(
        "admin_form.html",
        active_page="admin",
        place=None,
        form_title="맛집 등록",
        action_url=url_for("admin_new"),
    )


@app.route("/admin/<int:place_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit(place_id):
    """맛집 수정."""
    place = db.get_or_404(Place, place_id)

    if request.method == "POST":
        data, errors = read_place_form(request.form)
        if errors:
            for message in errors:
                flash(message, "danger")
            return render_template(
                "admin_form.html",
                active_page="admin",
                place=data,
                form_title="맛집 수정",
                action_url=url_for("admin_edit", place_id=place_id),
            )

        for key, value in data.items():
            setattr(place, key, value)
        db.session.commit()
        flash(f"'{place.name}' 정보를 수정했습니다.", "success")
        return redirect(url_for("admin_list"))

    return render_template(
        "admin_form.html",
        active_page="admin",
        place=place,
        form_title="맛집 수정",
        action_url=url_for("admin_edit", place_id=place_id),
    )


@app.route("/admin/<int:place_id>/delete", methods=["POST"])
@admin_required
def admin_delete(place_id):
    """맛집 삭제."""
    place = db.get_or_404(Place, place_id)
    name = place.name
    db.session.delete(place)
    db.session.commit()
    flash(f"'{name}' 을(를) 삭제했습니다.", "success")
    return redirect(url_for("admin_list"))


# --------------------------------------------------------------------------
# 샘플 데이터
# --------------------------------------------------------------------------

# 화면 확인용 샘플 데이터. 나중에 진짜 맛집 정보로 교체하면 된다.
SAMPLE_PLACES = [
    {
        "name": "행궁동 손칼국수",
        "district": "행궁동",
        "category": "한식",
        "rating": 4.6,
        "one_liner": "멸치육수가 진하고 면발이 쫄깃합니다. 비 오는 날 생각나는 집.",
    },
    {
        "name": "광교 가마솥국밥",
        "district": "광교",
        "category": "한식",
        "rating": 4.4,
        "one_liner": "국물이 맑은데도 깊습니다. 아침 해장으로 자주 갑니다.",
    },
    {
        "name": "권선 온기베이커리",
        "district": "권선동",
        "category": "베이커리",
        "rating": 4.7,
        "one_liner": "소금빵이 오후 3시면 다 나갑니다. 서둘러 가세요.",
    },
    {
        "name": "화서역 라멘야",
        "district": "화서동",
        "category": "일식",
        "rating": 4.5,
        "one_liner": "돈코츠가 묵직합니다. 면 굵기를 골라 주는 점이 좋아요.",
    },
    {
        "name": "영통 마늘닭갈비",
        "district": "영통동",
        "category": "한식",
        "rating": 4.2,
        "one_liner": "볶음밥까지 먹어야 완성입니다. 양이 넉넉해요.",
    },
    {
        "name": "매탄동 사거리분식",
        "district": "매탄동",
        "category": "분식",
        "rating": 4.0,
        "one_liner": "떡볶이는 평범하지만 튀김이 바삭합니다. 가성비가 좋아요.",
    },
]


@app.cli.command("seed")
def seed():
    """샘플 맛집 데이터를 DB에 넣는다. (이미 있으면 건너뛴다)"""
    added = 0
    for data in SAMPLE_PLACES:
        if Place.query.filter_by(name=data["name"]).first():
            continue
        db.session.add(Place(**data))
        added += 1

    db.session.commit()
    print(f"샘플 데이터 {added}건 추가 (전체 {Place.query.count()}건)")


if __name__ == "__main__":
    # 이 블록은 로컬에서 `python app.py` 로 실행할 때만 동작한다.
    # 운영 환경(Render)에서는 gunicorn 이 app 객체를 직접 실행하므로 여기를 거치지 않는다.
    app.run(
        debug=not IS_PRODUCTION,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
