from beanie import PydanticObjectId
from typing import List, Union

from api.models import LLMConfig, Agent

llm_config_collection = LLMConfig

############################################
# LLM Configurations
############################################


async def retrieve_llm_configs() -> List[LLMConfig]:
    llm_configs = await llm_config_collection.all().to_list()
    return llm_configs


async def add_llm_config(new_llm_config: LLMConfig) -> LLMConfig:
    llm_config = await new_llm_config.create()
    return llm_config


async def retrieve_llm_config(id: PydanticObjectId) -> LLMConfig:
    llm_config = await llm_config_collection.get(id)
    if llm_config:
        return llm_config


async def retrieve_llm_config_by_model(model: str) -> LLMConfig:
    llm_config = await llm_config_collection.find_one(LLMConfig.model == model)
    if llm_config:
        return llm_config


async def delete_llm_config(id: PydanticObjectId) -> bool:
    llm_config = await llm_config_collection.get(id)
    if llm_config:
        await llm_config.delete()
        return True


async def update_llm_config_data(
    id: PydanticObjectId,
    data: dict
) -> Union[bool, LLMConfig]:
    des_body = {k: v for k, v in data.items() if v is not None}
    update_query = {"$set": {field: value for field, value in des_body.items()}}
    llm_config = await llm_config_collection.get(id)
    if llm_config:
        await llm_config.update(update_query)
        return llm_config
    return False

############################################
# Agents
############################################


async def add_agent(new_agent: Agent) -> Agent:
    agent = await new_agent.create()
    return agent
