from fastapi import FastAPI,Request,HTTPException
from fastapi.params import Depends
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel

from app.database import check_db_connection,engine,Base,SessionLocal
from app import models,schemas,auth

from app.exchange import fetch_rates

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

models.Base.metadata.create_all(bind=engine)

class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

@app.get("/",response_class=HTMLResponse)
def index(request:Request):
    rates = fetch_rates() or {}
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"rates":rates})

@app.get("/health")
def health():
    return {"api":"ok","db":check_db_connection()}

@app.get("/api/rates")
def get_rates():
    rates = fetch_rates()
    if rates is None:
        raise HTTPException(status_code=503, detail="Сервис курсов недоступен")
    return {"base":"RUB","rates":rates}

@app.post("/api/convert")
def convert_currency(req: ConvertRequest):
    rates = fetch_rates()
    if rates is None:
        raise HTTPException(status_code=503,detail="Курсы недоступны")
    rates["RUB"]=1.0

    if req.from_currency not in rates or req.to_currency not in rates:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка. Запрошено: {req.from_currency} -> {req.to_currency}. Доступно: {list(rates.keys())[:20]}"
        )


    amount_in_rub= req.amount*rates[req.from_currency]
    result = amount_in_rub/rates[req.to_currency]

    return {"result":result}


@app.post("/register",
          response_model=schemas.UserResponse,tags=["Auth"])
def register(
        user_data:schemas.UserCreate,
        db:Session=Depends(auth.get_db)
):
    existing_user=db.query(models.User).filter(models.User.username==user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400,detail="Пользователь с таким логином уже существует")
    hashed_pwd=auth.get_password_hash(user_data.password)
    new_user=models.User(
        username=user_data.username,
        hashed_password=hashed_pwd
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login",response_model=schemas.Token,tags=["Auth"])
def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(auth.get_db)):
    user = db.query(models.User).filter(models.User.username==form_data.username).first()

    # Защита от временной атаки
    if user is None:
        dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$1/kKopFhFTmJP0aLfW15XQ$fwP4HIJ1Dwtk7Fb5XzW8HDenJ7WroA6fiz0FAynO1cA"
        auth.verify_passoword("dummy pointless password",dummy_hash)
        raise HTTPException(status_code=401,detail="Неверный логин или пароль")
    if not auth.verify_passoword(form_data.password,user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    access_token=auth.create_access_token(data={"sub",str(user.id)})
    return {"access_token":access_token,"token_type":"bearer"}

#Проверка токена
@app.get("/me",response_model=schemas.UserResponse,tags=["Auth"])
def read_users_me(current_user:models.User = Depends(auth.get_current_user)):
    return current_user

if __name__ == '__main__':
    uvicorn.run("app.main:app", reload=True)
