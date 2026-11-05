from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud import card as card_crud
from app.crud import card_note as crud
from app.db.session import get_db
from app.schemas.card_note import CardNoteIn, CardNoteOut

# メモは自分だけのものなので、user_idはいつもJWTから取る
router = APIRouter(
    prefix="/card",
    tags=["card_notes"],
    dependencies=[Depends(get_current_user_id)],
)


@router.put("/{card_id}/note/", response_model=CardNoteOut)
def save_note(
    card_id: UUID,
    body: CardNoteIn,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # お題の参照は誰でもできるので、メモもどのお題にでも付けられる
    if card_crud.get_card(db, card_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")
    return crud.save_note(db, user_id, card_id, body.note)


@router.delete("/{card_id}/note/", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    card_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    card_note = crud.get_note(db, user_id, card_id)
    if card_note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
    crud.delete_note(db, card_note)
