import pandas as pd
import ast
import os, sys
import numpy as np
sys.path.append("Zone_Generation/")

from Config.Constants import *
class Students(object):
    def __init__( self, config):
        self.drop_optout = config["drop_optout"]
        self.years = config["years"]
        self.population_type = config["population_type"]


    def load_student_data(self):
        cleaned_student_path = ("Zone_Generation/Zone_Data/Cleaned_Students_" +
                                '_'.join([str(year) for year in self.years]) + ".csv")
        if os.path.exists(cleaned_student_path):
            student_df = pd.read_csv(cleaned_student_path, low_memory=False)
            return student_df