from sqlmodel import create_engine, Session, SQLModel

engine = create_engine("sqlite:///database.db")
def init_db():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session