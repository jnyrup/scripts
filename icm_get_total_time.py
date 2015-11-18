#!/usr/bin/env python3
"""Script to accumulate the runtime for all movies from a csv file from iCheckMovies
	It tries to get runtime information from OMDb API and IMDb if it is not available
	on OMDb API.
	The first row is expected to be headers"""
import sys, os, csv, requests
from bs4 import BeautifulSoup

class Stats:
	skipped = 0
	runtimes = []

	def print(self):
		self.runtimes.sort()
		min_value = self.runtimes[0]
		max_value = self.runtimes[-1]
		median_value = median(self.runtimes)
		total = sum(self.runtimes)
		counted = len(self.runtimes)
		avg_value = total / counted

		hours, minutes = divmod(total, 60)
		days, hours = divmod(hours, 24)

		print("%d days, %d hours and %d minutes" % (days, hours, minutes))
		print("%d counted, %d skipped, %d in total" % (counted, self.skipped, (counted + self.skipped)))
		print("min: %d, max: %d, median: %d, avg %d" % (min_value, max_value, median_value, avg_value))

	def add(self, time):
		self.runtimes.append(time)

	def skip(self):
		self.skipped += 1

def get_from_imdb(session, imdb_url):
	response = session.get(imdb_url, stream=True)
	for line in response.iter_lines():
		if str(line).endswith(' min\''):
			return int(str(line).split()[1])
	return False

def median(lst):
	lstLen = len(lst)
	index = (lstLen - 1) // 2

	if (lstLen % 2):
		return lst[index]
	else:
		return (lst[index] + lst[index + 1])/2.0

def getTime(session, csv_file):
	csv_reader = csv.reader(csv_file)
	stats = Stats()
	
	# skip header and get index of column imdburl
	imdb_url_index = next(csv_reader).index('imdburl')
	for row in csv_reader:
		imdb_url = row[imdb_url_index]
		imdb_id = imdb_url[-10:-1]
		response = session.get("http://www.omdbapi.com/?plot=short&i=" + imdb_id)

		if response.status_code != 200:
			print("connection problems, try later")
			sys.exit()

		info = response.json()
		if info['Response'] != 'True': 
			print(info)
			stats.skip()
			continue

		title = info['Title']
		media_type = info['Type']
		if media_type != 'movie':
			print('"%s" (%s) is of type "%s", skipping' % (title, imdb_id, media_type))
			stats.skip()
			continue

		try:
			time = int(info['Runtime'][:-4])
		except ValueError:
			time = get_from_imdb(session, imdb_url)
			if time == False:
				print('"%s" (%s) has no info on omdbapi/IMDb' % (title, imdb_id))
				stats.skip()
				continue

		stats.add(time)

	stats.print()

def main():
	args = sys.argv[1:]
	with requests.Session() as session:
		if len(args) == 1:
			#argument is local file
			input_file = args[0]
			if not os.path.isfile(input_file):
				print("%s is not a file (did you mispell something?)" % input_file)
				sys.exit()
			with open(input_file, encoding='latin-1') as csv_file:
				getTime(session, csv_file)
		else:
			print("1 argument expected %d given" % len(args))
			sys.exit()

if __name__ == "__main__":
	main()
