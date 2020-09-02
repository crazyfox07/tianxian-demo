import uvicorn
from fastapi import FastAPI
from model.obu_model import OBUModel
from service.etc_toll import ETCToll

app = FastAPI()

# 引入模块路由
# app.include_router(router=etc_router, prefix='/etc_router')


@app.post("/etc-fee-deduction")
def etc_fee_deduction(body: OBUModel):
    ip_tianxian = '192.168.1.69'
    deduct_amonut = body.deduct_amount
    plate_no = body.plate_no
    result = ETCToll.toll(tianxian_ip=ip_tianxian, port=60001, money=deduct_amonut)
    print(result)
    return result


@app.get('/hello/{name}')
async def hello(name: str, age: int = 20):
    return {'name': name, 'age': age}


@app.get('/')
def head():
    return dict(hello='world')


if __name__ == '__main__':
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001, reload=True, debug=True)
