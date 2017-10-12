file = open('game_inventory','w')

steam_user = open('/users/yuanhsinhuang/desktop/projects/recommender/steam_user_id.txt','r')
a = steam_user.readlines()

for line in a:
    my_list = []
    import requests
    key = 'E0D8D21FA06CCD7A1781F6D1D23B68CC'
    steamid = line
    url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='+ key + '&' + 'steamid=' + steamid + '&' + 'format=json'
    data = requests.get(url)
    js = data.json()['response']['games']
    print dict(my_list.append(line) + ':'.join(js))


import subprocess
with open("game_inventory.txt", "w+") as output:
    subprocess.call(["python", "./Test.py"], stdout=output)
