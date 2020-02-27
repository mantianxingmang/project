import os
import sys
import click

from flask import Flask,render_template,request,url_for,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path,'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev'
db = SQLAlchemy(app)


login_manager = LoginManager(app) #实例化扩展类
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user
login_manager.login_view = 'login'
login_manager.login_message = '请登录'


class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True) #主键
    name = db.Column(db.String(20)) #name
    username = db.Column(db.String(20))  # 用户名
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self,password):
        return check_password_hash(self.password_hash,password)

class Movie(db.Model):
    id =db.Column(db.Integer,primary_key=True) #主键
    title = db.Column(db.String(60)) #电影标题
    year = db.Column(db.String(4)) #电影年份


#注册命令
@app.cli.command()
@click.option('--drop',is_flag=True,help='Create after drop')
def initdb(drop):
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('初始化数据库。')


#导入数据
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


#生成管理员账户
@app.cli.command()
@click.option('--username',prompt=True,help='用户名')
@click.option('--password',prompt=True,help='密码',confirmation_prompt=True)
def admin(username,password):
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('更新用户')
        user.username = username
        user.set_password(password)
    else:
        click.echo('创建用户')
        user = User(username=username,name="ZY")
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('创建管理员账号完成')


#首页
@app.route('/',methods=['GET','POST'])
def index():
    # user = User.query.first()
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        title = request.form.get('title')
        year =request.form.get('year') 
        #验证数据不为空，yeas长度不能超过4，title长度不能超过60
        if not title or not year or len(year)>4 or len(title)>60:
            flash('输入错误')
            return redirect(url_for('index'))
        movie = Movie(title=title,year=year)
        db.session.add(movie)
        db.session.commit()
        flash('数据插入成功')
        return redirect(url_for('index'))

    movies = Movie .query.all()
    return render_template('index.html',movies=movies)

#编辑视图函数
@app.route('/movie/edit/<int:movie_id>',methods=['GET','POST'])
@login_required
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year)>4 or len(title)>60:
            flash('输入错误')
            return redirect(url_for('edit'),movie_id=movie_id)

        movie.title = title
        movie.year = year
        db.session.commit()
        flash('数据编辑成功')
        return redirect(url_for('index'))
    return render_template('edit.html',movie=movie)


#删除
@app.route('/movie/delete/<int:movie_id>',methods=['POST']) 
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('删除数据成功')
    return redirect(url_for('index'))


#登录
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('输入错误')
            return redirect(url_for('login'))

        user = User.query.first()
        #验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登录用户
            flash('登录成功')
            return redirect(url_for('index'))  # 登录成功返回首页

        flash('用户名或密码输入错误')
        return redirect(url_for('login'))
    return render_template('login.html')


#退出
@app.route('/logout')
def logout():
    logout_user()
    flash('退出用户')
    return redirect(url_for('index'))


#设置
@app.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name)>20:
            flash('输入错误')
            return redirect(url_for('settings'))
        
        current_user.name = name
        db.session.commit()
        flash('设置name成功')
        return redirect(url_for('index'))

    return render_template('settings.html')



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