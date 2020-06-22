import csv
import praw
import time
import os
import logging
from string import punctuation


#contains client_id and client_secret used to connect
import config

TIME_PERIOD						= 60 * 60 * 4 * 1

SUBREDDIT						= 'wallstreetbets'
STOCK_SPECIFIC_METION_WEIGHT 	= 5
STOCK_POST_MENTION_WEIGHT 		= 3
STOCK_DEFAULT_WEIGHT			= 1

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('prawcore')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


#list of common english words to remove
common_word_filters=["ALOT", "JAN", "ONCE", "EDIT", "BRO", "SU", "LIFE", "CFO", "JOB", "BIT", "TWO", "BEST", "BIG", "EOD", "HOPE", "AM", "EVER", "PUMP", "NEXT", "HE", "REAL", "WORK", "NICE", "TOO", "MAN", "LOVE", "BY", "VERY", "ANY", "SEE", "NEW", "WELL", "TELL", "IT", "ONE", "POST", "ON", "TURN", "GOOD", "CAN", "HAS", "GO", "PLAY", "ELSE", "GAIN", "RUN", "INFO", "STAY", "CARE", "ALL", "AT", "PER", "DO", "ARE", "NOW", "BE", "OR", "SO", "OUT", "BEAT", "AGO", "AN", "PEAK", "LOW", "DD", "FOR", "FLAT"]
common_word_translations={"AVIS" : "CAR", "SPOTIFY" : "SPOT", "TESLA" : "TSLA", "Lockheed" : "LMU", "MICRON" : "MU", "SHOPIFY" : "SHOP", "DISNEY" : "DIS", "Boeing" : "BA", "NETFLIX" : "NFLX", "APPLE" : "AAPL", "INTEL" : "INTC", "PELOTON" : "PTON", "PELETON" : "PTON", "GOOGLE" : "GOOG", "STARBUCKS" : "SBUX"}
word_counts={}
stocks={}
specific_stocks={}

#Load base list of stock symbols from all csv files in cwd
#the first column must be the stock symbol
for filename in os.listdir(os.getcwd()):
    if filename.endswith(".csv"): 
    	print("Loading {}...".format(filename))
    	
    	with open(filename, mode='r') as infile:
    		reader = csv.reader(infile)
    		for rows in reader:
    			stocks[rows[0]] = 0

#analyze a blob of text, increment counts in stock dictionary
#add new entries for any words thats start with a $
def analyze_text(text, value=STOCK_DEFAULT_WEIGHT):
	for word in text.split():
		word=word.upper()
		word = word.rstrip(punctuation)
		
		if (len(word)<2):
			continue
			
		if ( (word.isalnum()) or ( (word[0] is "$") and (word[1:].isalpha()) )):
			if word in word_counts:
				word_counts[word] += value
			else:
				word_counts[word] = value


print("Crawling subreddit[{}] for all posts/comments within the last {} seconds".format(SUBREDDIT, TIME_PERIOD))
#Create praw connection	
reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent='Comment extraction by /u/rizir')

#iterate through latest 24 hours of submissions and all comments made on those submissions

timestamp	= int(time.time())

for submission in reddit.subreddit(SUBREDDIT).new(limit=1000):
	time_delta=timestamp - submission.created_utc

	if (time_delta > TIME_PERIOD):
		break

	print("Title:\t", submission.title)
	print("ID:\t", submission.id)
	print("Comments:\t", submission.num_comments)
	print("Age:\t", time_delta)

	analyze_text(submission.title, value=STOCK_POST_MENTION_WEIGHT)
	analyze_text(submission.selftext, value=STOCK_POST_MENTION_WEIGHT)

	#submission.comments.replace_more(limit=None, threshold=0)
	if submission.num_comments > 500:
		print("Getting more comments (", submission.num_comments, "), this may take a while...")
	submission.comments.replace_more(limit=None, threshold=0)
	
	for comment in submission.comments.list():
		print("\t", comment.id)
		analyze_text(comment.body)

	print()

#create dict of specific stock mentions of only $* stocks
for k, v in word_counts.items():
	if k[0] is "$":
		stock = k[1:]
		specific_stocks[stock] = v
		
#first iteration to add $ words to stocks dict and input specific mentions of $stock
for k, v in word_counts.items():
	if k[0] is "$":
		stock = k[1:]
		stocks[stock] = v * STOCK_SPECIFIC_METION_WEIGHT

#second iteration to add values to stocks, its added to count mentions of $ that occured without the $
#also do commmon translations
for k, v in word_counts.items():
	if (k in stocks) and (k not in common_word_filters):
		stocks[k]+=v

	if k in common_word_translations:
		stocks[common_word_translations[k]] += v

#remove stocks with 0 mentions
stock_with_mentions = dict((k, v) for k, v in stocks.items() if v >= 1)
#sort by value
sorted_stocks = {k: v for k, v in sorted(stock_with_mentions.items(), key=lambda item: item[1], reverse=True)}
print("STOCK MENTIONS")
print(sorted_stocks)

print()
print("STOCK SPECIFIC MENTIONS")
sorted_specific_stocks = {k: v for k, v in sorted(specific_stocks.items(), key=lambda item: item[1], reverse=True)}
print(sorted_specific_stocks)