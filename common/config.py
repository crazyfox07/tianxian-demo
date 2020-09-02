import os

class CommonConf(object):
    # 电子标签一级分散因子，比如"万集万集"的十六进制 'CDF2BCAFCDF2BCAF'
    OBU_DIV_FACTOR = 'c9bdb6abc9bdb6ab'   # 'cdf2bcafcdf2bcaf'
    # 数据帧序列号计数器
    COUNT = 0
    # 数据帧序列号8XH中X可选数值
    RSCTL = [0, 1, 2, 3, 4, 5, 6, 7, 9]
    # 指令开始标志
    COMMAND_BEGIN_FLAG = 'ffff'
    # 指令结束标志
    COMMAND_END_FLAG = 'ff'
    # 项目根目录
    ROOT_DIR = os.path.realpath(__file__).rsplit('common')[0]
    # 日志路径
    LOG_DIR = os.path.join(ROOT_DIR, 'logs')
    # 超时时间
    TIME_OUT = 10



if __name__ == '__main__':
    pass