from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select, or_
from ...database import get_session
from ...models.entities import (
    Exam,
    Question,
    QuestionCreate,
    QuestionRead,
    QuestionType,
    QuestionUpdate,
)

router = APIRouter(prefix="/questions", tags=["Questions 題目管理"])

SessionDep = Annotated[Session, Depends(get_session)]


class QuestionWithExamRead(QuestionRead):
    exam_title: Optional[str] = None
    year: Optional[int] = None
    school: Optional[str] = None


def parse_question_type(raw: str | None) -> QuestionType | None:
    if not raw:
        return None
    val = raw.strip().lower()
    if val in [e.value for e in QuestionType]:
        return QuestionType(val)
    if "單選" in raw:
        return QuestionType.SINGLE_CHOICE
    elif "複選" in raw or "多選" in raw:
        return QuestionType.MULTIPLE_CHOICE
    elif "證明" in raw:
        return QuestionType.PROOF
    elif "計算" in raw:
        return QuestionType.CALCULATION
    elif "申論" in raw:
        return QuestionType.ESSAY
    return None


@router.get("", response_model=list[QuestionWithExamRead])
def list_questions(
    session: SessionDep,
    exam_id: int | None = Query(default=None, description="依試卷 ID 篩選"),
    year: int | None = Query(default=None, description="依民國年份篩選（如：113, 114, 115）"),
    school: str | None = Query(default=None, description="依學校名稱篩選（如：國立臺北大學）"),
    question_type: str | None = Query(default=None, description="依題型篩選（支援英文代碼或中文如：複選題、計算題）"),
    tag: str | None = Query(default=None, description="依標籤關鍵字搜尋（如：效用, Cournot）"),
    keyword: str | None = Query(default=None, description="依題目內容關鍵字搜尋（如：Hicksian, Nash）"),
    offset: int = 0,
    limit: int = Query(default=50, le=100),
) -> list[QuestionWithExamRead]:
    statement = select(Question, Exam).join(Exam, isouter=True)

    if exam_id is not None:
        statement = statement.where(Question.exam_id == exam_id)
    if year is not None:
        statement = statement.where(Exam.year == year)
    if school:
        statement = statement.where(col(Exam.school).contains(school))
    
    # 彈性解析題型
    parsed_type = parse_question_type(question_type)
    if parsed_type is not None:
        statement = statement.where(Question.question_type == parsed_type)

    if tag:
        statement = statement.where(col(Question.tags).contains(tag))
        
    if keyword and keyword.strip():
        kw = keyword.strip()
        statement = statement.where(
            or_(
                col(Question.content).contains(kw),
                col(Question.tags).contains(kw),
                col(Question.answer).contains(kw),
                col(Question.explanation).contains(kw)
            )
        )

    statement = statement.offset(offset).limit(limit)
    results = session.exec(statement).all()

    output = []
    for question, exam in results:
        q_dict = question.model_dump()
        if exam:
            q_dict["exam_title"] = exam.title
            q_dict["year"] = exam.year
            q_dict["school"] = exam.school
        output.append(QuestionWithExamRead(**q_dict))

    return output


@router.post("", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    question_in: QuestionCreate,
    session: SessionDep,
) -> Question:
    question = Question.model_validate(question_in)
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


@router.get("/{question_id}", response_model=QuestionWithExamRead)
def get_question(
    question_id: int,
    session: SessionDep,
) -> QuestionWithExamRead:
    statement = select(Question, Exam).where(Question.id == question_id).join(Exam, isouter=True)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="找不到該題目")
    question, exam = result
    q_dict = question.model_dump()
    if exam:
        q_dict["exam_title"] = exam.title
        q_dict["year"] = exam.year
        q_dict["school"] = exam.school
    return QuestionWithExamRead(**q_dict)


@router.patch("/{question_id}", response_model=QuestionRead)
def update_question(
    question_id: int,
    question_in: QuestionUpdate,
    session: SessionDep,
) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="找不到該題目")
    
    update_data = question_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)
        
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    session: SessionDep,
) -> None:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="找不到該題目")
    session.delete(question)
    session.commit()
