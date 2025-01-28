from datetime import datetime
from typing import List
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptContextProviderBase
)


class TrendingMemesProvider(SystemPromptContextProviderBase):
    def __init__(self, title):
        super().__init__(title=title)
        self.memes: List[str] = []

    def get_info(self) -> str:
        return (
            f"The current trending memes are: {self.memes}."
            if self.memes else "No trending memes found."
        )


class PreviousPostProvider(SystemPromptContextProviderBase):
    # should we retrieve previous posts dinamically or from a db of our own??
    def __init__(self, title):
        super().__init__(title)
        self.content_items: List[str] = []

    def get_info(self) -> str:
        enumerated_posts = "\n".join(
            [
                f"({i}, '{post}')\n{'-'*80}"
                for i, post in enumerate(self.content_items, 1)
            ]
        )
        return f"Previous posts:\n{enumerated_posts}"


class CurrentDateContextProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str, date_format: str = "%A %B %d, %Y"):
        super().__init__(title=title)
        self.date_format = date_format

    def get_info(self) -> str:
        return (
            f"The current date in the format {self.date_format} is {
                datetime.now().strftime(self.date_format)
            }."
        )
