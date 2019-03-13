"""This is the primary component of the backend."""
import asyncio
import ssl
import json
import websockets

from vehicles import CAV, HV
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
        self.new_vehicles = []
        self.cavs = []
        self.hvs = []
        self.set_parameters()
        self.current_frame = 0
        self.frame_number = 0

    def init_vehicle_dir(self, vehicle):
        """Initialize vehicle direction based on which road it's on"""

    def init_intersections(self):
        """Initialize intersections"""
        return [
            Intersection(item['id'],
                         item['connects_roads'],
                         (item['loc']['x'], item['loc']['y']))
            for item in self.gui.infrastructure['intersections']
        ]

    def init_roads(self, intersections):
        """Initialize roads"""
        roads = []
        for item in self.gui.infrastructure['roads']:
            ends = [item['ends'][0], item['ends'][1]]
            # Convert road endpoints to tuples if they're coordinates
            for i in range(2):
                try:
                    ends[i] = (ends[i]['x'], ends[i]['y'])
                except TypeError:
                    for intersection in intersections:
                        if intersection.intersection_id == ends[i]:
                            ends[i] = intersection
                            break
            roads.append(Road(item['id'], (item['two_way'], item['lanes'],
                                           (ends[0], ends[1]))))
        return roads

    def init_vehicles(self):
        """Initialize vehicles"""
        for item in self.gui.vehicles:
            if item['type'] == 0:
                vehicle = HV(self)
            elif item['type'] == 1:
                vehicle = CAV(self)
            else:
                raise ValueError
            vehicle.vehicle_id = item['id']
            vehicle.loc = (item['start_loc']['x'], item['start_loc']['y'])
            vehicle.plan[0] = (item['end_loc']['x'], item['end_loc']['y'])
            self.new_vehicles.append({'entry': item['entry_time'],
                                      'vehicle': vehicle})
        self.new_vehicles.sort(key=lambda o: o['entry'])

    def sort_new_vehicles(self):
        """Takes vehicles from new_vehicles and appends to cavs/hvs
            respectively where entry time <= current frame.
        """
        while self.new_vehicles:
            if self.new_vehicles[0]["entry"] / 100 > self.current_frame:
                break
            if self.new_vehicles[0]["vehicle"].autonomous:
                self.cavs.append(self.new_vehicles.pop(0))
                continue
            self.hvs.append(self.new_vehicles.pop(0))

    def set_parameters(self):
        """Set parameters pulled from GUI, aka initializing simulation
        Parameters: num_frames, vehicle positions, infrastructure setup
        """
        intersections = self.init_intersections()
        roads = self.init_roads(intersections)
        for intersection in intersections:
            for i, road_id in enumerate(intersection.roads):
                if road_id is None:
                    continue
                for road in roads:
                    if road_id == road.road_id:
                        intersection.roads[i] = road
                        break
        self.infrastructure = Infrastructure(intersections, roads)
        self.init_vehicles()

    def data_to_json(self):
        # takes data from vehicle array and puts into a json file as a new frame.

        # TODO: Needs modification in vehicles.py to match json keys. Currently testframes
        # and the attributes in the Vehicle class are not exactly the same.
        data = {}
        data['frameid'] = self.frame_number
        data['vehicles'] = []
        for i in range(len(self.cavs)):
            data['vehicles'].append({
                'id': self.cavs[i].vehicle_id,
                'loc': {
                    'x': self.cavs[i].location['x'],
                    'y': self.cavs[i].location['y']
                },
                'destination': {
                    'x': self.cavs[i].destination['x'],
                    'y': self.cavs[i].destination['y']
                }
            })

        for i in range(len(self.hvs)):
            data['vehicles'].append({
                'id': self.hvs[i].vehicle_id,
                'loc': {
                    'x': self.hvs[i].location['x'],
                    'y': self.hvs[i].location['y']
                },
                'destination': {
                    'x': self.hvs[i].destination['x'],
                    'y': self.hvs[i].destination['y']
                }
            })
        # dump the data into json
        with open('frame.json', 'w') as outfile:
            json.dump(data, outfile, indent=4)

    async def build_frames(self):
        """Run simulation for certain number of frames;
        when ready to send a frame,
        call "await self.gui.send_frame(json)".
        """
        # decide each vehicle's move.
        #TODO decide_move should change the attributes in the
        # HV and CAV classes

        for cav in self.cavs:
            cav.decide_move()

        for hv in self.hvs:
            hv.decide_move()

        # vehicle locations should have been changed now. call data_to_json to build a new frame
        self.data_to_json()

        # send frame
        await self.gui.send_frame("frame.json")

    def cavs_in_range(self, location, length):
        """Gives list of CAVs within distance of length (in feet) of
        location
        """
        return [
            vehicle
            for vehicle in self.cavs
            if 0 < vehicle.dist_to(location) <= length
        ]


class Connection():
    """Handles a connection with the GUI"""
    def __init__(self, websocket, path):
        self.websocket = websocket
        self.path = path
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

'''
def get_frame_data(file_name, frame):
    """Temporary function to read json from a file;
    should be deleted soon
    """
    with open(file_name) as json_file:
        data = json.load(json_file)
        return data[frame]
'''

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
