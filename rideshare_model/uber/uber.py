from uber_rides.session import Session
from uber_rides.client import UberRidesClient
from key import TOKEN

session = Session(server_token=<TOKEN>)
client = UberRidesClient(session)
