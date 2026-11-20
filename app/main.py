from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel

from app.database import check_db_connection,engine,Base
from app import models

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

if __name__ == '__main__':
    uvicorn.run("app.main:app", reload=True)
