import struct
import enc
import aioudp
import asyncio

peer_addr = ("127.0.0.1", 1234)
file = bytearray([0, 0, 0, 0, 0]) * 1
public_key, private_key = enc.create_key_pairs()

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


def build_piece_into_file(data, offset, block_length, public_key=None):
    # public key value is not used; it's just to understand if torrent is encrypted or not. 
    if public_key:
        data = enc.decrypt_using_private(data, private_key)
        block_length = len(data)

    for i in range(block_length):
        file[i + offset] = data[i]

    if offset + 1 >= len(file):
        print(file)
        print("finished")
        exit(1)


def generate_init_msg(public_pem=None):
    if not public_pem:
        return b'bittorrent'

    return b'bittorrent' + public_pem


def get_trans_id_from_resp(resp, public_pem=None):
    if public_pem:
        assert resp[1:] == public_pem
        return resp[0]

    return resp[0]


def parse_block_message(msg):
    # 4 bytes - length
    # 1 bytes - trans id
    # 1 bytes - msg type
    # 4 bytes - piece
    # 4 bytes - block offset
    # 4 bytes - block length
    # rest - data
    return struct.unpack('i b b i i i', msg)


async def main():
    BLOCK_SIZE = 0xfff
    block_offset = 0

    if public_key:
        BLOCK_SIZE = enc.MSG_SIZE_REQUEST_BYTES

    remote_conn = await aioudp.open_remote_endpoint(*peer_addr)
    remote_conn.send(generate_init_msg(public_key))
    print("sent init msg")

    trans_id = await remote_conn.receive()
    trans_id = get_trans_id_from_resp(trans_id)
    print("finished handshake")

    while True:
        req = create_piece_request(trans_id, 0, block_offset, BLOCK_SIZE)
        remote_conn.send(req)
        print("sent a piece request msg")
        msg = await remote_conn.receive()
        # msg should be of type:
        # piece, no piece

        length, trans_id, msg_type, piece_index, recv_offset, block_length = parse_block_message(msg[:20])
        print(
            f"recieved data from peer, piece index: {piece_index}, block offset: {recv_offset}, block length: {block_length}")

        if msg_type == TYPES["PIECE"]:
            build_piece_into_file(msg[20:length + 1], block_offset, block_length, public_key)
            block_offset += BLOCK_SIZE

        await asyncio.sleep(0.001)


asyncio.run(main())
