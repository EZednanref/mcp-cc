# test_server.py
# juste un petit test direct des fonctions du server.py
import asyncio
from server import start_tracking, stop_tracking, get_status

async def main():
    print(await get_status())
    print(await start_tracking(measure_power_secs=1))
    print(await get_status())
    print(await stop_tracking())
    print(await get_status())

asyncio.run(main())
