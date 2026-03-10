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


    def __init__(self, user_id, number_of_items, total_amount):
        self.user_id = user_id
        self.number_of_items = number_of_items
        self.total_amount = total_amount
