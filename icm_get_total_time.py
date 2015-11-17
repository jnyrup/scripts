#!/usr/bin/env python3
"""Script to accumulate the runtime for all movies from a csv file from iCheckMovies
	It tries to get runtime information from OMDb API and IMDb if it is not available
	on OMDb API.
	The first row is expected to be headers"""
import sys, os, csv, requests

def main():
	args = sys.argv
	if len(args) != 2:
		print("1 argument expected %d given" % len(args))
		sys.exit()
	input_file = args[1]
	if not os.path.isfile(input_file):
		print("%s is not a file (did you mispell something?)" % input_file)
		sys.exit()

	with open(input_file, encoding='latin-1') as csvfile, requests.Session() as session:
		csv_reader = csv.reader(csvfile)
		total_time = 0
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
			if info['Response'] == 'True':
				try:
					total_time += int(info['Runtime'][:-4])
				except ValueError:
					response = session.get(imdb_url, stream=True)
					found = False
					for line in response.iter_lines():
						if str(line).endswith(' min\''):
							found = True
							total_time += int(str(line).split()[1])
							break
					if not found:
						print('"%s" (%s) has no info on omdbapi/IMDb' % (info['Title'], imdb_id))
			else: print(info)
		hours, minutes = divmod(total_time, 60)
		days, hours = divmod(hours, 24)
		print("%d days, %d hours and %d minutes" % (days, hours, minutes))

if __name__ == "__main__":
	main()
