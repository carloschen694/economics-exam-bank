from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select
from ...database import get_session
from ...models.question import (
    Question,
    QuestionCreate,
    QuestionRead,
    QuestionType,
    QuestionUpdate,
)

router = APIRouter(prefix="/questions", tags=["Questions 題目管理"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[QuestionRead])
def list_questions(
    session: SessionDep,
    exam_id: int | None = Query(default=None, description="依試卷 ID 篩選"),
    question_type: QuestionType | None = Query(default=None, description="依題型篩選"),
    tag: str | None = Query(default=None, description="依標籤關鍵字搜尋"),
    keyword: str | None = Query(default=None, description="依題目內容關鍵字搜尋"),
    offset: int = 0,
    limit: int = Query(default=50, le=100),
) -> list[Question]:
    statement = select(Question)
    if exam_id is not None:
        statement = statement.where(Question.exam_id == exam_id)
    if question_type is not None:
        statement = statement.where(Question.question_type == question_type)
    if tag:
        statement = statement.where(col(Question.tags).contains(tag))
    if keyword:
        statement = statement.where(col(Question.content).contains(keyword))

    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement).all())


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


@router.get("/{question_id}", response_model=QuestionRead)
def get_question(
    question_id: int,
    session: SessionDep,
) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="找不到該題目")
    return question


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
