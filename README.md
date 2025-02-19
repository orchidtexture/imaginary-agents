# Imaginary Agents

A toolkit for creating and managing agentic systems, powered by [atomic-agents](https://github.com/BrainBlend-AI/atomic-agents)

## Project Structure

Imaginary Agents uses a monorepo structure with the following main components:

### imaginary_agents

1. `imaginary_agents/agents/`: Contains each agent logic separately
2. `imaginary_agents/tg_bots/`: Contains each telegram bot logic separately
3. `imaginary_agents/tools/`: Contains each tool logic separately
4. `imaginary_agents/x_bots/`: Contains each X bot logic separately
5. `imaginary_agents/context_providers.py`: Contains all the context provider logic (maybe separate in different context provider files)

## Examples

- `x_bots/examples/x_bot_example.py` [WIP] A minimal X bot authenticating with OAuth1 and posting a tweet using the tweepy library.
- `tg_bots/examples/tg_bot_example.py` [WIP] A minimal Telegram bot exposing example_agent using the Telebot library.

### API

This layer holds the REST API logic that utilizes the agents from `imaginary_agents`

1. `api/routes/agents`: The API routes for calling the different agent types (simple, tg, twitter, etc) Currently only `simple` agent is available.
2. `api/server`: Fast API server setup.

To run the server:

`poetry run uvicorn api.server:app --reload`

Run Simple Agent request example where the agent analyzes onchain data for this address `EJpLyTeE8XHG9CeREeHd6pr6hNhaRnTRJx4Z5DPhEJJ6`:

```shell
# POST api/v1/agent/run
curl -X POST http://localhost:8000/api/v1/agent/run \
-H "Content-Type: application/json" \
-d '{
    "type": "simple",
    "input_schema_fields": {
        "onchain_data": {
            "type": "str",
            "description": "The onchain data of the address."
        }
    },
    "output_schema_fields": {
        "insights": {
            "type": "str",
            "description": "The generated insights from the provided onchain data."
        }
    },
    "background": [
        "You are a highly skilled Solana Onchain analysis assistant.",
        "You can analyze onchain data and provide insights about an address on the Solana blockchain."
    ],
    "steps": [
        "Thouroughly analyze the provided onchain data of an individual address",
        "Provide insights about the address such as the number of transactions, the total amount of SOL transacted, the number of unique tokens held, etc.",
        "Provide insights about the tokens held by the address, the number of tokens, the total value of the tokens, etc."
    ],
    "output_instructions": [
        "Be extremely careful with the data analysis and ensure the accuracy of the insights provided.",
        "Provide the insights in a clear and concise manner to the user."
    ],
    "input_data": {
        "onchain_data": "{\"nativeBalance\":{\"lamports\":\"0\",\"solana\":\"0\"},\"tokens\":[{\"associatedTokenAddress\":\"4V2QhEt59AGxGN8VwbmGUvPcjPpxPC2BGZoYWWZQppRi\",\"mint\":\"Doggoyb1uHFJGFdHhJf8FKEBUMv58qo98CisWgeD7Ftk\",\"amountRaw\":\"25700670593\",\"amount\":\"257006.70593\",\"decimals\":5,\"name\":\"DOGGO\",\"symbol\":\"DOGGO\",\"logo\":\"https://d23exngyjlavgo.cloudfront.net/solana_Doggoyb1uHFJGFdHhJf8FKEBUMv58qo98CisWgeD7Ftk\"},{\"associatedTokenAddress\":\"J3sQDCWQQuZRCSgW7BWZ8s8Zoz16mprPxoCuryo6YXUX\",\"mint\":\"VVWAy5U2KFd1p8AdchjUxqaJbZPBeP5vUQRZtAy8hyc\",\"amountRaw\":\"7777000000000\",\"amount\":\"7777\",\"decimals\":9,\"name\":\"Flip.gg | #1 Lootbox Game\",\"symbol\":\"FLIPGG\",\"logo\":\"https://d23exngyjlavgo.cloudfront.net/solana_VVWAy5U2KFd1p8AdchjUxqaJbZPBeP5vUQRZtAy8hyc\"},{\"associatedTokenAddress\":\"ANG2Qh3Zn5kh1ifj4cNXbqbZT8KP7waNm3r2iVeaFwMF\",\"mint\":\"HsQ9h5Hq3h4W2ez7EHmVp4XToJYbwFFSTBKdfutHxpsk\",\"amountRaw\":\"1\",\"amount\":\"1\",\"decimals\":0,\"name\":\"Cets Eyemask\",\"symbol\":\"goons\",\"logo\":null},{\"associatedTokenAddress\":\"GqboUZFpTZ6UeRhujy39q9B5ZVa7CXnqpWzTGXH7GuVg\",\"mint\":\"7SZUnH7H9KptyJkUhJ5L4Kee5fFAbqVgCHvt7B6wg4Xc\",\"amountRaw\":\"24061600000\",\"amount\":\"240616\",\"decimals\":5,\"name\":\"TheSolanDAO\",\"symbol\":\"SDO\",\"logo\":\"https://d23exngyjlavgo.cloudfront.net/solana_7SZUnH7H9KptyJkUhJ5L4Kee5fFAbqVgCHvt7B6wg4Xc\"},{\"associatedTokenAddress\":\"7uuY4rNkvaJ8ZFbp4K32XZSw4dMybYb2wE3VVXjh8WXC\",\"mint\":\"5BLVGCJLYDL4UEC7dye3c7BeAtam7s2gEnHxW2JpEgwC\",\"amountRaw\":\"1\",\"amount\":\"1\",\"decimals\":0,\"name\":\"Diamond\",\"symbol\":\"goons\",\"logo\":null},{\"associatedTokenAddress\":\"FaygwmWV2RGQVABXdvaPoa4Kar8EcjpaQcB4czcy4pUJ\",\"mint\":\"EL4YBAq2vnh2oQe454x64f4WJGxrywtUtxhJpv4cx2ks\",\"amountRaw\":\"2\",\"amount\":\"2\",\"decimals\":0,\"name\":\"Cets Ears\",\"symbol\":\"goons\",\"logo\":null},{\"associatedTokenAddress\":\"FcbfLtfg5ZL9VvmCBB2msyFsgDeGSuSS6UZFsi4G3Rhr\",\"mint\":\"SHDWyBxihqiCj6YekG2GUr7wqKLeLAMK1gHZck9pL6y\",\"amountRaw\":\"5155\",\"amount\":\"0.000005155\",\"decimals\":9,\"name\":\"Shadow Token\",\"symbol\":\"SHDW\",\"logo\":\"https://d23exngyjlavgo.cloudfront.net/solana_SHDWyBxihqiCj6YekG2GUr7wqKLeLAMK1gHZck9pL6y\"},{\"associatedTokenAddress\":\"HQphaovZMmDXhDoH6LtMCGijVXB3JXuXvBPRPP1pAJSd\",\"mint\":\"5yvYnJZC6oCQXJ5w5AQxw2uC4VEdsjwk8rvwdqZ9uwAg\",\"amountRaw\":\"1\",\"amount\":\"1\",\"decimals\":0,\"name\":\"Stay Diamond\",\"symbol\":\"goons\",\"logo\":null}],\"nfts\":[{\"associatedTokenAddress\":\"A8HqSgauFDqwjwPPtHCUpDoxpReGQztMZfVxVyyUkCWB\",\"mint\":\"5K74vmkAPbcQv7p3iZXFYdYhWpZB7kmZ89kEpQL3GdtZ\",\"name\":\"Arakne #1006\",\"symbol\":\"Chimera\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"Ag66H71oWijFj2VWousokmuJ1khLyt9haqbZ1cK8qfaT\",\"mint\":\"3QoQDmfAzRmPn85Mdr3YefzqWbhduhnwgQsPfgsJSBmW\",\"name\":\"Nug 325\",\"symbol\":\"METAWANA\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"Ez3KqGF5CoudwicRPMi9ecKehbk4hvMMxWG1ujcrhpt7\",\"mint\":\"5JCbscpbomhDi6pyBP2Fd9Xic9cddPb83SYKwbJ6zRD3\",\"name\":\"burtunt\",\"symbol\":\"POWR\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"DttJbcBy9qfdRBzjXPkBixRpXLSDxvPw4ebsUnY5k9s8\",\"mint\":\"F4Ro2FyGRzSQGefzCr7yRPjLrshv2qt4eGzRACoPjLxa\",\"name\":\"Cerberus #1067\",\"symbol\":\"CREATURE\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"21tSs3xUXzmGAgUaeJaN2AaZvaAqq92N1XbhAfem7z5R\",\"mint\":\"HqpsEeh6C3AJoDGrPJHQUUhaRSQFhoJHx1Fmf9SQZmZX\",\"name\":\"Rауdium аlрhа рrоgrаm\",\"symbol\":\"RAP\",\"decimals\":0,\"amount\":\"16\",\"amountRaw\":\"16\"},{\"associatedTokenAddress\":\"7ir8Bbc6AsCg9D3FQXe6nFTS4Zcu6FDSmteyZMHbGdRe\",\"mint\":\"7t9N9oA234YQTTqpSFCBW9dm8FFfY4cqVkSADXQPJioc\",\"name\":\"tarod\",\"symbol\":\"POWR\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"GSjJRpV71pBBcmXMpAkfma2sM5nEghTQVtkjTsdZA5po\",\"mint\":\"2PTJ4owuFMtKcNSZUvXsUBzqqFcao3x8zi3rkrhjn4Pb\",\"name\":\"Santa #11\",\"symbol\":\"SANTA\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"9bd54da8STwbhELTi7HqQdj3tnaxmfmSq695MzNi94yi\",\"mint\":\"BkaFvbSf8s7ZLoE3QoYa328No1FEz3D7Yzy38bvtMhdn\",\"name\":\"Evopill #6494\",\"symbol\":\"GOONS\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"Gshsqnk1qWDy1PcryceyjQQnSvUzqFnmiE9LLwvFPZdx\",\"mint\":\"5E56nvwdbFSyT52Wp4Kw3FBHpxdh5szVpvS8ASUX7nn8\",\"name\":\"Centaur #105\",\"symbol\":\"CREATURE\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"},{\"associatedTokenAddress\":\"2pzv1eXrLY6rLYNe3pGr2mu16zHbny31oYYrFUC8368G\",\"mint\":\"88xKwCgkhNZkSbEZYH95VkZYkRHQJqq9A2J6aHq6PTB5\",\"name\":\"Nug 1295\",\"symbol\":\"METAWANA\",\"decimals\":0,\"amount\":\"1\",\"amountRaw\":\"1\"}]}"
    }
}'
```
Example response:

```json
{
    "insights": "The address has a total of 0 SOL. It holds 8 different tokens and 10 different NFTs. The tokens held by the address are DOGGO (257006.70593), FLIPGG (7777), Cets Eyemask (1), TheSolanDAO (240616), Diamond (1), Cets Ears (2), Shadow Token (0.000005155), and Stay Diamond (1). The NFTs held by the address are Arakne #1006 (1), Nug 325 (1), burtunt (1), Cerberus #1067 (1), Rаudium аlрhа рrоgrаm (16), tarod (1), Santa #11 (1), Evopill #6494 (1), Centaur #105 (1), and Nug 1295 (1)."
}
```

> Note: In this example , the value passed to onchain_data comes from this [request](https://docs.moralis.com/web3-data-api/solana/reference/get-sol-portfolio?network=mainnet&address=EJpLyTeE8XHG9CeREeHd6pr6hNhaRnTRJx4Z5DPhEJJ6) to Moralis:

```shell
curl --request GET \
     --url 'https://solana-gateway.moralis.io/account/mainnet/EJpLyTeE8XHG9CeREeHd6pr6hNhaRnTRJx4Z5DPhEJJ6/portfolio' \
     --header 'accept: application/json' \
     --header 'X-API-Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjFmMGExMWM5LWVlNjEtNGRmMC1hNmVhLTQxYWE4MjkzNDI5YiIsIm9yZ0lkIjoiNDMyMzMzIiwidXNlcklkIjoiNDQ0NzE1IiwidHlwZUlkIjoiOGNmMTgzZTItYjI5NC00YzM4LTljY2EtMmU1ZjlmMjJmOWI2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3Mzk5MDgzMDksImV4cCI6NDg5NTY2ODMwOX0.ZZfYYJtzrrBYWcZ2Nyum7sKng4tuifPCAntmpJgYW10' 
```
