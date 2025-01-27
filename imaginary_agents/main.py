import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
import time

from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase

from agents.operate_dot_fun import (
    operate_dot_fun_agent, 
    OperateDotFunAgentInputSchema, 
    previous_post_provider
)

import openai
import instructor

load_dotenv()

# Initialize a Rich Console for pretty console outputs
console = Console()

console.print("[bold blue]Operate.fun AI Agent[/bold blue]")
console.print("This agent creates X posts for the operate.fun account.")

# Create the input schema
input_schema = OperateDotFunAgentInputSchema()

while True:
    try: # Keep it on a try as it will prob call twitter api
        # output = operate_dot_fun_agent.run(input_schema)
        output = operate_dot_fun_agent.get_response()

        # Update previous_post_provider
        previous_post_provider.content_items.append(output.tweet_content)

        # Create a Rich Console instance
        console = Console()

        # Print the answer using Rich's Markdown rendering
        console.print("\n[bold blue]Tweet:[/bold blue]")
        console.print(output.tweet_content)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
    time.sleep(10)
