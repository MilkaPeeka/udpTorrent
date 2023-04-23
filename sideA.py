import struct

import aioudp
import asyncio

"""
This is the client with the file.

Algorithm:

1. we will send a "bittorrent protocol" message in udp.
2. the client will search us in its iptable - if we exist, then the new connection protocol will be created with existing_connections+1
2. now we can send msgs - 
4 first bytes is length of message
1 byte is for the maximum amount of connections (that way we will know which torrent is related)
1 byte is for the message
4 bytes for piece
4 byte for block offset
rest is for the data itself...
"""

file = [bytes([0, 1, 2, 3, 4, 5]) * 21230]
my_addr = ("127.0.0.1", 1234)

TYPES = {
    "REQUEST": 1,
    "PIECE": 2,
    "NO PIECE": 3,
    "KEEP ALIVE": 4
}

def keep_alive(trans_id):
    return struct.pack('i b b', 6, trans_id, TYPES["KEEP ALIVE"])


def parse_request(payload):
    return struct.unpack('i b b i i i', payload)


def get_block_of_file(piece_index, block_offset, block_length):
    return file[piece_index][block_offset:block_length + block_offset]


def create_data_msg(data, trans_id, piece_index, block_offset, block_length):
    # 4 bytes - length
    # 1 bytes - trans id
    # 1 bytes - msg type
    # 4 bytes - piece
    # 4 bytes - block offset
    # 4 bytes - block length
    # rest - data
    return struct.pack('i b b i i i', 4 + 1 + 1 + 4 + 4 + 4 + len(data) + 1, trans_id, TYPES["PIECE"], piece_index, block_offset, block_length) + data


async def parse_init_msg(msg, addr):
    ip_table = []
    offset = len(ip_table)
    if addr[0] not in ip_table:
        offset += 1
        ip_table.append(addr[0])


    if msg == b'bittorrent':
        return (struct.pack('! b', offset), None)
    
    public_pem = msg[10:]
    return (struct.pack('! b', offset) + public_pem, public_pem)


async def listen():
    print("starting connection")
    conn_with_peer = await aioudp.open_local_endpoint(*my_addr)

    msg, addr = await conn_with_peer.receive()

    resp, public_key = parse_init_msg(msg, addr)
    conn_with_peer.send(resp, addr)
    

    sleep_cntr = 1
    while True:
        if sleep_cntr % 30 == 0:
            conn_with_peer.send(keep_alive(trans_id))
            sleep_cntr = 0

        msg, addr = await conn_with_peer.receive()
        msg_length, trans_id, msg_type, piece_index, block_offset, block_length = parse_request(msg)

        if msg_type == 1:
            data = get_block_of_file(piece_index, block_offset, block_length)
            block_len = len(data)
            print(f"data being sent: {data}")
            data = create_data_msg(data, trans_id, piece_index, block_offset, block_len)
            print(f"sent to peer data, piece index: {piece_index}, block offset: {block_offset}, block length: {block_len}")
            conn_with_peer.send(data, addr)

        await asyncio.sleep(0.001)
        sleep_cntr += 0.001

asyncio.run(listen())
