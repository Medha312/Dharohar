from fastapi import APIRouter
from app.api.deps import CurrentUserDep, SessionDep
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.audit_service import audit_service
from app.utils.enums import AuditAction

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: CurrentUserDep) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: CurrentUserDep,
    db: SessionDep,
) -> User:
    old_data = {"name": current_user.name, "email": current_user.email}

    if user_update.name is not None:
        current_user.name = user_update.name
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.password is not None:
        current_user.password_hash = get_password_hash(user_update.password)

    db.commit()
    db.refresh(current_user)

    audit_service.log(
        db=db,
        action=AuditAction.USER_UPDATED,
        entity_type="User",
        entity_id=str(current_user.id),
        user_id=current_user.id,
        old_value=old_data,
        new_value={"name": current_user.name, "email": current_user.email},
    )

    return current_user
