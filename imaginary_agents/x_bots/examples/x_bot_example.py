import tweepy

client = tweepy.Client(
    consumer_key="your twitter api key",
    consumer_secret="your twitter api key secret",
    access_token="Your twitter access token",
    access_token_secret="Your twitter access token secret"
)

# Example tweet text
tweet_text = "GMGM"

client.create_tweet(text=tweet_text)
