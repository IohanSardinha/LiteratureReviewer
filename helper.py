import pickle
from os import path

def saveData(variable, name):
    with open(path.join(path.dirname(__file__),f"data/{name}"), "wb") as file:
        pickle.dump(variable, file)

def loadData(name):
    if not path.isfile(path.join(path.dirname(__file__),f"data/{name}")): 
        return
    
    with open(path.join(path.dirname(__file__),f"data/{name}"), "rb") as file:
        variable = pickle.load(file)
    return variable