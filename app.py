from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "这是我的项目首页!!"