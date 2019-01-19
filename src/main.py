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
        file_data_json = get_json_data("./data.json")
        intersections_id_data = []
        intersections_road_data = []
        intersections_position_data = []
        num_of_intersections = data_from_intersection(file_data_json, intersections_id_data, intersections_road_data, intersections_position_data)
        intersection_list = []
        for i in range(num_of_intersections):
            intersection_list.append(Intersection(intersections_id_data[i],intersections_road_data[i],intersections_position_data[i]))
            print(intersection_list[i].roads)
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

def data_from_intersection(file_data_json, id_data, roads_data, loc_data):
    num_of_intersections = 0
    current_count_num = 0
    for intersections in file_data_json['intersections']:
        """Store Intersections' id"""
        id_data.append(intersections['id'])
        """append roads data to 2d list"""
        roads_data.append([])
        """store intersections' location"""
        loc_data.append((intersections['loc']['x'],intersections['loc']['y']))
        num_of_intersections += 1
    for intersections in file_data_json['intersections']:
        """store intersections' roads in 2d list"""
        for i in range(4):
            roads_data[current_count_num].append(intersections['connects_roads'][i])
        current_count_num += 1
    return num_of_intersections

def get_json_data(file_name):
    """read json file data"""
    with open(file_name) as json_file:
        data = json.load(json_file)
        return data

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
