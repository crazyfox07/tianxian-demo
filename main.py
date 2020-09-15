import uvicorn
import os
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from common.config import CommonConf
from common.log import logger
from model.db_orm import init_db
from model.obu_model import OBUModel
from service.check_rsu_status import RsuStatus
from service.etc_toll import ETCToll
from service.third_etc_api import ThirdEtcApi

app = FastAPI()

# scheduler = AsyncIOScheduler()
scheduler = BackgroundScheduler()


@app.on_event('startup')
def init_rsu():
    """
    初始化天线，主要用于心跳检测
    :return:
    """
    RsuStatus.init_rsu_status_list()


@app.on_event('startup')
def create_sqlite():
    """数据库初始化"""
    init_db()


@app.on_event('startup')
def init_scheduler():
    """初始化调度器"""
    job_sqlite_path = os.path.join(CommonConf.SQLITE_DIR, 'jobs.sqlite')
    # 每次启动任务时删除数据库
    os.remove(job_sqlite_path) if os.path.exists(job_sqlite_path) else None
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///' + job_sqlite_path)  # SQLAlchemyJobStore指定存储链接
    }
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 10},  # 最大工作线程数20
        'processpool': ProcessPoolExecutor(max_workers=1)  # 最大工作进程数为5
    }

    scheduler.configure(jobstores=jobstores, executors=executors)

    # scheduler.add_job(ThirdEtcApi.my_job1, trigger='cron', minute="*/2")
    # scheduler.add_job(ThirdEtcApi.my_job2, trigger='cron', minute="*/5")
    # scheduler.add_job(ThirdEtcApi.download_blacklist_base, trigger='cron', hour='1')
    # scheduler.add_job(ThirdEtcApi.download_blacklist_incre, trigger='cron', hour='*/1')
    scheduler.add_job(ThirdEtcApi.reupload_etc_deduct_from_db, trigger='cron', hour='*/1')
    scheduler.add_job(RsuStatus.timing_update_rsu_status_list, trigger='cron', second='*/30',
                      kwargs={'callback': ThirdEtcApi.tianxian_heartbeat})
    # scheduler.add_job(ThirdEtcApi.tianxian_heartbeat, trigger='cron', second='*/20')
    logger.info("启动调度器...")

    scheduler.start()


@app.post("/etc_fee_deduction")
def etc_fee_deduction(body: OBUModel):
    """
    etc扣费
    :param body:
    :return:
    """
    result = ETCToll.toll(body)
    return result


@app.get('/')
def head():
    return dict(hello='world')


if __name__ == '__main__':
    # TODO workers>1时有问题，考虑gunicorn+uvicorn，同时考虑多进程的定时任务问题
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001)
