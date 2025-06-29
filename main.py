from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from fastapi import FastAPI, Depends, HTTPException

from pydantic import BaseModel

from typing import Optional

app = FastAPI()

DATABASE_URL = "sqlite:///.test.db"

#Conectar api com banco
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

#Sessão para imteragir com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Classe base
Base = declarative_base()

#Tabela
class User(Base):
    __tablename__ = "users" #Nome da tabela

    id = Column(Integer, primary_key=True, index=True) #ID
    name = Column(String, index=True) #Nome
    email = Column(String, unique=True, index=True) #Email
 
#Criar a tabela de acordo com o modelo passado
Base.metadata.create_all(bind=engine)



#Get
def get_db():   
    db = SessionLocal()
    try:
        #Retornar um valor
        yield db
    finally:
        #Fechar a sessão após procedimento
        db.close()

#Validar dados 
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class Config:
    orm_mode = True

#Endpoint para retornar os dados do user como resposta
@app.post("/users/", response_model=UserResponse)
#O Depends é usado para injetar o banco no endpoint
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    #Criar um novo usuário com os dados passados na requisição
    db_user = User(name=user.name, email=user.email)
    #Adicionar novo usuário na sessão
    db.add(db_user)
    #Salvar as alterações no banco
    db.commit()
    #Reload no objeto do user com os novos dados
    db.refresh(db_user)
    return db_user

#Endpoint para retornar todos os registros
#Retornar uma lista de usuários
@app.get("/users/", response_model=list[UserResponse])
#skip e limite é para exibição de paginação, skip é para quantos pular e limit é o máximo de retorno
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    #faz a query
    users = db.query(User).offset(skip).limit(limit).all()
    return users

#Endpoint para retornar registro específico de acordo com o parâmetro
@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    #faz a query
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code = 404, detail="User not found")
    return user

#Validar se o dado é válido antes de realizar alterações
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

#Endpoint de update
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    #Query para achar user por id
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code = 404, detail="User not found")
    #Fazer upload só se houver uma nova informação
    db_user.name = user.name if user.name is not None else db_user.name
    db_user.email = user.email if user.email is not None else db_user.email
    db.commit()
    db.refresh(db_user)
    return db_user

#Endpoint de delete
@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    #Query para achar user por id
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code = 404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user


#Use o comando uvicorn main:app --reload
#Use o endereço http://127.0.0.1:8000/docs