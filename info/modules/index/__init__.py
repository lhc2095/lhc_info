from flask import Blueprint

index_blue=Blueprint('index_blue',__name__)

from . import views   # 导入视图函数
