"""데이터베이스 모델(표) 정의."""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

# 앱과 분리해서 만들어 두고, app.py 에서 db.init_app(app) 으로 연결한다.
# (이렇게 해야 models.py 와 app.py 가 서로를 import 하는 순환 참조가 생기지 않는다.)
db = SQLAlchemy()


class Place(db.Model):
    """맛집 한 곳을 담는 표."""

    __tablename__ = "places"

    # 기본키: 각 행을 구분하는 번호. 자동으로 1, 2, 3... 증가한다.
    id = db.Column(db.Integer, primary_key=True)

    # 가게 이름 (필수)
    name = db.Column(db.String(100), nullable=False)

    # 동네 (예: 행궁동, 광교, 영통) (필수)
    district = db.Column(db.String(50), nullable=False)

    # 음식 종류 (예: 한식, 카페)
    category = db.Column(db.String(50))

    # 평점 (0.0 ~ 5.0)
    rating = db.Column(db.Float, default=0.0)

    # 한줄평
    one_liner = db.Column(db.String(200))

    # 등록 시각 (자동 기록)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        """터미널에서 출력할 때 보기 좋게."""
        return f"<Place {self.name} ({self.district})>"
