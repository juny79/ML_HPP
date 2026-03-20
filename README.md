# House Price Prediction | 리더보드 채점 시스템

서울시 아파트 실거래가 예측 대회 리더보드 시스템입니다.

---

## 📁 프로젝트 구조

```
leaderboard_system/
├── backend/
│   ├── app.py                    # Flask 메인 서버
│   ├── config.py                 # 설정 파일
│   ├── requirements.txt          # 패키지 목록
│   ├── .env                      # 환경 변수
│   ├── baseline.py               # 베이스라인 코드
│   ├── models/
│   │   └── database.py           # DB 모델
│   ├── routes/
│   │   ├── auth.py               # 인증 API
│   │   ├── submission.py         # 제출 API
│   │   └── leaderboard.py        # 리더보드 API
│   ├── services/
│   │   ├── evaluator.py          # RMSE 평가
│   │   └── file_handler.py       # 파일 처리
│   └── data/
│       ├── ground_truth.csv      # 정답 데이터 (비공개)
│       ├── sample_submission.csv # 샘플 제출 파일
│       └── create_ground_truth.py
└── frontend/
    ├── index.html
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

---

## ⚙️ 설치 및 실행

### 1단계 - 저장소 클론 및 디렉토리 이동

```bash
git clone https://github.com/your-repo/leaderboard_system.git
cd leaderboard_system
```

### 2단계 - 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Mac/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

### 3단계 - 패키지 설치

```bash
pip install -r requirements.txt
```

### 4단계 - 환경 변수 설정

```bash
# .env 파일 복사 후 수정
cp .env.example .env
```

`.env` 파일을 열어 아래 항목을 수정합니다.

```bash
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@competition.com
ADMIN_PASSWORD=admin1234!
GROUND_TRUTH_PATH=data/ground_truth.csv
```

### 5단계 - 정답 데이터 생성

```bash
cd data
python create_ground_truth.py
cd ..
```

실제 대회에서는 `data/ground_truth.csv`를 실제 정답 데이터로 교체합니다.

```
index,target
0,85000
1,62000
2,120000
...
```

### 6단계 - 서버 실행

```bash
python app.py
```

서버가 정상 실행되면 아래와 같이 출력됩니다.

```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### 7단계 - 프론트엔드 실행

별도의 빌드 없이 `frontend/index.html`을 브라우저에서 열거나,
간단한 HTTP 서버로 실행합니다.

```bash
cd frontend
python -m http.server 8080
```

브라우저에서 `http://localhost:8080` 접속

---

## 🔌 API 명세

### 인증

| Method | Endpoint             | 설명         | 인증 필요 |
|--------|----------------------|--------------|-----------|
| POST   | `/api/auth/register` | 회원가입     | ❌        |
| POST   | `/api/auth/login`    | 로그인       | ❌        |
| GET    | `/api/auth/me`       | 내 정보 조회 | ✅        |
| PUT    | `/api/auth/me`       | 내 정보 수정 | ✅        |

### 제출

| Method | Endpoint                              | 설명               | 인증 필요 |
|--------|---------------------------------------|--------------------|-----------|
| POST   | `/api/submit`                         | 파일 제출          | ✅        |
| GET    | `/api/submissions`                    | 내 제출 목록       | ✅        |
| GET    | `/api/submissions/<id>/status`        | 채점 상태 조회     | ✅        |
| POST   | `/api/submissions/<id>/select`        | 최종 제출 선택     | ✅        |
| GET    | `/api/daily-limit`                    | 일일 제출 한도     | ✅        |

### 리더보드

| Method | Endpoint                   | 설명                      | 인증 필요      |
|--------|----------------------------|---------------------------|----------------|
| GET    | `/api/leaderboard/public`  | Public 리더보드 조회      | ❌             |
| GET    | `/api/leaderboard/private` | Private 리더보드 조회     | ✅ (관리자만)  |
| GET    | `/api/leaderboard/my-rank` | 내 순위 조회              | ✅             |

### 헬스체크

| Method | Endpoint       | 설명           |
|--------|----------------|----------------|
| GET    | `/api/health`  | 서버 상태 확인 |

---

## 📄 제출 파일 형식

```csv
index,target
0,85000
1,62000
2,120000
3,75000
...
9271,95000
```

| 컬럼   | 타입    | 설명                        |
|--------|---------|-----------------------------|
| index  | integer | 테스트 샘플 인덱스 (0~9271) |
| target | integer | 예측 아파트 거래가 (만원)   |

---

## 📊 평가 지표

$$RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$$

- **Public 리더보드** : 전체 테스트 데이터의 **50%** 기준
- **Private 리더보드** : 전체 테스트 데이터의 **100%** 기준 (대회 종료 후 공개)

---

## 🚀 베이스라인 실행

```bash
python baseline.py
```

생성된 `submission.csv`를 리더보드에 제출합니다.

---

## ⚠️ 주의사항

- 일일 제출 횟수는 **최대 5회**로 제한됩니다.
- 제출 파일은 반드시 **CSV 형식**이어야 합니다.
- `index` 컬럼은 **0~9271** 범위여야 합니다.
- `target` 컬럼에 **음수 또는 결측값**이 있으면 제출이 거부됩니다.
- `data/ground_truth.csv`는 **절대 외부에 노출되지 않도록** 관리하세요.

---

## 🛠️ 운영 환경 배포 (선택)

### Gunicorn으로 실행

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

### Docker로 실행

```bash
docker build -t leaderboard .
docker run -p 5000:5000 --env-file .env leaderboard
```
