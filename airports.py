import os

def get_airport_codes():
    with open(os.path.join(os.getcwd(), 'airports')) as f:
        airports = f.readlines()
    return [x.strip() for x in airports if x.strip()]
