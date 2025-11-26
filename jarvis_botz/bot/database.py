from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import or_


engine = create_engine('sqlite:///base.db', echo=False)


SessionLocal = sessionmaker(bind=engine, autoflush=True)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'


    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    tokens = Column(Float, default=10)
    role = Column(String, default='user')






def get_user(id=None, username=None):
    with SessionLocal() as session:
        user = session.query(User).filter(or_(User.id == id, User.username == username)).first()
        return user
    

def add_user(id, username):
    with SessionLocal() as session:
        if session.query(User).filter_by(id=id).first():
            return False
        user = User(id=id, username=username)
        session.add(user)
        session.commit()
        return user
    

def add_token(id, num):
    with SessionLocal() as session:
        user = session.get(User, id)
        if not user:
            return False
        
        user.tokens += num
        session.commit()
        return True
    

def remove_token(id, num):
    with SessionLocal() as session:
        user = session.get(User, id)
        if not user:
            return False
        
        user.tokens -= num
        session.commit()
        return True
    


def change_role(id=None, username=None, role:str='user'):
    with SessionLocal() as session:
        user = session.query(User).filter(or_(User.id == id, User.username == username)).first()
        if not user:
            return False
        
        user.role = role
        session.commit()
        return True
    
    