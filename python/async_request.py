import asyncio
import nest_asyncio
nest_asyncio.apply()

from concurrent.futures import ThreadPoolExecutor
from requests import Session
from json import loads



async def get_data_asynchronous(func, data):

    with ThreadPoolExecutor(max_workers=8) as executor:
            # Set any session parameters here before calling `fetch`
        with Session() as session:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor,func,*(session, name, i)) for i,name in enumerate(data)]
            
            #print(await asyncio.gather(*tasks))
            #info = await asyncio.gather(*tasks)
            array = [response for response in await asyncio.gather(*tasks)]
    return array
    # return asyncio.gather(*tasks)

def make_request(func, data):
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(get_data_asynchronous(func, data))
    array = loop.run_until_complete(future)
    return array