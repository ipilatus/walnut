import pytz
from sqlalchemy.ext.declarative import declarative_base

tz = pytz.timezone('Asia/Shanghai')  # 时区
fmt = '%Y-%m-%d %H:%M:%S'  # 时间格式
base = declarative_base()  # sqlalchemy model base class
