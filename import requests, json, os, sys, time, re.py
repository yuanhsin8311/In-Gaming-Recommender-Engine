import requests, json, os, sys, time, re
from pyspark.mllib.recommendation import ALS
from pyspark import SparkContext
import sqlalchemy
import pandas as pd


sc = SparkContext()

# set file path
path_user_inventory = '/Users/AlanLiu/game_project/data/input/user_inventory_short.txt'


def parse_raw_string(raw_string):
	user_inventory = json.loads(raw_string)
	return user_inventory.items()[0]


user_inventory_rdd = sc.textFile(path_user_inventory).map(parse_raw_string).zipWithIndex()


def id_index(x):
	((user_id,lst_inventory),index) = x
	return (index, user_id)


dic_id_index = user_inventory_rdd.map(id_index).collectAsMap()


def create_tuple(x):
	((user_id,lst_inventory),index) = x
	if lst_inventory != None:
		return (index, [(i.get('appid'), i.get('playtime_forever')) for i in lst_inventory if i.get('playtime_forever') > 0])
	else:
		return (index, [])

training_rdd = user_inventory_rdd.map(create_tuple).flatMapValues(lambda x: x).map(lambda (index,(appid,time)):(index,appid,time))

model = ALS.train(training_rdd, 10)

dic_recommended = {'g0':{},'g1':{},'g2':{},'g3':{},'g4':{},'g5':{},'g6':{},'g7':{},'g8':{},'g9':{}}
for index in dic_id_index.keys():
	try:
		lst_recommended = [i.product for i in model.recommendProducts(index,10)]
		user_id = dic_id_index.get(index)
		rank = 0
		for app_id in lst_recommended:
			dic_recommended['g%s'%rank].update({user_id:app_id})
			rank+=1
	except:
		pass


engine = sqlalchemy.create_engine('mysql+pymysql://:@127.0.0.1/game_recommendation?charset=utf8mb4')

df = pd.DataFrame(dic_recommended)
df.index.name = 'user_id'
df = df.reset_index()
df.to_sql('tbl_recommended_games', engine, if_exists='replace')









