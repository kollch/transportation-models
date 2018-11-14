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

    def set_parameters():
        """Set parameters pulled from GUI, aka initializing simulation
        Parameters: num_frames, vehicle positions, infrastructure setup
        """
        return

    def build_frames():
        """Run simulation for certain number of frames"""
        return

    def cavs_in_range(location, length):
        """Gives list of CAVs within distance of length (in meters) of
        location
        """
        return

class Connection():
    """Handles a connection with the GUI"""
    def establish():
        """Make connection with GUI (using websockets)"""
        return

    def get_parameters():
        """Get parameters from GUI and store them"""
        return

    def close():
        """Close connection with GUI"""
        return

def main():
    """Start the program"""
    connect = Connection()
    connect.establish()
    connect.get_parameters()
    run = InvisibleHand(connection)
    run.build_frames()
    connect.close()

while True:
    main()
