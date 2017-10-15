from pyspark.mllib.recommendation import ALS
from pyspark import SparkContext
import sqlalchemy
import json
import pandas as pd
import math
from pyspark.sql import SQLContext

sc = SparkContext()


path_user_inventory = '/users/yuanhsinhuang/desktop/projects/recommender/steam_user_inventory.txt'


# parse the crawled data set
def parse_new_string(raw_string):
    user_inventory = json.loads(raw_string)
    user_id = list(user_inventory.keys())[0]
    if user_inventory[user_id]['response'] != {} and user_inventory[user_id]['response']['game_count'] != 0:
        user_inventory = user_inventory[user_id]['response']['games']
    else:
        user_inventory = {}
    return user_id, user_inventory

# represent 'steam_appid' with index
user_inventory_rdd = sc.textFile(path_user_inventory).map(parse_new_string).zipWithIndex()

# build relationship between 'steam_appid' and 'index'
def id_index(x):
    ((user_id, lst_inventory), index) = x
    return index, user_id

dict_id_index = user_inventory_rdd.map(id_index).collectAsMap()


# create training rdd => format in (index, appid, playtime_forever)
def create_tuple(x):
    ((user_id, lst_inventory), index) = x
    if lst_inventory != {}:
        return index, [(i.get('appid'), i.get('playtime_forever'))
                       for i in lst_inventory if i.get('playtime_forever') > 0]
    else:
        return index, []

training_rdd = user_inventory_rdd.map(create_tuple).flatMapValues(lambda x: x).map(lambda x: (x[0], x[1][0], x[1][1]))

print "There are %s games in the complete dataset" % (training_rdd.count())


## mean
def get_counts_and_averages(ID_and_ratings_tuple):
    nratings = len(ID_and_ratings_tuple[1])
    return ID_and_ratings_tuple[0], (nratings, float(sum(x for x in ID_and_ratings_tuple[1]))/nratings)

app_ID_with_minutes_RDD = (training_rdd.map(lambda x: (x[1], x[2])).groupByKey())
app_ID_with_avg_minutes_RDD = app_ID_with_minutes_RDD.map(get_counts_and_averages)
app_counts_RDD = app_ID_with_avg_minutes_RDD.map(lambda x: (x[0], x[1][0]))
app_avg_minutes_RDD = app_ID_with_avg_minutes_RDD.map(lambda x: (x[0], x[1][1]))

print app_ID_with_avg_minutes_RDD.count
print app_counts_RDD
print app_avg_minutes_RDD


top_app = app_counts_RDD.takeOrdered(10, key=lambda x: -x[1])
print ('TOP Downloaded app_id :\n%s' % '\n'.join(map(str, top_app)))
top_app_play_time = app_avg_minutes_RDD.takeOrdered(10, key=lambda x: -x[1])
print ('TOP Play Time app_id :\n%s' % '\n'.join(map(str, top_app_play_time)))





#for i in range(len(file_new[['name']])):
#    print file_new['name'].iloc[i]

#if top_app[i][0] == file_new['steam_appid'] 
#print file_new['name'].iloc[i]




## Split sample data
training_RDD, validation_RDD, test_RDD = training_rdd.randomSplit([6,2,2], seed=0L) 
print training_RDD.count(), validation_RDD.count(),test_RDD.count()


validation_for_predict_RDD = validation_RDD.map(lambda x: (x[0], x[1]))
test_for_predict_RDD = test_RDD.map(lambda x: (x[0], x[1]))


## Training 
seed = 5L
iterations = 10
regularization_parameter = 0.1
ranks = [3,6,9,12]
errors = [0, 0, 0]
err = 0
tolerance = 0.02

min_error = float('inf')
best_rank = -1
best_iteration = -1

for rank in ranks:
    model = ALS.train(training_RDD, rank, seed=seed, iterations=iterations,
                      lambda_=regularization_parameter)
    predictions = model.predictAll(validation_for_predict_RDD).map(lambda r: ((r[0], r[1]), r[2]))
    rates_and_preds = validation_RDD.map(lambda r: ((int(r[0]), int(r[1])), float(r[2]))).join(predictions)
    error = math.sqrt(rates_and_preds.map(lambda r: (r[1][0] - r[1][1])**2).mean())
    errors[err] = error
    err += 1
    print 'For rank %s the RMSE is %s' % (rank, error)
    if error < min_error:
        min_error = error
        best_rank = rank

#print 'The best model was trained with rank %s' % best_rank   
#print 'For testing data the RMSE is %s' % (error)


# test
test_for_predict_RDD = test_RDD.map(lambda x: (x[0], x[1]))

predictions = model.predictAll(test_for_predict_RDD).map(lambda r: ((r[0], r[1]), r[2]))
rates_and_preds = test_RDD.map(lambda r: ((int(r[0]), int(r[1])), float(r[2]))).join(predictions)
error = math.sqrt(rates_and_preds.map(lambda r: (r[1][0] - r[1][1])**2).mean())
    
print 'For testing data the RMSE is %s' % (error)




# '5' stands for feature dimension; default value is '3'
model = ALS.train(training_RDD, 3)


# make the recommendation
dic_recommend = {'g0':{}, 'g1':{}, 'g2':{},'g3':{}, 'g4':{}, 'g5':{},'g6':{}, 'g7':{}, 'g8':{}, 'g9':{}}
for index in dict_id_index.keys():
    try:
        if index % 200 == 0:
            print('working on ', index)
        lst_recommend = [i.product for i in model.recommendProducts(index, 10)]
        user_id = dict_id_index.get(index)
        rank = 0
        for app_id in lst_recommend:
            dic_recommend['g%s'%rank].update({user_id:app_id})
            rank+=1
    except:
        pass


# output to the mySQL database
engine = sqlalchemy.create_engine('mysql+pymysql://root:Abcd0101@127.0.0.1/game_recommendation?charset=utf8mb4')
df = pd.DataFrame(dic_recommend)
df.index.name = 'user_id'
df = df.reset_index()
df.to_sql('tbl_recommend_games', engine, if_exists='replace')













