from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    mentioned_games = relationship("MentionedGame", back_populates="user")
    threads = relationship("Thread", back_populates="user")

class MentionedGame(Base):
    __tablename__ = "mentioned_games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_title = Column(String, index=True)
    mention_count = Column(Integer, default=1)
    sentiment_score = Column(Float, default=-1.0)  # New column

    user = relationship("User", back_populates="mentioned_games")

class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="threads")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

    user = relationship("User")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)

    user = relationship("User")

class VerificationKey(Base):
    __tablename__ = "verification_keys"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    key = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)