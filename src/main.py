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
            vehicle_obj = self.new_vehicles.pop(0)
            vehicle = vehicle_obj["vehicle"]
            for road in self.infrastructure.roads:
                if road.has_point(vehicle.loc):
                    vehicle.veloc[1] = road.lane_direction(vehicle.loc)
                    road.vehicles_on.append(vehicle)
                    break
            if vehicle.autonomous:
                self.cavs.append(vehicle)
                continue
            self.hvs.append(vehicle)

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

    def stats_to_json(self):
        """Sends vehicle stats to a json file."""
        stats = {}
        stats['vehicles'] = []

        for vehicle in self.cavs + self.hvs:
            stats['vehicles'].append({
                'id': vehicle.vehicle_id,
                'velocity': vehicle.veloc[0],
                'acceleration': vehicle.accel
            })

        with open('vehicle_stats.json', 'w') as outfile:
            json.dump(stats, outfile, indent=4)

    def data_to_json(self):
        """Takes data from vehicle list and puts into a json file as a
        new frame.
        """
        data = {}
        data['frameid'] = self.current_frame
        data['vehicles'] = []
        for vehicle in self.cavs + self.hvs:
            data['vehicles'].append({
                'id': vehicle.vehicle_id,
                'loc': {
                    'x': vehicle.loc[0],
                    'y': vehicle.loc[1]
                },
                'direction': vehicle.veloc[1]
            })
        return data

    async def build_frames(self, num_frames=100):
        """Run simulation for certain number of frames;
        when ready to send a frame,
        call "await self.gui.send_frame(json)".
        """
        for frame in range(num_frames):
            self.current_frame += 1
            self.sort_new_vehicles()
            for vehicle in self.cavs + self.hvs:
                vehicle.decide_move()

            # Vehicle locations should have been changed now.
            # Build a new frame of JSON.
            frame = self.data_to_json()
            # Send frame
            print("Sending frame #" + str(self.frame_number))
            await self.gui.send_frame(frame)
        # Specify end of frames
        await self.gui.send_frame(None)

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
