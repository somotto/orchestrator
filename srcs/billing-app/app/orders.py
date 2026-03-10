from sqlalchemy import Integer, Float
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = 'orders'

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(Integer, nullable=False)
    number_of_items = mapped_column(Integer, nullable=False)
    total_amount = mapped_column(Float, nullable=False)
