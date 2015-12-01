#!/usr/bin/env python3
"""Script to accumulate the runtime for all movies from a csv file from iCheckMovies
	It tries to get runtime information from OMDb API and IMDb if it is not available
	on OMDb API.
	The first row is expected to be headers"""
import sys, os, csv, requests
from bs4 import BeautifulSoup
from operator import itemgetter
from collections import Counter
from math import floor

class Stats:
	skipped = 0
	runtimes = []
	histograms = {
		'Genre' : Counter(),
		'Runtime' : Counter(),
		'Country' : Counter(),
		'Year' : Counter(),
		'imdbRating' : Counter()
	}

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

		for title, hist in sorted(self.histograms.items()):
			print(title)
			for k1, v1 in sorted(hist.items(), key=itemgetter(0)):
				print("\t%s: %s" % ( k1, v1))

	def add(self, time):
		self.runtimes.append(time)

	def skip(self):
		self.skipped += 1

def get_from_imdb(session, imdb_url, not_seen, value_saver):
	genres = []

	response = session.get(imdb_url, stream=True)
	it = response.iter_lines()
	for line in it:
		if not not_seen:
			break
		if 'Runtime' in not_seen and str(line).endswith(' min\''):
			value_saver['Runtime'] = int(str(line).split()[1])
			del not_seen['Runtime']
		elif 'Genre' in not_seen and  '><span class="itemprop" itemprop="genre">' in str(line):
			genres += str(line)[43:].split('<')[0]
		elif 'Country' in not_seen and '<a href="/country/ee?ref_=tt_dt_dt"' in str(line):
			value_saver['Country'] = [str(next(it))[17:-5]]
			del not_seen['Country']
		elif 'imdbRating' in not_seen and '<div class="titlePageSprite star-box-giga-star">' in str(line):
			value_saver['imdbRating'] =  [str(line)[59:-8]]
			del not_seen['imdbRating']
	value_saver['Genre'] = genres
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

		hist_values = stats.histograms.keys()
		not_seen = dict()
		value_saver = dict()
		for hist_value in hist_values:
			if info[hist_value] != 'N/A':
				if hist_value == 'Runtime':
					value_saver[hist_value] = [int(info['Runtime'][:-4])]
				else:
					value_saver[hist_value] = info[hist_value].split(', ')
			else:
				not_seen[hist_value] = True
		if not_seen:
			get_from_imdb(session, imdb_url, not_seen, value_saver)

		if not_seen:
			print('"%s" (%s) has no %s' % (title, imdb_id, not_seen))

		if 'Runtime' in value_saver:
			stats.add(value_saver['Runtime'][0])
		else:
			stats.skip()

		for k, v in value_saver.items():
			for v1 in v:
				key = v1
				if k == 'Runtime':
					v1 -= v1 % 15
					key = "%s-%s" % (str(v1).rjust(3), str(v1+15).rjust(3))
				elif k == 'Year':
					v1 = int(v1)
					v1 -= v1 % 10
					key = "%d-%d" % (v1, v1+10)
				elif k == 'imdbRating':
					v1 = .5 * floor(float(v1)/.5)
					key = "%.1f-%.1f" % (v1, v1+.5)
				stats.histograms[k][key] += 1

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
