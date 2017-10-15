from app import app
from flask import render_template, Response, request
import json
import sqlalchemy
from sqlalchemy import create_engine, MetaData
from flask import Flask, jsonify, render_template, redirect, url_for
from flask.ext.cors import CORS
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
import csv


#app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4'
# json.dump(dic_recommended, open(path_recommended_games, 'wb'), indent=3)
#engine = sqlalchemy.create_engine('mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4')

engine = create_engine('mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4', convert_unicode=True)
metadata = MetaData(bind=engine)

class ResultEntry:
    def __init__(self, mean_value):
        self.mean_value = mean_value
        self.recommend_list_text = ''
        self.cat_name = ''
        self.outputlier_list_text = ''

class BarChartEntry:
    def __init__(self):
        self.name_list = []
        self.value_list_text = ''
        self.play_name_list = []
        self.play_value_list_text = ''

class KmeansEntry:
    def __init__(self):
        self.g0_list_text = ''
        self.g1_list_text = ''
        self.g2_list_text = ''


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
    # Play1: high recommendation -> price tier 
	query1 = engine.execute('SELECT case when initial_price=0 then "free" when initial_price between 1 and 20 then "mass" when initial_price>20 then "masstige" else "uncertain" end as price_tier,recommendation FROM tbl_steam_app order by recommendation desc;')
	#user_id = 76561197972183630
	#query1 = engine.execute('SELECT g0,g1,g2,g3,g4,g5,g6,g7,g8,g9 FROM tbl_recommend_games WHERE user_id= %s;' % user_id).first()
	#query1 = engine.execute('SELECT g0,g1,g2,g3,g4,g5,g6,g7,g8,g9 FROM tbl_recommend_games WHERE user_id= 76561197972183630;')
	# Play2: 

	outputlier_list_text = ''
	free_data_list = []
	mass_data_list = []
	masstige_data_list = []
	uncertain_data_list = []
	all_data_list = []
	#counter = 0
	for each_entry in query1:
		all_data_list.append(each_entry['recommendation'])
		if each_entry['price_tier'] == 'free':
			#counter = counter + 1
			free_data_list.append(each_entry['recommendation'])
		elif each_entry['price_tier'] == 'mass':
			mass_data_list.append(each_entry['recommendation'])
		elif each_entry['price_tier'] == 'masstige':
			masstige_data_list.append(each_entry['recommendation'])
		else: #elif each_entry['price_tier'] == 'uncertain':
			uncertain_data_list.append(each_entry['recommendation'])

	data = np.array(free_data_list)
	B=plt.boxplot(data)
	low = B['whiskers'][0].get_ydata()[1]
	q1 = B['whiskers'][0].get_ydata()[0]
	medium = np.median(data)
	q3 = B['whiskers'][1].get_ydata()[0]
	high = B['whiskers'][1].get_ydata()[1]
	recommend_list_text = '[' + str(low) + ', ' + str(q1) + ', ' + str(medium) + ', ' + str(q3) + ', ' + str(high) + ']'
	free_data_list.sort()
	if free_data_list[0] < low:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[0, ' + str(free_data_list[0]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [0, ' + str(free_data_list[0]) + ']'
	if free_data_list[-1] > high:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[0, ' + str(free_data_list[-1]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [0, ' + str(free_data_list[-1]) + ']'

	data = np.array(mass_data_list)
	B=plt.boxplot(data)
	low = B['whiskers'][0].get_ydata()[1]
	q1 = B['whiskers'][0].get_ydata()[0]
	medium = np.median(data)
	q3 = B['whiskers'][1].get_ydata()[0]
	high = B['whiskers'][1].get_ydata()[1]
	recommend_list_text = recommend_list_text + ', [' + str(low) + ', ' + str(q1) + ', ' + str(medium) + ', ' + str(q3) + ', ' + str(high) + ']'
	mass_data_list.sort()
	if mass_data_list[0] < low:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[1, ' + str(mass_data_list[0]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [1, ' + str(mass_data_list[0]) + ']'
	if mass_data_list[-1] > high:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[1, ' + str(mass_data_list[-1]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [1, ' + str(mass_data_list[-1]) + ']'

	data = np.array(masstige_data_list)
	B=plt.boxplot(data)
	low = B['whiskers'][0].get_ydata()[1]
	q1 = B['whiskers'][0].get_ydata()[0]
	medium = np.median(data)
	q3 = B['whiskers'][1].get_ydata()[0]
	high = B['whiskers'][1].get_ydata()[1]
	recommend_list_text = recommend_list_text + ', [' + str(low) + ', ' + str(q1) + ', ' + str(medium) + ', ' + str(q3) + ', ' + str(high) + ']'
	masstige_data_list.sort()
	if masstige_data_list[0] < low:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[2, ' + str(masstige_data_list[0]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [2, ' + str(masstige_data_list[0]) + ']'
	if masstige_data_list[-1] > high:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[2, ' + str(masstige_data_list[-1]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [2, ' + str(masstige_data_list[-1]) + ']'

	data = np.array(uncertain_data_list)
	B=plt.boxplot(data)
	low = B['whiskers'][0].get_ydata()[1]
	q1 = B['whiskers'][0].get_ydata()[0]
	medium = np.median(data)
	q3 = B['whiskers'][1].get_ydata()[0]
	high = B['whiskers'][1].get_ydata()[1]
	recommend_list_text = recommend_list_text + ', [' + str(low) + ', ' + str(q1) + ', ' + str(medium) + ', ' + str(q3) + ', ' + str(high) + ']'
	uncertain_data_list.sort()
	if uncertain_data_list[0] < low:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[3, ' + str(uncertain_data_list[0]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [3, ' + str(uncertain_data_list[0]) + ']'
	if masstige_data_list[-1] > high:
		if outputlier_list_text == '':
			outputlier_list_text = outputlier_list_text + '[3, ' + str(uncertain_data_list[-1]) + ']'
		else:
			outputlier_list_text = outputlier_list_text + ', [3, ' + str(uncertain_data_list[-1]) + ']'

	data = np.array(all_data_list)
	medium = np.median(data)
	mean_value = medium

	#recommend_list_text = str(1) + ', ' + str(2) + ', ' + str(3) + ', ' + str(4) + ', ' + str(5)
	#recommend_list_text = '[' + str(1) + ', ' + str(2) + ', ' + str(3) + ', ' + str(4) + ', ' + str(5) + ']' + ', [' + str(1) + ', ' + str(2) + ', ' + str(3) + ', ' + str(4) + ', ' + str(5) + ']'
	#mean_value = 3

	result_entry = ResultEntry(mean_value)
	result_entry.recommend_list_text = recommend_list_text
	result_entry.cat_name = 'free, mass, masstige, uncertain'
	result_entry.outputlier_list_text = outputlier_list_text

    #return redirect(url_for('static', filename='graph1.html'))
	return render_template('test2.html',
							result_entry = result_entry)

@app.route('/barchart')
def barchart():
	#query3 = engine.execute('select ')
	mybar = BarChartEntry()
	ifile = open('/Users/yuanhsinhuang/Desktop/Projects/Recommender/down.csv', "rb")
	reader = csv.reader(ifile)
	rownum = 0
	for row in reader:
		if rownum ==0:
			header = row
			#mybar.name_list = header
		else:
			if mybar.value_list_text == '': 
				mybar.value_list_text = row[1]
			else:
				mybar.value_list_text = mybar.value_list_text + ', ' + row[1]
			mybar.name_list.append(row[0])
			 
		rownum = rownum + 1
	ifile.close()

	ifile = open('/Users/yuanhsinhuang/Desktop/Projects/Recommender/play.csv', "rb")
	reader = csv.reader(ifile)
	rownum = 0
	for row in reader:
		if rownum ==0:
			header = row
			#mybar.name_list = header
		else:
			if mybar.play_value_list_text == '': 
				mybar.play_value_list_text = row[1]
			else:
				mybar.play_value_list_text = mybar.play_value_list_text + ', ' + row[1]
			mybar.play_name_list.append(row[0])
			 
		rownum = rownum + 1
	ifile.close()

	result_entry = mybar
	return render_template('test3.html',
							result_entry = result_entry)

@app.route('/my_kmean')
def my_kmean():
	query1 = engine.execute('SELECT initial_price,recommendation FROM tbl_steam_app;')

	my_kmeans = KmeansEntry()
	list_all_points = []
	for each_entry in query1:
		list_all_points.append([each_entry['initial_price'], each_entry['recommendation']])

	X_array = np.array(list_all_points)
	kmeans = KMeans(n_clusters=3, random_state=0).fit(X_array)
	labels = kmeans.labels_
	index_i = 0
	for each_point in list_all_points:
		label_index = labels[index_i]
		if label_index == 0:
			if my_kmeans.g0_list_text == '': 
				my_kmeans.g0_list_text = '[' + str(each_point[0]) + ', ' + str(each_point[1]) + ']'
			else:
				my_kmeans.g0_list_text = my_kmeans.g0_list_text + ', [' + str(each_point[0]) + ', ' + str(each_point[1]) + ']'
		elif label_index == 1:
			if my_kmeans.g1_list_text == '': 
				my_kmeans.g1_list_text = '[' + str(each_point[0]) + ', ' + str(each_point[1]) + ']'
			else:
				my_kmeans.g1_list_text = my_kmeans.g1_list_text + ', [' + str(each_point[0]) + ', ' + str(each_point[1]) + ']'
		else:
			if my_kmeans.g2_list_text == '': 
				my_kmeans.g2_list_text = '[' + str(each_point[0]) + ', ' + str(each_point[1]) + ']'
			else:
				my_kmeans.g2_list_text = my_kmeans.g2_list_text + ', [' + str(each_point[0]) + ', ' + str(each_point[1]) + ']'
		index_i = index_i + 1

	result_entry = my_kmeans
	return render_template('test5.html',
							result_entry = result_entry)










if __name__ == '__main__':
    app.run('127.0.0.1', 5000) 



  
	



