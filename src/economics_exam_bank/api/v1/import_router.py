from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlmodel import Session
import csv
import json
from ...database import get_session
from ...models.exam import Exam, ExamCreate, SubjectType
from ...models.question import Question, QuestionCreate, QuestionType

router = APIRouter(prefix="/import", tags=["Import 匯入資料"])

BATCH_SIZE = 1000

def _parse_csv(file_bytes: bytes):
    lines = file_bytes.decode("utf-8").splitlines()
    reader = csv.DictReader(lines)
    return list(reader)

def _parse_json(file_bytes: bytes):
    return json.loads(file_bytes.decode("utf-8"))

@router.post("/", status_code=status.HTTP_201_CREATED)
def import_data(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Bulk import Exams and Questions from a CSV or JSON file.

    The file must contain the following columns (CSV header) or keys (JSON):
    school, year, subject, exam_name, question_text, question_number (optional),
    sub_number (optional), question_type (optional), options (optional), answer (optional),
    explanation (optional), tags (optional), difficulty (optional), points (optional).
    """
    content = file.file.read()
    if file.filename.lower().endswith('.csv'):
        records = _parse_csv(content)
    elif file.filename.lower().endswith('.json'):
        records = _parse_json(content)
    else:
        raise HTTPException(status_code=400, detail="僅支援 CSV 或 JSON 檔案")

    success = 0
    failed = 0
    exam_cache: dict[tuple, int] = {}
    batch: list[Question] = []

    for idx, rec in enumerate(records, start=1):
        try:
            # Identify or create exam
            exam_key = (
                rec["school"],
                int(rec["year"]),
                rec["subject"],
                rec["exam_name"]
            )
            if exam_key not in exam_cache:
                exam_in = ExamCreate(
                    title=rec["exam_name"],
                    school=rec["school"],
                    year=int(rec["year"]),
                    subject=SubjectType(rec["subject"]),
                )
                exam = Exam.model_validate(exam_in)
                session.add(exam)
                session.commit()
                session.refresh(exam)
                exam_cache[exam_key] = exam.id
            exam_id = exam_cache[exam_key]

            question_in = QuestionCreate(
                exam_id=exam_id,
                question_number=int(rec.get("question_number", 1)),
                sub_number=rec.get("sub_number"),
                question_type=QuestionType(rec.get("question_type", "calculation")),
                content=rec["question_text"],
                options=rec.get("options"),
                answer=rec.get("answer"),
                explanation=rec.get("explanation"),
                tags=rec.get("tags"),
                difficulty=int(rec.get("difficulty", 3)),
                points=float(rec.get("points", 10.0)),
            )
            question = Question.model_validate(question_in)
            batch.append(question)
            # Commit batch when size reaches limit
            if len(batch) >= BATCH_SIZE:
                with session.begin():
                    session.add_all(batch)
                batch.clear()
            success += 1
        except Exception:
            session.rollback()
            failed += 1
    # Commit any remaining questions
    if batch:
        with session.begin():
            session.add_all(batch)
    return {"imported": success, "failed": failed}
