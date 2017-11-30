# Simple Python Scraper

## Parameters:

	starting_urls - [string] - List of starting URLs	
	next_url_filters - [string] - List of regex strings to filter the next URLs to retrieve. 
	parse_urls_callbacks - [function] - List of function callbacks to customize parsing of links in retrieved URL responses. Callback takes a single parameter response - fn(response). 
	max_depth - int - Maximum depth of links to retrieve 
	session - requests.Session() - Session to use while retrieving links 
	max_workers - int - Maxmimum number of concurrent requests
	
	

## Example:

	from scrape import scrape
	
	scrape(starting_urls=['http://www-us.apache.org/dist/'], 
		next_url_filters=['^http://www-us.apache.org/dist/.*/$'], 
		max_depth=2)


