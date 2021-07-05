import os,sys
import re
import pymongo
import pandas as pd
import numpy as np
from datetime import datetime,timezone,timedelta
from collections import Counter
import numpy as np
from scipy.stats import \
    nbinom,\
    nhypergeom,\
    betabinom

from scipy.optimize import minimize
from matplotlib import pyplot as plt
from sklearn.neighbors import KNeighborsRegressor as knn
from . import analysis
from .db import symptoms_db


class knn_dist:

    def __init__(self,neighbors=4):
        self.neighbors = neighbors
        self.model = None
        self.partition = None
        self.xmin = None
        self.xmax = None

    def fit(self,x,y):
        model = knn(self.neighbors)
        X = np.array(x).reshape(-1,1)
        model.fit(X,y)
        self.model = model
        self.xmin = min(x)
        self.xmax = max(x)
        XX = np.arange(self.xmin,self.xmax+1).reshape(-1,1)
        p = model.predict(XX)
        self.partition = sum(p)

    
    def predict(self,x):
        if self.model is None:
            raise ValueError("No fit KNN model.  Run fit(X,y) first.")
        X = np.array(x).reshape(-1,1)
        return self.model.predict(X)
    
    def pmf_single(self,x):
        if self.model is None:
            raise ValueError("No fit KNN model.  Run fit(X,y) first.")
        if (x >= self.xmin) and (x <= self.xmax):
            return self.predict(x)[0]/self.partition
        else:
            return 0

    def pmf(self,x):
        if (isinstance(x,float) or isinstance(x,int)):
            return self.pmf_single(x)
        else:
            return np.array([self.pmf_single(i) for i in x])
    
    def logpmf(x):
        return np.log(self.pmf(x) + 0.00000000001)
    
