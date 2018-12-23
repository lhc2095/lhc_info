from . import  index_blue
from  flask import  session,render_template,current_app

@index_blue.route('/')
def index():
    session['my_name']='李华程'
    return render_template('news/index.html')


@index_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')