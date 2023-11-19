from sqlalchemy.orm import Mapped, mapped_column

from db import DB


class SantaParticipant(DB.Model):
    __tablename__ = 'santa_participant'

    santa_id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column()
    has_shipped: Mapped[bool] = mapped_column(default=False)
