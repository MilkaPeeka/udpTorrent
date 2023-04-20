import struct

import aioudp
import asyncio

peer_addr = ("127.0.0.1", 1234)
file = bytearray([0]) * 6 * 21230
print(f"file length: {len(file)}")
TYPES = {
    "REQUEST": 1,
    "PIECE": 2,
    "NO PIECE": 3,
    "KEEP ALIVE": 4
}


def create_piece_request(trans_id, piece_index, block_offset, length):
    # 4 bytes - length
    # 1 bytes - trans id
    # 1 bytes - msg type
    # 4 bytes - piece
    # 4 bytes - block offset
    # 4 bytes - block length

    return struct.pack('i b b i i i', 4 + 1 + 1 + 4 + 4 + 4, trans_id, TYPES['REQUEST'], piece_index, block_offset,
                       length)


def build_piece_into_file(data, offset, block_length):
    for i in range(block_length):
        file[i + offset] = data[i]

    if offset + 1 >= len(file):
        print(file)
        print("finished")
        exit(1)
async def init_conn():
    BLOCK_SIZE = 0xfff
    block_offset = 0

    remote_conn = await aioudp.open_remote_endpoint(*peer_addr)
    remote_conn.send(b'bittorrent')
    trans_id = await remote_conn.receive()
    trans_id = int.from_bytes(trans_id)

    while True:
        req = create_piece_request(trans_id, 0, block_offset, BLOCK_SIZE)
        remote_conn.send(req)
        msg = await remote_conn.receive()

        # msg should be of type:
        # piece, no piece

        # 4 bytes - length
        # 1 bytes - trans id
        # 1 bytes - msg type
        # 4 bytes - piece
        # 4 bytes - block offset
        # 4 bytes - block length
        # rest - data

        if msg[5] == TYPES["KEEP ALIVE"]:
            continue

        length, trans_id, msg_type, piece_index, recv_offset, block_length = struct.unpack('i b b i i i', msg[:20])
        print(f"recieved data from peer, piece index: {piece_index}, block offset: {recv_offset}, block length: {block_length}")

        if msg_type == TYPES["PIECE"]:
            build_piece_into_file(msg[20:length + 1], block_offset, block_length)
            block_offset += BLOCK_SIZE

        await asyncio.sleep(0.001)


asyncio.run(init_conn())
