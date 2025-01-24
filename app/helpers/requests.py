# todo desc

import aiohttp


async def handle_request(
    url: str, params: dict[str, any] = {}, headers: dict[str, any] = {}
) -> aiohttp.ClientResponse:
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, params=params) as response:
            # tobeunderstoodlater
            response_text: str = await response.text()
            # print(response_text) #debug here idk

            # with open("test.gejson", "w", encoding="utf-8") as file:
            #    file.write(response_text)

            # todo change to trycatch
            if response.status != 200:
                print(":((")
            return response
