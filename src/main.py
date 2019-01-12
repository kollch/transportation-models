# Needed for connection to frontend
import asyncio
import re
import logging
from hashlib import sha1
from base64 import b64encode

from vehicles import Vehicle, CAV, HV
from infrastructure import Infrastructure, Intersection, Road

class InvisibleHand():
    """Runs everything like the clock and spawning of vehicles;
    presumably connects to the GUI.
    """
    def __init__(self, connection):
        """Allow class to pass to GUI via Connection class"""
        self.gui = connection
        self.set_parameters()

    def set_parameters(self):
        """Set parameters pulled from GUI, aka initializing simulation
        Parameters: num_frames, vehicle positions, infrastructure setup
        """
        return

    async def build_frames(self):
        """Run simulation for certain number of frames;
        when ready to send a frame,
        call "await self.gui.send_frame(json)".
        """
        await self.gui.send_frame("Pseudo-frame data")
        return

    def cavs_in_range(self, location, length):
        """Gives list of CAVs within distance of length (in meters) of
        location
        """
        return

class Connection():
    """Handles a connection with the GUI"""
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.addr = writer.get_extra_info('peername')

    async def establish(self):
        """Make connection with GUI (using websockets)"""
        data = await self.reader.readuntil(b'\r\n\r\n')
        message = data.decode()
        regex = re.search('Sec-WebSocket-Key: (.+)\r\n', message, re.IGNORECASE)
        key = regex.group(1)
        temp = (key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()
        accept_key = b64encode(sha1(temp).digest()).decode()
        header = 'HTTP/1.1 101 Switching Protocols\r\n'
        header += 'Upgrade: websocket\r\n'
        header += 'Connection: Upgrade\r\n'
        header += 'Sec-WebSocket-Accept: ' + accept_key + '\r\n\r\n'
        encoded_header = header.encode()
        self.writer.write(encoded_header)
        await self.writer.drain()
        print("Connection established with", self.addr[1], "from", self.addr[0])

    async def get_parameters(self):
        """Get parameters from GUI and store them"""
        # Diagram given by the document detailing Websockets, RFC6455:
        #  0                   1                   2                   3
        #  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        # +-+-+-+-+-------+-+-------------+-------------------------------+
        # |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
        # |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
        # |N|V|V|V|       |S|             |   (if payload len==126/127)   |
        # | |1|2|3|       |K|             |                               |
        # +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
        # |     Extended payload length continued, if payload len == 127  |
        # + - - - - - - - - - - - - - - - +-------------------------------+
        # |                               |Masking-key, if MASK set to 1  |
        # +-------------------------------+-------------------------------+
        # | Masking-key (continued)       |          Payload Data         |
        # +-------------------------------- - - - - - - - - - - - - - - - +
        # :                     Payload Data continued ...                :
        # + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
        # |                     Payload Data continued ...                |
        # +---------------------------------------------------------------+
        data = await self.reader.readexactly(2)
        # Generate a list of ints representing half-bytes
        intlist = [int(x, 16) for x in data.hex()]
        #print("Data:", ' '.join([hex(x) for x in data]))
        if intlist[0] == 8:
            fin = True
        elif intlist[0] == 0:
            fin = False
        else:
            print("Error: RSV1 or RSV2 or RSV3 not set to 0.")
            raise ValueError
        if intlist[1] != 0 and intlist[1] != 1 and intlist[1] != 8:
            print("Error: don't know the opcode '" + str(intlist[1]) + "'.")
            raise ValueError
        elif intlist[1] == 8:
            print("Client asking to close connection")
            return None
        if intlist[2] >= 8:
            masked = True
            intlist[2] -= 8
        else:
            masked = False
        payload_length = 16 * intlist[2] + intlist[3]
        if payload_length == 126:
            data = await self.reader.readexactly(2)
            payload_length = int.from_bytes(data, byteorder='big')
        elif payload_length == 127:
            data = await self.reader.readexactly(8)
            payload_length = int.from_bytes(data, byteorder='big')
        if masked:
            mask = await self.reader.readexactly(4)
        data = await self.reader.readexactly(payload_length)
        if masked:
            # Octet i of the transformed data is the XOR of
            # octet i of the original data with octet at index
            # i modulo 4 of the masking key
            unmasked_data = [data[i] ^ mask[i % 4] for i in range(len(data))]
            payload = bytearray(unmasked_data).decode()
        else:
            payload = data.decode()

        # TODO: store data in connection (from variable "payload")
        print("Data from frontend:", payload)

    async def send_frame(self, data):
        """Send frame from json data to GUI"""
        frame = [129]
        if 125 < len(data) < 65536:
            frame.append(126)
            frame.extend(len(data).to_bytes(2, byteorder='big'))
        elif len(data) >= 65536:
            frame.append(127)
            frame.extend(len(data).to_bytes(8, byteorder='big'))
        else:
            frame.append(len(data))
        self.writer.write(bytearray(frame) + data.encode())
        await self.writer.drain()

    def close(self):
        """Close connection with GUI"""
        print("Closing the client socket")
        self.writer.close()

async def main(reader, writer):
    """Start the program with a connected frontend"""
    connect = Connection(reader, writer)
    await connect.establish()
    await connect.get_parameters()
    run = InvisibleHand(connect)
    await run.build_frames()
    connect.close()

loop = asyncio.get_event_loop()
coro = asyncio.start_server(main, '127.0.0.1', 8888, loop=loop)
server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
socket_name = server.sockets[0].getsockname()
print("Serving on port", socket_name[1], "at", socket_name[0])
try:
    loop.run_forever()
except KeyboardInterrupt:
    print("Closing server")

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
