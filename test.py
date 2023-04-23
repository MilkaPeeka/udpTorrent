import aioudp
import asyncio


async def main():
    remote_conn = await aioudp.open_remote_endpoint("127.0.0.1", 1234)
    remote_conn.send(b'bittorrent')
    trans_id = await remote_conn.receive()
    print(trans_id)


asyncio.run(main())