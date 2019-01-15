# Needed for connection to frontend
import asyncio
import ssl
import websockets
import json

from vehicles import Vehicle, CAV, HV
from infrastructure import Infrastructure, Intersection, Road

secure = False

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
        for i in range(6):
            frame = get_frame_data("testframes.json", i)
            await self.gui.send_frame(frame)
        # Specify end of frames
        await self.gui.send_frame(None)
        return

    def cavs_in_range(self, location, length):
        """Gives list of CAVs within distance of length (in meters) of
        location
        """
        return

class Connection():
    """Handles a connection with the GUI"""
    def __init__(self, websocket, path):
        self.websocket = websocket
        #self.addr = writer.get_extra_info('peername')

    async def get_parameters(self):
        payload_str = await self.websocket.recv()
        # Now convert the payload string to a json object
        payload = json.loads(payload_str)

        # TODO: store data in connection (from variable "payload")
        print("Data from frontend:", payload)

    async def send_frame(self, json_data):
        """Send frame from json data to GUI"""
        data = json.dumps(json_data)
        await self.websocket.send(data)

async def main(websocket, path):
    """Start the program with a connected frontend"""
    connect = Connection(websocket, path)
    await connect.get_parameters()
    run = InvisibleHand(connect)
    await run.build_frames()

def get_frame_data(file_name, frame):
    """Temporary function to read json from a file;
    should be deleted soon
    """
    with open(file_name) as json_file:
        data = json.load(json_file)
        return data[frame]

# Start server with or without ssl
if secure:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('cert/localhost.crt', 'cert/localhost.key')
else:
    ssl_context = None
start_server = websockets.serve(main, 'localhost', 8888, ssl=ssl_context)

loop = asyncio.get_event_loop()
server = loop.run_until_complete(start_server)

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
