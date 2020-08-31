import uvicorn
import time
import threading
from pprint import pprint
from fastapi import FastAPI
from fastapi.encoders import  jsonable_encoder
from func_timeout import func_set_timeout

from model.obu_model import OBUModel
from socket_client import tianxian_demo

app = FastAPI()


@func_set_timeout(3)
def f1():
    time.sleep(20)

@app.get("/", response_model=OBUModel)
def home():
    start = time.time()
    print('1111')
    try:
        f1()
    except:
        print('3333')
    end = time.time()
    print('time use: {}s'.format(end - start))
    json_compatible_item_data = jsonable_encoder(OBUModel )
    # command_recv_set = tianxian_demo()
    # # 交易结束，打印信息
    # print('b0-------------------------------------------------------------------')
    # pprint(command_recv_set.info_b0)
    # print('b2-------------------------------------------------------------------')
    # pprint(command_recv_set.info_b2)
    # print('b3-------------------------------------------------------------------')
    # pprint(command_recv_set.info_b3)
    # print('b4-------------------------------------------------------------------')
    # pprint(command_recv_set.info_b4)
    # print('b5-------------------------------------------------------------------')
    # pprint(command_recv_set.info_b5)
    return OBUModel


@app.get('/hello/{name}')
async def hello(name: str, age: int=20 ):
    # time.sleep(10)
    threading.Event().wait(10)
    return {'name': name, 'age': age}


@app.post('/obu')
def obu_info(data: OBUModel):
    data = {
        "method": "etcPayUpload",
        "params": {
            "algorithm_type": "1",
            "balance": 43070,
            "card_net_no": "3702",
            "card_rnd": "75A6E727",
            "card_serial_no": "0419",
            "card_sn": "1303220100390927",
            "card_type": "22",
            "charging_type": "0",
            "deduct_amount": 300,
            "device_no": "Showlinx-0000000013",
            "device_type": "0",
            "discount_amount": 0,
            "entrance_time": "20200828104818",
            "exit_time": "20200828111728",
            "issuer_identifier": "C9BDB6AB37010001",
            "obu_id": "070C062A",
            "park_code": "371157",
            "park_record_time": "28分钟",
            "plate_color_code": "0",
            "plate_no": "鲁RK3679",
            "plate_type_code": "0",
            "psam_id": "37010101000000295602",
            "psam_serial_no": "000026EC",
            "receivable_total_amount": 300,
            "serial_number": "3701071521078758",
            "tac": "CC688326",
            "terminal_id": "0137000482B2",
            "trans_before_balance": 43370,
            "trans_order_no": "1818620411622008757",
            "trans_type": "09",
            "vehicle_type": "1"
        }
    }
    return data

if __name__ == '__main__':
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True, debug=True)


























