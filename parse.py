from bs4 import BeautifulSoup
import re
import urllib

def parsePage(soup):
	pokeObjs = []
	# temp hack to use global abilities since per-set ones are broken
	"""
	Technician - 91.52 % (228550 battles)
	Swarm - 7.12 % (17773 battles)
	Light Metal - 1.36 % (3408 battles)
	"""
	abilities = []
	for abilityStr in soup.ul.find_all('li'):
		abilityStr = abilityStr.get_text()
		match = re.match(r'(.+?) - ([\d\.]+) %', abilityStr)
		if match == None:
			raise Exception("Problem finding abilities")
		abilities.append( (match.group(1),float(match.group(2))) )
	
	for start in soup.find_all('p', class_='pokemonRank', limit=5):
		pokeObj = {}
		pokeObj['abilities'] = abilities
		
		# usage | # 1 - 5.40 % (12143 battles)
		match = re.match(r'.*? - ([\d\.]+) %', start.get_text())
		pokeObj['usage'] = float(match.group(1))
			
		# name, item | Scizor @ Choice Band Lv. 100
		nameItemLine = start.find_next("p")
		match = re.match(r'(.+?) @ (.+?) Lv.', nameItemLine.get_text())
		if match == None:
			raise Exception("Problem finding a name and item")
		pokeObj['name'] = match.group(1)
		pokeObj['item'] = match.group(2)
		
		# nature+EVs | Nature: Adamant - EVs: 248 HP / 252 Atk / 8 SDef 
		natureEVLine = nameItemLine.find_next("p")
		match = re.match(r'Nature: (.+?) - EVs: (.+?)  -', natureEVLine.get_text())
		if match == None:
			raise Exception("Problem finding a nature/EVs")
		pokeObj['nature'] = match.group(1)
		evStr = match.group(2)
		evRegex = [('hp',r"(\d+) HP"), ('atk',r"(\d+) Atk"), ('def',r"(\d+) Def"), ('spa',r"(\d+) SAtk"), ('spd',r"(\d+) SDef"), ('spe',r"(\d+) Spd")];
		evs = {}
		for i in xrange(0,6):
			evName = evRegex[i][0]
			regex = evRegex[i][1]
			evs[evName] = 0
			match = re.search(regex, evStr)
			if (match != None):
				evs[evName] = int(match.group(1))
		pokeObj['evs'] = evs
		
		# moves
		"""
		Swords Dance
		Superpower
		Bullet Punch
		Bug Bite
		"""
		moves = []
		for moveStr in natureEVLine.find_next('ul').find_all('li'):
			moves.append(moveStr.get_text())
		if len(moves) != 4:
			raise Exception("Problem finding four moves")
		pokeObj['moves'] = moves
		pokeObjs.append(pokeObj)
	
	return pokeObjs
	
def pokeObjToSql(pokeObj):
	abilitiesPadded = pokeObj['abilities']
	while (len(abilitiesPadded) < 3):
		abilitiesPadded.append(('null','null'))
	st = pokeObj['evs']
	ab = pokeObj['abilities']
	mv = pokeObj['moves']
	query = "INSERT INTO usage_stats (pokemon,usage,ability1,ability1percent,ability2,ability2percent,ability3,ability3percent,item,nature,move1,move2,move3,move4,hp,atk,def,spa,spd,spe) VALUES "
	query += "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}');".format(
		pokeObj['name'],pokeObj['usage'],ab[0][0],ab[0][1],ab[1][0],ab[1][1],ab[2][0],ab[2][1],pokeObj['item'],pokeObj['nature'],mv[0],mv[1],
		mv[2],mv[3],st['hp'],st['atk'],st['def'],st['spa'],st['spd'],st['spe']
	).replace("'null'","null")
	return query
	
baseURL = "http://stats.pokemon-online.eu/Wifi%20OU/"
index = urllib.urlopen(baseURL+"index.html").read()
index = BeautifulSoup(index)

f = open("output.sql","w")
for pokeTag in index.find_all('p', class_=re.compile("Pokemon$"), limit=10):
	link, name = pokeTag.find('a')['href'],pokeTag.find('a').get_text()
	print "Getting "+name+"..."
	page = BeautifulSoup(urllib.urlopen(baseURL+link).read())
	pokeObjs = parsePage(page)
	for po in pokeObjs:
		f.write(pokeObjToSql(po)+"\n")