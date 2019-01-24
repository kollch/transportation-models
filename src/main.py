"""This is the primary component of the backend."""
import math
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
        self.infrastructure = None
        self.set_parameters()

    def set_parameters(self):
        """Set parameters pulled from GUI, aka initializing simulation
        Parameters: num_frames, vehicle positions, infrastructure setup
        """
        # Create intersections
        intersections = [
            Intersection(item['id'],
                         item['connects_roads'],
                         (item['loc']['x'], item['loc']['y']))
            for item in self.gui.infrastructure['intersections']
        ]
        # Create roads
        roads = [
            Road(item['id'],
                 item['two_way'],
                 item['lanes'],
                 (item['ends'][0], item['ends'][1]))
            for item in self.gui.infrastructure['roads']
        ]
        # Convert road endpoints to tuples if they're coordinates
        for road in roads:
            new_ends = [road.ends[0], road.ends[1]]
            for i in range(2):
                try:
                    new_ends[i] = (new_ends[i]['x'], new_ends[i]['y'])
                except TypeError:
                    pass
            road.ends = (new_ends[0], new_ends[1])
        # Create infrastructure
        self.infrastructure = Infrastructure(intersections, roads)

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
        x_1 = location[0]
        y_1 = location[1]
        in_range_cavs = []

        for single_vehicle in self.cavs:
            x_2 = single_vehicle.location[0]
            y_2 = single_vehicle.location[1]
            if x_2 - x_1 != 0 or y_2 - y_1 != 0:
                dist = math.sqrt((x_2 - x_1) ** 2 + (y_2 - y_1) ** 2)
                if dist <= length:
                    in_range_cavs.append(single_vehicle)
        return in_range_cavs


class Connection():
    """Handles a connection with the GUI"""
    def __init__(self, websocket, path):
        self.websocket = websocket
        self.addr = websocket.remote_address
        self.infrastructure = None
        self.vehicles = None

    async def get_parameters(self, data_type):
        """Get infrastructure parameters from the frontend"""
        payload_str = await self.websocket.recv()
        # Now convert the payload string to a json object
        payload = json.loads(payload_str)

        if data_type == "infrastructure":
            self.infrastructure = payload
        elif data_type == "vehicles":
            self.vehicles = payload
        else:
            raise ValueError("Parameter type unknown")

    async def send_frame(self, json_data):
        """Send frame from json data to GUI"""
        data = json.dumps(json_data)
        await self.websocket.send(data)

async def main(websocket, path):
    """Start the program with a connected frontend"""
    connect = Connection(websocket, path)
    await connect.get_parameters("infrastructure")
    await connect.get_parameters("vehicles")
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
