from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from economics_exam_bank.database import get_session
from economics_exam_bank.main import app
from economics_exam_bank.models.exam import SubjectType
from economics_exam_bank.models.question import QuestionType


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    def get_session_override() -> Session:
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_root_and_health(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "歡迎使用" in res.json()["message"]

    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"


def test_exam_and_question_flow(client: TestClient) -> None:
    # 1. 建立試卷
    exam_payload = {
        "title": "113學年度台大經濟所個體經濟學",
        "school": "國立臺灣大學",
        "department": "經濟學研究所",
        "year": 113,
        "subject": SubjectType.MICROECONOMICS.value,
        "description": "第 1-10 題為單選題，第 11-12 題為計算分析題",
    }
    exam_res = client.post("/api/v1/exams", json=exam_payload)
    assert exam_res.status_code == 201
    exam_data = exam_res.json()
    exam_id = exam_data["id"]

    # 2. 新增題目（包含 LaTeX 數學式）
    question_payload = {
        "exam_id": exam_id,
        "question_number": 1,
        "question_type": QuestionType.SINGLE_CHOICE.value,
        "content": "消費者效用函數為 $U(x, y) = x^{0.5} y^{0.5}$，在預算限制 $p_x x + p_y y \\le I$ 下，其需求函數為：",
        "options": '{"A": "x* = I/(2px)", "B": "x* = I/px", "C": "x* = 2I/px", "D": "以上皆非"}',
        "answer": "A",
        "explanation": "由 Cobb-Douglas 效用函數指數各佔一半，支出份額均為 1/2，故 $p_x x = 0.5 I \\implies x^* = \\frac{I}{2 p_x}$。",
        "tags": "個體經濟學,消費者理論,Cobb-Douglas,需求函數",
        "difficulty": 2,
        "points": 5.0,
    }
    q_res = client.post("/api/v1/questions", json=question_payload)
    assert q_res.status_code == 201
    q_data = q_res.json()
    q_id = q_data["id"]

    # 3. 取得試卷並包含題目
    get_exam_res = client.get(f"/api/v1/exams/{exam_id}")
    assert get_exam_res.status_code == 200
    assert len(get_exam_res.json()["questions"]) == 1

    # 4. 測驗作答驗證
    submit_res = client.post(
        "/api/v1/practice/submit",
        json={"question_id": q_id, "user_answer": "A"},
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["is_correct"] is True

    # 5. 測驗作答錯誤驗證
    wrong_submit = client.post(
        "/api/v1/practice/submit",
        json={"question_id": q_id, "user_answer": "B"},
    )
    assert wrong_submit.status_code == 200
    assert wrong_submit.json()["is_correct"] is False
