# Imaginary Agents

A toolkit for creating and managing agentic systems, powered by [atomic-agents](https://github.com/BrainBlend-AI/atomic-agents)

## Project Structure

Imaginary Agents uses a monorepo structure with the following main components:

1. `agents/`: Contains each agent logic separately
2. `tg_bots/`: Contains each telegram bot logic separately
3. `tools/`: Contains each tool logic separately
4. `x_bots/`: Contains each X bot logic separately
5. `context_providers.py`: Contains all the context provider logic (maybe separate in different context provider files)

## Examples

- `x_bots/examples/x_bot_example.py` [WIP] A minimal X bot authenticating with OAuth1 and posting a tweet using the tweepy library.
- `tg_bots/examples/tg_bot_example.py` [WIP] A minimal Telegram bot exposing example_agent using the Telebot library.
