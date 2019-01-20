"""This is the primary component of the backend."""
# Needed for connection to frontend
import asyncio
import ssl
import json
import websockets

from vehicles import Vehicle, CAV, HV
from infrastructure import Infrastructure, Intersection, Road

SECURE = False


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
        x1 = location[0]
        y1 = location[1]
        in_range_cavs = []

        for single_vehicle in self.cavs:
            x2 = single_vehicle.location[0]
            y2 = single_vehicle.location[1]
            if x2 - x1 != 0 or y2 - y1 != 0:
                dist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if dist <= 3000:
                    in_range_cavs.append(single_vehicle)
        return in_range_cavs


class Connection():
    """Handles a connection with the GUI"""
    def __init__(self, websocket, path):
        self.websocket = websocket
        self.addr = websocket.remote_address

    async def get_parameters(self):
        """Get infrastructure parameters from the frontend"""
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
if SECURE:
    SSL_CONTEXT = ssl.SSLContext()
    SSL_CONTEXT.load_cert_chain('cert/localhost.crt', 'cert/localhost.key')
else:
    SSL_CONTEXT = None
START_SERVER = websockets.serve(main, 'localhost', 8888, ssl=SSL_CONTEXT)

LOOP = asyncio.get_event_loop()
SERVER = LOOP.run_until_complete(START_SERVER)

# Serve requests until Ctrl+C is pressed
SOCKET_NAME = SERVER.sockets[0].getsockname()
print("Serving on port", SOCKET_NAME[1], "at", SOCKET_NAME[0])
try:
    LOOP.run_forever()
except KeyboardInterrupt:
    print("Closing server")

# Close the server
SERVER.close()
LOOP.run_until_complete(SERVER.wait_closed())
LOOP.close()
