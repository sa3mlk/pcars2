#!/usr/bin/env python

from bs4 import BeautifulSoup, Tag
from urllib2 import urlopen
from operator import itemgetter

URL="http://cars2-stats-steam.wmdportal.com/index.php"

class ProjectCARS2(object):
	def __init__(self, baseurl=URL):
		self.baseurl = baseurl
		self.soup = self.__get_soup(baseurl)
		self.track_by_name = self.__get_tracks()
		self.track_by_id = self.invert_dict(self.track_by_name)
		self.vehicle_by_name = self.__get_vehicles()
		self.vehicle_by_id = self.invert_dict(self.vehicle_by_name)

	def invert_dict(self, d):
		return {v: k for k, v in d.iteritems()}

	def __get_soup(self, url):
		page = urlopen(url)
		soup = BeautifulSoup(page, "lxml")
		page.close()
		return soup

	def __get_vehicles(self):
		select = self.__tags(self.soup.find(attrs={"id": "select_leaderboard_vehicle", "name": "vehicle"}))
		vehicles = {}
		for option in select:
			vehicles[option.text] = int(option["value"])
		return vehicles

	def __get_tracks(self):
		select = self.__tags(self.soup.find(attrs={"id": "select_leaderboard_track", "name": "track"}))
		tracks = {}
		for option in select:
			tracks[option.text] = int(option["value"])
		return tracks

	def __tags(self, coll):
		return filter(lambda x: isinstance(x, Tag), coll)

	# Return the sector times in milliseconds.
	def get_sector_times(self, td):
		times = td["title"]
		sector_times = []
		for sector, mins, secs in (x.split(":") for x in td["title"].split("\n")):
			ms = int(mins)*60*1000
			secs = secs.split(".")
			ms += int(secs[0])*1000 + int(secs[1])
			sector_times.append(ms)
		return sector_times

	# Return the sum of all sector times in "m:ss.nnn"
	def format_time(self, sector_times):
		ms = sum(sector_times) if isinstance(sector_times, list) else sector_times
		return "%d:%02d.%03d" % (ms/(60*1000), (ms/1000)%60, ms%1000)

	def get_leaderboard(self, track, vehicle=0):
		track = int(track)
		vehicle = int(vehicle)
		page = urlopen(self.baseurl + "/leaderboard?track=%d&vehicle=%d" % (track, vehicle))
		soup = BeautifulSoup(page, "lxml")
		page.close()

		def get_td(tr, name):
			return tr.find("td", {"class": name})

		table = soup.find("table", id="leaderboard")
		leaderboard = []
		for tr in self.__tags(table.tbody.findAll("tr")):
			sector_times = self.get_sector_times(get_td(tr, "time"))
			leaderboard.append({
				"rank": get_td(tr, "rank").text,
				"user": get_td(tr, "user").text.strip(),
				"sector_times": sector_times,
				"time": self.format_time(sector_times),
				"vehicle": get_td(tr, "vehicle").text if vehicle == 0 else self.vehicle_by_id[vehicle],
				#"gap": get_td(tr, "gap").text,
				"timestamp": get_td(tr, "timestamp").text
			})

		return sorted(leaderboard, key=itemgetter("time"))

def main():
	pc2 = ProjectCARS2()

	#for k, v in pc2.tracks.iteritems():
	#	if "Texas" in k:
	#		print k, v

	# Texas Motor Speedway Road Course = 533066470
	lb = pc2.get_leaderboard(533066470, 3019822479)
	#lb = pc2.get_leaderboard(533066470, 1278633095)
	#lb = pc2.get_leaderboard(533066470, 4253159674)
	for row in lb:
	#	print row["time"]
		print "%-25.25s %s %s %s" % (row["user"], row["time"], row["vehicle"], row["sector_times"])

	return 0

if __name__ == "__main__":
	exit(main())
