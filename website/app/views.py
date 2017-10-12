from app import app
from flask import render_template
import json
import sqlalchemy
from sqlalchemy import create_engine, MetaData

#app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4'
# json.dump(dic_recommended, open(path_recommended_games, 'wb'), indent=3)
#engine = sqlalchemy.create_engine('mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4')

engine = create_engine('mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4', convert_unicode=True)
metadata = MetaData(bind=engine)



@app.route('/')
@app.route('/index')
def index():
    #return "Hello, World!\n\nAppend /recommendation/<userid> to the current url\n\nSome availble userids: 76561198249026172, 76561198082481473, 76561198040992485, 76561197960464402"
    return render_template('index.html')


@app.route('/recommendation/<user_id>')
def recommendation(user_id):
	
	result = engine.execute('SELECT g0,g1,g2,g3,g4,g5,g6,g7,g8,g9 FROM tbl_recommend_games WHERE user_id= %s;' % user_id).first()

	lst_recommended_games = []
	for app_id in list(result):
		app_data = engine.execute('SELECT name,initial_price,header_image FROM tbl_steam_app WHERE steam_appid = %s;' % app_id).first()
		if app_data != None:
			lst_recommended_games.append(app_data)

	# lst_recommended_game_url = [dic_image_url.get(str(i), None) for i in dic_recommended.get(str(userid))]

#current_time=datetime.datetime.now()

	return render_template('recommendationR.html',
							user_id = user_id,
							lst_recommended_games = lst_recommended_games)

@app.route('/gamerecommender')
def gamerecommender():
    
    return render_template('index.html')

@app.route('/tracking')
def tracking():
    
    return render_template('tracking.html')


if __name__ == '__main__':
    app.run('127.0.0.1', 5000) 
