from dotenv import load_dotenv
from rich.console import Console
import time

from agents.operate_dot_fun import (
    operate_dot_fun_agent,
    OperateDotFunAgentInputSchema,
    previous_post_provider,
    trending_memes_provider
)
from agents.memecoin_lore_agent import (
    memecoin_lore_agent,
    MemecoinLoreAgentInputSchema
)

from tools.pump_dot_fun_trends_tool import PumpDotFunTrendsTool
from tools.memecoin_descriptions_tool import (
    MemecoinDescriptionsTool,
    MemecoinDescriptionsToolInputSchema
)
load_dotenv()

# Initialize a Rich Console for pretty console outputs
console = Console()

trending_memecoin_tool = PumpDotFunTrendsTool()
memecoin_descriptions_tool = MemecoinDescriptionsTool()

while True:
    try:  # Keep it on a try as it will prob call twitter api

        # Retrieve trending memecoins
        trending_memes = trending_memecoin_tool.run()

        # Generate memecoin lore
        memecoin_descriptions_tool_output = memecoin_descriptions_tool.run(
            MemecoinDescriptionsToolInputSchema(tag=trending_memes.trending[0])
        )

        # pass to memecoin_lore_agent
        memecoin_lore_agent_output = memecoin_lore_agent.run(
            MemecoinLoreAgentInputSchema(
                descriptions=memecoin_descriptions_tool_output.descriptions
            )
        )
        print(f"{'-'*80}")
        print(f"Lore for {trending_memes.trending[0]}")
        print(memecoin_lore_agent_output.lore)
        print(f"{'-'*80}")

        operate_dot_fun_output = operate_dot_fun_agent.run(
            OperateDotFunAgentInputSchema(
                meme_lore=memecoin_lore_agent_output.lore
            )
            )

        # Update previous_post_provider
        previous_post_provider.content_items.append(
            operate_dot_fun_output.tweet_content
        )

        # Update trending_memes_provider
        trending_memes_provider.memes = trending_memes.trending
        print(trending_memes_provider.get_info())

        # Create a Rich Console instance
        console = Console()

        # Print the answer using Rich's Markdown rendering
        console.print("\n[bold blue]Tweet:[/bold blue]")
        console.print(operate_dot_fun_output.tweet_content)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    time.sleep(10)
