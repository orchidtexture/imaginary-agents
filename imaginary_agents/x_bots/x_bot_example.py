import os
import load_dotenv
import tweepy

# Load environment variables from the .env file
load_dotenv()

# Get the Twitter API credentials from the environment variables
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_KEY_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# Example tweet text
tweet_text = "GMGM"

client.create_tweet(text=tweet_text)
