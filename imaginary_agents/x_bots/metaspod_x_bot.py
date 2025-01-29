import os
import asyncio
from dotenv import load_dotenv
from twikit import Client

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
USERNAME = os.getenv("TWITTER_USERNAME")
EMAIL = os.getenv("TWITTER_EMAIL")
PASSWORD = os.getenv("TWITTER_PASSWORD")

if not all([USERNAME, EMAIL, PASSWORD]):
    raise ValueError("Twitter login credentials are not set in the .env file")

# Initialize the Twikit client
client = Client('en-US')

trending_memecoin_tool = PumpDotFunTrendsTool()


async def login():
    """Login to Twitter using twikit."""
    try:
        await client.login(
            auth_info_1=USERNAME,
            auth_info_2=EMAIL,
            password=PASSWORD
        )
        print("Logged in successfully!")
    except Exception as e:
        print(f"Error logging in: {e}")


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
    """Post a tweet using twikit."""
    try:
        await client.create_tweet(text)
        print("Tweet posted successfully!")
    except Exception as e:
        print(f"Error posting tweet: {e}")


async def main():
    # Perform login once
    await login()

    while True:
        # Create a post with the agent
        post_content = await create_post_with_agent()

        # Post the content to Twitter
        if post_content:
            await tweet(post_content)

        # Wait for an hour before posting again
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
