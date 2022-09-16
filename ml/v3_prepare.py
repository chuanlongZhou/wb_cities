import os
import pickle
import argparse
from ml.add_all_features import *
from ml.preprocessing import *

def prepare(data, city):
    data = add_all_features(data, city)
    path = os.path.join("data", "ml", "datasets", city+".pkl")
    print(data.head(10))
    with open(path,"wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def main():
    description = "This script prepares the city dataset so it can be fed into the ML pipeline"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('city', type=str, help="The city's name")
    args = parser.parse_args()
    city = args.city
    path = os.path.join(".", "data", "ml", city+".pkl")
    with open(path, 'rb') as f:     
        data = pickle.load(f)
        prepare(data, city)    
    return

main()
