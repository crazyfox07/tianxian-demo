from pydantic import BaseModel

class OBUModel(BaseModel):
    """
    obu信息body体
    """
    deduct_amount: float  # 扣款金额
    plate_no: str  # 车牌号


if __name__ == '__main__':
    pass