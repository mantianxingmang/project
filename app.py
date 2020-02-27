import os
import sys
import click

from flask import Flask,render_template

from flask_sqlalchemy import SQLAlchemy

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path,'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #关闭对模型修改的监控
db = SQLAlchemy(app)


#注册命令
@app.cli.command()
@click.option('--drop',is_flag=True,help='Create after drop')
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('初始化数据库。')


class User(db.Model):
    id = db.Column(db.Integer,primary_key=True) #主键
    name = db.Column(db.String(20)) #name

class Movie(db.Model):
    id =db.Column(db.Integer,primary_key=True) #主键
    title = db.Column(db.String(60)) #电影标题
    year = db.Column(db.String(4)) #电影年份

@app.cli.command()
def forge():
    db.create_all()
    name = "ZY"
    movies = [
        {'title':'杀破狼','year':'2003'},
        {'title':'扫毒','year':'2018'},
        {'title':'捉妖记','year':'2016'},
        {'title':'囧妈','year':'2020'},
        {'title':'葫芦娃','year':'1989'},
        {'title':'玻璃盒子','year':'2020'},
        {'title':'调酒师','year':'2020'},
        {'title':'釜山行','year':'2017'},
        {'title':'导火索','year':'2005'},
        {'title':'叶问','year':'2015'}
    ]
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'],year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('导入数据完成')


@app.route('/')
def index():
    # user = User.query.first()
    movies = Movie .query.all()
    return render_template('index.html',movies=movies)

#处理页面404错误
@app.errorhandler(404)
def page_not_found(e):
    # user = User.query.first()
    return render_template('404.html'),404

#模板上下文处理函数
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)