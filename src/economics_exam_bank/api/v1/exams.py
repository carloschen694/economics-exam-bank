from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from ...database import get_session
from ...models.exam import Exam, ExamCreate, ExamRead, ExamReadWithQuestions, SubjectType

router = APIRouter(prefix="/exams", tags=["Exams 試卷管理"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[ExamRead])
def list_exams(
    session: SessionDep,
    school: str | None = Query(default=None, description="依學校篩選"),
    year: int | None = Query(default=None, description="依年度篩選"),
    subject: SubjectType | None = Query(default=None, description="依考科篩選"),
    offset: int = 0,
    limit: int = Query(default=50, le=100),
) -> list[Exam]:
    statement = select(Exam)
    if school:
        statement = statement.where(Exam.school == school)
    if year:
        statement = statement.where(Exam.year == year)
    if subject:
        statement = statement.where(Exam.subject == subject)
    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement).all())


@router.post("", response_model=ExamRead, status_code=status.HTTP_201_CREATED)
def create_exam(
    exam_in: ExamCreate,
    session: SessionDep,
) -> Exam:
    exam = Exam.model_validate(exam_in)
    session.add(exam)
    session.commit()
    session.refresh(exam)
    return exam


@router.get("/{exam_id}", response_model=ExamReadWithQuestions)
def get_exam(
    exam_id: int,
    session: SessionDep,
) -> Exam:
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="找不到該試卷")
    return exam


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    session: SessionDep,
) -> None:
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="找不到該試卷")
    session.delete(exam)
    session.commit()
