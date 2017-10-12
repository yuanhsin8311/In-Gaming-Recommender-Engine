import requests, json, os, sys, time, random
from datetime import datetime
from multiprocessing import Pool


def split_list(lst_long,n):
	lst_splitted = []
	if len(lst_long) % n == 0:
		totalBatches = len(lst_long) / n
	else:
		totalBatches = len(lst_long) / n + 1
	for i in xrange(totalBatches):
		lst_short = lst_long[i*n:(i+1)*n]
		lst_splitted.append(lst_short)
	return lst_splitted



def show_work_status(singleCount, totalCount, currentCount=0):
	currentCount += singleCount
	percentage = 1. * currentCount / totalCount * 100
	status =  '+' * int(percentage)  + '-' * (100 - int(percentage))
	sys.stdout.write('\rStatus: [{0}] {1:.2f}% '.format(status, percentage))
	sys.stdout.flush()
	if percentage >= 100:
		print '\n'


############################################################
### crawler 1: get game inventory of each steam user id ####
############################################################

def worker(lst_steam_id):
	time.sleep(random.random()+random.randint(2,5))
	dic_temp = {}
	for user_id in lst_steam_id:
		base_url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
		params = {
			'key' : 'E0D8D21FA06CCD7A1781F6D1D23B68CC',		# replace with your steam api key
			'steamid' : user_id,
			'format' : 'json' }
		r = requests.get(base_url, params = params)
		user_inventory = r.json().get('response').get('games')
		dic_temp.update({user_id:user_inventory})
		time.sleep(.1)
	return dic_temp


if __name__ == '__main__':
	path_user_id = '/Users/yuanhsinhuang/desktop/projects/recommender/data/input/steam_user_id.txt'		# 5k user ids to crawl
	path_user_inventory = '/Users/yuanhsinhuang/desktop/projects/recommender/data/output/%s_user_inventory.json' % (datetime.today().isoformat()[:10])
	

	with open(path_user_id, 'rb') as f:
		set_user_id = set(f.read().splitlines())

	if os.path.exists(path_user_inventory):
		with open(path_user_inventory, 'rb') as f:
			json_crawled_data = json.load(f)
			set_crawled_user_id = set(json_crawled_data.keys())
	else:
		json_crawled_data = {}
		set_crawled_user_id = set([])

	total_count = len(set_user_id)
	current_count = len(set_crawled_user_id)
	lst_remaining_id = list(set_user_id - set_crawled_user_id)

	p = Pool(20)
	for lst_steam_id in split_list(lst_remaining_id,1000):
		lst_temp_dic = p.map(worker, split_list(lst_steam_id,50))
		for dic_temp in lst_temp_dic:
			json_crawled_data.update(dic_temp)
		
		with open(path_user_inventory,'wb') as f:    # optional: need to update
			json.dump(json_crawled_data,f)

		show_work_status(len(lst_steam_id), total_count, current_count)
		current_count += len(lst_steam_id)


####################################
#### crawler 2: get app details ####
####################################

r = requests.get('http://steamspy.com/api.php?request=all')
dic_app_user = r.json()

path_app_user = '/Users/yuanhsinhuang/desktop/projects/recommender/data/output/path_app_user.json'

with open(path_app_user, 'wb') as f:
	json.dump(dic_app_user, f)

lst_app_id = dic_app_user.keys()
total_count = len(lst_app_id)
current_count = 0
print current_count, total_count

path_app_info = '/Users/yuanhsinhuang/desktop/projects/recommender/data/output/path_app_info.json'
with open(path_app_info, 'wb') as f:
	for app_id in lst_app_id:
		url_app_detail = ('http://store.steampowered.com/api/appdetails?appids=%s') % (app_id)
		for i in range(3):		# try no more than 3 times for each app id
			try:
				r = requests.get(url_app_detail)
				result = r.json()	# we know the result is in JSON format, so use json() to parse it from text directly
				break			# if all scripts under try block was run successfully, we get what we need. Break the loop and move onto the next app id
			except:	
				time.sleep(5)
				pass 			# otherwise, continue for loop and try to send the http request again
		f.write(json.dumps(result))
		f.write('\n')
		current_count += 1
		if current_count % 200 == 0:
			time.sleep(300)		# this API endpoint has a limit of 200 calls per 5 min
		else:
			time.sleep(.5)