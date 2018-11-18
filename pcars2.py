#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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
		return "%02d:%02d.%03d" % (ms/(60*1000), (ms/1000)%60, ms%1000)

	def get_leaderboard(self, track, vehicle=0, index=1):
		track = int(track)
		vehicle = int(vehicle)
		page = urlopen(self.baseurl + "/leaderboard?track=%d&vehicle=%d&page=%d" % (track, vehicle, index))
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
				"gap": get_td(tr, "gap").text,
				"timestamp": get_td(tr, "timestamp").text
			})

		# Test for more pages
		if len(leaderboard) == 100:
			leaderboard += self.get_leaderboard(track, vehicle, index+1)

		return sorted(leaderboard, key=itemgetter("time"))

	def print_leaderboard(self, lb):
		for row in lb:
			print "%s: %-25.25s %s %s %s" % (
				row["rank"],
				row["user"],
				row["time"],
				row["vehicle"],
				row["gap"]
			)

def main():
	pc2 = ProjectCARS2()

	# Download the complete leaderboard for Nissan GT-R Nismo GT3 for Nürburgring Nordschleife
	lb = pc2.get_leaderboard(697498609, 2878763807)
	pc2.print_leaderboard(lb)

	"""for track_name, track_id in pc2.track_by_name.iteritems():
		try:
			print "Getting leaderboard for %s [overall best]" % track_name
			pc2.print_leaderboard(pc2.get_leaderboard(track_id))
		except TypeError:
			print "This leaderboard contains no data"
		raw_input()"""

	return 0

if __name__ == "__main__":
	exit(main())
