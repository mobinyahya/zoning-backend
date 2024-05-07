import yaml, ast, json, pickle
import types, textwrap
import re
import numpy as np
import pandas as pd
import textwrap, types, pandas
import gurobipy as gp
from Zone_Generation.design_zones import DesignZones
from Zone_Generation.zone_eval import Zone_Eval
from Zone_Generation.Zone_Helper.zone_vizualization import *
from Zone_Generation.Zone_Helper.util import Compute_Name
from Zone_Generation.Zone_Helper.local_search import *
from Zone_Generation.Config.Constants import *
from LLM.api_calls import make_api_call


class Filter_Request(object):
    def __init__(self, user_inputs):
        self.update_config(user_inputs)
        self.name = Compute_Name(self.config)

    def fetch_llm_response(self):
        self.solution_status = {}

        if self.config["request_constraint"] == "":
            return

        # llm_response = make_api_call(self.config["request_constraint"])
        # with open('LLM/llm_filteration_response_5_06.txt', 'w') as file:
        #     file.write(llm_response)


        with open('LLM/llm_filteration_response_5_06.txt', 'r') as file:
        # with open('LLM/llm_filteration_response.txt', 'r') as file:
            llm_response = file.read()


        try:
            response_json = ast.literal_eval(llm_response)
            latex_formula = repr(response_json["Latex_Formula"]['Formula'])
            latex_formula = latex_formula.replace('\\x0c', '\\\\f')

            # Remove the extra quotes added by repr()
            latex_formula = latex_formula[1:-1]
            latex_formula = re.sub('\\\\\\\\forall', '∀', latex_formula)
            latex_formula = latex_formula.replace('\\\\', '\\')

            # print("latex_formula", latex_formula)
            # print("response_json ", response_json)

            self.solution_status["Function_Code"] = response_json["Function_Code"]
            self.solution_status["Latex_Formula"] = {}
            self.solution_status["Latex_Formula"]["Variables"] = response_json["Latex_Formula"]["Variables"]
            self.solution_status["Latex_Formula"]["Formula"] = latex_formula.replace('\\\\', '\\')


            # self.solution_status["Latex_Formula"]["Formula"] = latex_formula
            # print("self.solution_status[Latex_Formula][Formula]", self.solution_status["Latex_Formula"]["Formula"])
            # print("response_json[Latex_Formula][Formula]", response_json["Latex_Formula"]["Formula"])
            # exit()

            # TODO replace // with / before returning the latex
            # TODO replace \forall with ∀ character (weird handling of that in the frontend)
            # TODO check if the structure of the Latex Formula is exactly as expected. (because otherwise we'll run into error on the frontend)

            # divided_string = llm_response.split('"')
            # self.solution_status["Function_Code"] = divided_string[3]

        except Exception as e:
            print(f"LLM Response has invalid format: {e}")
            self.solution_status["Function_Code"] = "Unable to parse the code"
            self.solution_status["Latex_Formula"] = {}
            self.solution_status["Latex_Formula"]["Variables"] = {}
            self.solution_status["Latex_Formula"]["Formula"] = "Unable To parse your additional constraints"
            self.solution_status["LLM_Request_Execution"] = False


    def update_config(self, user_inputs):
        with open("Zone_Generation/Config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        self.config["centroids_type"] = str(user_inputs["number_of_zones"]) + "-zone"
        self.config["FRL_Dev"] = user_inputs["FRL_Dev"]
        self.config["Z"] = user_inputs["number_of_zones"]
        self.config["request_constraint"] = user_inputs["request_constraint"]

    def load_zoning_without_llm_function(self, input_folder, zone_map_paths, ZE, ZV):
        with open(os.path.expanduser(input_folder + "/" + zone_map_paths[0]), 'rb') as file:
            zone_dict = pickle.load(file)
            ZE.build_zone_list(zone_dict)
            self.solution_status["zone_dict"] = ZE.zone_dict
            ZV.zones_from_dict(ZE.zone_dict)
            return

    def load_zoning_with_llm_function(self, input_folder, zone_map_paths, ZE, ZV):
        for zone_path in zone_map_paths:
            with open(os.path.expanduser(input_folder + "/" + zone_path), 'rb') as file:
                print("File: ", os.path.expanduser(input_folder + "/" + zone_path))
                zone_dict = pickle.load(file)
                ZE.build_zone_list(zone_dict)

                try:

                    Function_Code = textwrap.dedent(self.solution_status["Function_Code"])
                    # Change the Function_Code string into an executable function for Integer_Program class
                    local_scope = {}
                    global_scope = {
                        'np': np,
                        'pandas': pd,
                        'pickle': pickle,
                        'textwrap': textwrap,
                        'types': types,
                        **globals()
                    }
                    exec(Function_Code, global_scope, local_scope)
                    requested_function = local_scope['requested_function']
                    ZE.requested_function = types.MethodType(requested_function, ZE)
                    llm_cons_satisfied = ZE.requested_function()
                    self.solution_status["LLM_Request_Execution"] = True
                except Exception as e:
                    llm_cons_satisfied = False
                    print(f"An error occurred, proceeding without executing the requested function. Error: {e}")
                    self.solution_status["LLM_Request_Execution"] = False
                    break
                if llm_cons_satisfied:
                    self.solution_status["zone_dict"] = ZE.zone_dict
                    ZV.zones_from_dict(ZE.zone_dict)
                    return True
        return False
    def filter_zones(self):
        DZ = DesignZones(config=self.config)
        ZV = ZoneVisualizer(self.config["level"])
        ZE = Zone_Eval(DZ)


        input_folder = "Generated_Zones/Zones_" + str(self.config["Z"]) + "/FRL_Dev_0." + str(self.config["FRL_Dev"])
        # Sort zone maps in ascending order of their boundary cost
        zone_map_paths = sorted(
            [f for f in os.listdir(input_folder)], #if f.endswith('.pkl')
            key=lambda x: float(x.split('_')[1].replace('.pkl', ''))
        )

        if "Function_Code" not in self.solution_status:
            self.load_zoning_without_llm_function(input_folder, zone_map_paths, ZE, ZV)
            return
        else:
            llm_cons_satisfied = self.load_zoning_with_llm_function(input_folder, zone_map_paths, ZE, ZV)
            if llm_cons_satisfied == False:
                print("We couldn't meet your additional constraints, but here's a solution that fits your fixed settings from the dashboard.")
                self.load_zoning_without_llm_function(input_folder, zone_map_paths, ZE, ZV)
                return

if __name__ == "__main__":
    user_inputs = {}
    user_inputs["FRL_Dev"] = 2
    user_inputs["number_of_zones"] = 6
    # user_inputs["request_constraint"] = ("Write a function in python to make sure the average school"
    #                                   " quality across zones is within 20% deviation. Use Math"
    #                                   "Score at school level to compute school quality.")
    user_inputs["request_constraint"] = ("Make sure each zone has one of the top 10 schools in SF. "
                                         "Use 'Met' standard ranking as a quality metric to find the top school.")
    FR = Filter_Request(user_inputs)
    FR.fetch_llm_response()
    FR.filter_zones()
    if "Latex_Formula" in FR.solution_status:
        print("FR.solution_status[Latex_Formula][Formula]: ",  FR.solution_status["Latex_Formula"]["Formula"])
        print("FR.solution_status[Latex_Formula]: ",  FR.solution_status["Latex_Formula"])
