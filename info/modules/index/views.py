from . import  index_blue
from  flask import  session

@index_blue.route('/')
def index():
    session['my_name']='李华程'
    return 'hello world'

@index_blue.route('/get')
def getpage():
    session['my_name'] = '李华程'
    return 'get page'