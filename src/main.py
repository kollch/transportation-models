"""This is the primary component of the backend."""
import asyncio
import ssl
import json
import websockets
import matplotlib.pyplot as plt
plt.style.use('ggplot')
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
            road = self.infrastructure.road_at(vehicle.loc)
            if road is None:
                raise RuntimeError("Vehicle not initialized on a road")
            vehicle.veloc[1] = road.lane_direction(vehicle.loc)
            road.vehicles_on.append(vehicle)
            vehicle.road = road
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

    async def build_frames(self):
        """Run simulation for certain number of frames;
        when ready to send a frame,
        call "await self.gui.send_frame(json)".
        """
        velocities = []
        accelerations = []
        auto_velocities = []
        human_velocities = []
        auto_accelerations = []
        human_accelerations = []
        for i in range(100):
            velocities.append([])
            accelerations.append([])
            auto_velocities.append([])
            human_velocities.append([])
            auto_accelerations.append([])
            human_accelerations.append([])
        x = []
        while True:
            x.append(self.current_frame)
            self.current_frame += 1
            self.sort_new_vehicles()
            # If there are no more vehicles
            if not self.new_vehicles and not self.cavs and not self.hvs:
                break
            # This is to keep the y and x axis the same length. Every
            # iteration, add a 'None' as the default value, and for the
            # vehicle loop, if the vehicle id is present in the frame,
            # it will delete the last 0 and push the actual vehicle
            # velocity, balancing out the y axis lengths to match the
            # x axis.
            for vlist in velocities:
                vlist.append(None)
            for alist in accelerations:
                alist.append(None)
            for auto_vlist in auto_velocities:
                auto_vlist.append(None)
            for auto_alist in auto_accelerations:
                auto_alist.append(None)
            for human_vlist in human_velocities:
                human_vlist.append(None)
            for human_alist in human_accelerations:
                human_alist.append(None)
            for intersection in self.infrastructure.intersections:
                intersection.road_open()
            for vehicle in self.cavs + self.hvs:
                if (vehicle.loc[0] < 0 or vehicle.loc[0] > 1600
                        or vehicle.loc[1] < 0 or vehicle.loc[1] > 1600):
                    if vehicle.autonomous:
                        self.cavs.remove(vehicle)
                    else:
                        self.hvs.remove(vehicle)
                    break
                vehicle.decide_move()
                if vehicle.at_dest():
                    if vehicle.autonomous:
                        self.cavs.remove(vehicle)
                    else:
                        self.hvs.remove(vehicle)
                if vehicle.autonomous:
                    auto_velocities[vehicle.vehicle_id] = auto_velocities[vehicle.vehicle_id][:-1]
                    auto_accelerations[vehicle.vehicle_id] = auto_accelerations[vehicle.vehicle_id][:-1]
                    auto_velocities[vehicle.vehicle_id].append(vehicle.veloc[0])
                    auto_accelerations[vehicle.vehicle_id].append(vehicle.accel)
                else:
                    human_velocities[vehicle.vehicle_id] = human_velocities[vehicle.vehicle_id][:-1]
                    human_accelerations[vehicle.vehicle_id] = human_accelerations[vehicle.vehicle_id][:-1]
                    human_velocities[vehicle.vehicle_id].append(vehicle.veloc[0])
                    human_accelerations[vehicle.vehicle_id].append(vehicle.accel)

                velocities[vehicle.vehicle_id] = velocities[vehicle.vehicle_id][:-1]
                accelerations[vehicle.vehicle_id] = accelerations[vehicle.vehicle_id][:-1]
                velocities[vehicle.vehicle_id].append(vehicle.veloc[0])
                accelerations[vehicle.vehicle_id].append(vehicle.accel)

                plt.subplot(2, 3, 1)
                plt.title("Vehicle Velocities")
                plt.plot(x, velocities[vehicle.vehicle_id])
                plt.xlabel("frame number")
                plt.ylabel("velocity")
                
                plt.subplot(2, 3, 4)
                plt.title("Vehicle Accelerations")
                plt.plot(x, accelerations[vehicle.vehicle_id])
                plt.xlabel("frame number")
                plt.ylabel("acceleration")

                plt.subplot(2, 3, 2)
                plt.title("CAV Velocities")
                plt.plot(x, auto_velocities[vehicle.vehicle_id])
                plt.xlabel("frame number")
                plt.ylabel("velocity")

                plt.subplot(2, 3, 5)
                plt.title("CAV Accelerations")
                plt.plot(x, auto_accelerations[vehicle.vehicle_id])
                plt.xlabel("frame number")
                plt.ylabel("acceleration")
                
                plt.subplot(2, 3, 3)
                plt.title("HV Velocities")
                plt.plot(x, human_velocities[vehicle.vehicle_id])
                plt.xlabel("frame number")
                plt.ylabel("velocity")
                
                plt.subplot(2, 3, 6)
                plt.title("HV Accelerations")
                plt.plot(x, human_accelerations[vehicle.vehicle_id])
                plt.xlabel("frame number")
                plt.ylabel("acceleration")


            # Vehicle locations should have been changed now.
            # Build a new frame of JSON.
            frame = self.data_to_json()
            # Send frame
            await self.gui.send_frame(frame)
            print("Completed frame", self.current_frame)
        # Specify end of frames
        await self.gui.send_frame(None)
        print("Finished sending frames")
        plt.show()

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
