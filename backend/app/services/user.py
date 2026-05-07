from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session


from app.models import User, UserRole
from app.schemas import UserCreate, UserUpdate
from app.core.security import hash_password



#create_user
def create_user(db: Session, user_data: UserCreate) -> User:
    print(user_data.password)
    print(len(user_data.password.encode("utf-8")))

    user = User(
        username=user_data.username,
        fullname=user_data.fullname,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        is_active=True,
    )

    db.add(user)
    db.flush()

    for role_id in user_data.role_ids:

        user_role = UserRole(
            user_id=user.id,
            role_id=role_id,
        )
        db.add(user_role)



    db.commit()
    db.refresh(user)

    return user


#get_user_by_id
def get_user_by_id(db: Session ,user_id:UUID) -> User | None:
    statement = select(User).where(User.id == user_id)

    return db.execute(statement).scalar_one_or_none()


#get_user_by_email
def get_user_by_email(db: Session ,email:str) -> User | None:
    statement = select(User).where(User.email == email)

    return db.execute(statement).scalar_one_or_none()

#get_user_by_username
def get_user_by_username(db: Session ,username:str) -> User | None:
    statement = select(User).where(User.username == username)

    return db.execute(statement).scalar_one_or_none()

#get_users
def get_users(db: Session) -> list[User]:
    statement = select(User)

    return list (db.execute(statement).scalars().all())

#update_user
def update_user(db: Session, user_data: UserUpdate, user_id:UUID) -> User | None:

    statement = select(User).where(User.id == user_id)
    user = db.execute(statement).scalar_one_or_none()

    if user is None: return None

    # Update only the fields sent by the backend and conserve the unsent fields
    updated_data = user_data.model_dump(exclude_unset=True)

    #role_ids are in a separate table
    role_ids = updated_data.pop("role_ids", None)

    #handle password to hash it
    password = updated_data.pop("password", None)
    if password is not None:
        user.password_hash = hash_password(password)

    for field, value in updated_data.items():
        setattr(user, field, value)

    # if frontend sent role_ids, replace user's roles
    if role_ids is not None:
        # remove old role links
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()

        for role_id in role_ids:
            db.add(UserRole(user_id=user.id, role_id=role_id))

    db.commit()
    db.refresh(user)

    return user

#deactivate_user
def deactivate_user(db: Session, user_id: UUID) -> User | None:
    statement = select(User).where(User.id == user_id)
    user = db.execute(statement).scalar_one_or_none()

    if user is None: return None

    user.is_active = False

    db.commit()
    db.refresh(user)

    return user

def activate_user(db: Session, user_id: UUID) -> User | None:
    statement = select(User).where(User.id == user_id)
    user = db.execute(statement).scalar_one_or_none()

    if user is None: return None

    user.is_active = True

    db.commit()
    db.refresh(user)

    return user


