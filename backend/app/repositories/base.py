from sqlalchemy.orm import Session
from typing import Type, TypeVar, Generic, List, Optional
from backend.app.database.session import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.user_id == id if hasattr(self.model, "user_id") and self.model.__tablename__ == "users" 
                                           else (self.model.tenant_id == id if hasattr(self.model, "tenant_id") and self.model.__tablename__ == "tenants"
                                                 else getattr(self.model, self.model.__tablename__[:-1] + "_id", None) == id)).first()

    def get_by_field(self, db: Session, field_name: str, value) -> Optional[ModelType]:
        return db.query(self.model).filter(getattr(self.model, field_name) == value).first()

    def get_all_by_field(self, db: Session, field_name: str, value) -> List[ModelType]:
        return db.query(self.model).filter(getattr(self.model, field_name) == value).all()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in, commit: bool = True) -> ModelType:
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in, commit: bool = True) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, val)
        db.add(db_obj)
        if commit:
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: ModelType, commit: bool = True) -> bool:
        db.delete(db_obj)
        if commit:
            db.commit()
        return True
