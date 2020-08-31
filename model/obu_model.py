from pydantic import BaseModel

class OBUModel(BaseModel):
    """
    obu信息body体
    """
    terminal_id: str  # 终端编号
    card_serial_no: str  # 卡内交易序号
    psam_serial_no: str  # PSAM流水号
    card_rnd: str  # 卡内随机数
    tac: str  # tac
    card_net_no: str  # 网络编号
    trans_before_balance: int  # 交易前余额
    deduct_amount: int  # 扣款金额
    balance: int  # 余额
    trans_type: str  # 交易类型（06：传统， 09： 复合）
    card_type: str  # etc卡片类型（22：储值卡； 23：记账卡）
    charging_type: str  # 扣费方式（0： 天线  1： 刷卡器）
    obu_id: str  # obu序号编码
    vehicle_type: str  # 收费车型
    algorithm_type: str  # 算法标识
    issuer_identifier: str  # 发行商代码
    serial_number: str  # 合同序列号
    receivable_total_amount: int  # 应收金额
    discount_amount: int  # 折扣金额


if __name__ == '__main__':
    pass