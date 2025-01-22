# todo desc

import httpx


async def handle_request(
    url: str, params: dict[str, any], headers: dict[str, any]
) -> httpx.request:
    # todo desc
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)

    # todo add debug mode here response.text
    # todo add path not just the name
    with open("test.gejson", "w", encoding="utf-8") as file:
        file.write(response.text)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response
