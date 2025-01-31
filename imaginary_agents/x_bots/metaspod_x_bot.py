import os
import asyncio
from dotenv import load_dotenv
import tweepy

from imaginary_agents.tools.pump_dot_fun_trends_tool import (
    PumpDotFunTrendsTool
)

from imaginary_agents.agents.metaspod_agent import (
    metas_pod_agent,
    MetasPodAgentInputSchema,
    previous_post_provider,
    trending_memes_provider
)

# Load environment variables from the .env file
load_dotenv()

# Get the Twitter API credentials from the environment variables
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

if not all(
    [
        TWITTER_API_KEY,
        TWITTER_API_KEY_SECRET,
        TWITTER_ACCESS_TOKEN,
        TWITTER_ACCESS_TOKEN_SECRET
    ]
):
    raise ValueError("Twitter API credentials are not set in the .env file")

# Initialize the Tweepy client
client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_KEY_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

trending_memecoin_tool = PumpDotFunTrendsTool()


async def create_post_with_agent():
    """Generate content using agents."""
    try:
        # Retrieve trending memecoins
        trending_memes = trending_memecoin_tool.run()
        trending_memes_string = ", ".join(trending_memes.trending)
        print(f"Trending memes {trending_memes_string}")
        # Generate post content
        metas_pod_agent_output = metas_pod_agent.run(
            MetasPodAgentInputSchema(trending_memes=trending_memes_string)
        )

        print(f"{'-'*80}")
        print(f"Trending memes {trending_memes.trending}")
        print("Post content: ")
        print(metas_pod_agent_output.tweet_content)
        print(f"{'-'*80}")

        # Update providers
        previous_post_provider.content_items.append(
            metas_pod_agent_output.tweet_content
        )
        trending_memes_provider.memes = trending_memes.trending

        return metas_pod_agent_output.tweet_content
    except Exception as e:
        print(f"Error creating post: {e}")
        return None


async def tweet(text: str):
    """Post a tweet using tweepy."""
    try:
        client.create_tweet(text=text)
        print("Tweet posted successfully!")
    except Exception as e:
        print(f"Error posting tweet: {e}")


async def main():
    while True:
        # Create a post with the agent
        post_content = await create_post_with_agent()

        # Post the content to Twitter
        if post_content:
            await tweet(post_content)

        # Wait for 10 minutes before posting again
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main())
