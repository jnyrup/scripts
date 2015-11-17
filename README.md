# iCheckMovies get total runtime
Takes a csv file (e.g. exported from iCheckMovies) as input and calculates the total runtime in days, hours and minutes.
It mainly uses OMDb API as opposed to IMDb because:
* It has a clean API
* It is faster to handle a small json file than downloading and parse an entire IMDb page

According to my small test of 1176 titles OMDb has information on more than 99 % of the titles.
For the few cases where OMDb does not have the runtime information a lookup on IMDb is performed.

The unscientific test of 1176 entries, containing plenty of rare and old titles.
The table shows how many hits there were on OMDb, IMDb if OMDb failed, or neither of them.

| OMDb | Imdb | Neither |
| ---- | ---- | ------- |
| 1165 |     1|       10|

## How to use
`./icm_get_total_time path-to-csv-file`
