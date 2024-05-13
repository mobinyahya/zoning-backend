import yaml, ast, json, pickle
import types, textwrap
import re, os
import numpy as np
import pandas as pd
import textwrap, types, pandas
from Zone_Generation.design_zones import DesignZones
from Zone_Generation.zone_eval import Zone_Eval
# from Zone_Generation.Zone_Helper.zone_vizualization import *
from Zone_Generation.Zone_Helper.util import Compute_Name
# from Zone_Generation.Zone_Helper.local_search import *
from Zone_Generation.Config.Constants import *
# from LLM.api_calls import make_api_call


class Filter_Request(object):
    def __init__(self, user_inputs):
        self.update_config(user_inputs)
        self.name = Compute_Name(self.config)

    def response_string_cleaning(self, llm_response):
        # Drop any initial explanation that is proivided before the first "{"
        if not llm_response.startswith("{"):
            idx = llm_response.find("{")
            if idx != -1:
                llm_response = llm_response[idx:]

        # Drop any follow-up explanation that is proivided after the last "}"
        if not llm_response.endswith("}"):
            idx = llm_response.rfind("}")
            if idx != -1:
                llm_response = llm_response[:idx + 1]
        return llm_response

    def fetch_llm_response(self):
        self.solution_status = {}

        if self.config["request_constraint"] == "":
            return

        try:
            # llm_response = make_api_call(self.config["request_constraint"])
            # with open('LLM/llm_filteration_response_5_12_3.txt', 'w') as file:
            #     file.write(llm_response)


            # with open('LLM/llm_filteration_response_5_06_1.txt', 'r') as file:
            # with open('LLM/llm_filteration_response_5_05.txt', 'r') as file:
            # with open('LLM/llm_filteration_response_5_06.txt', 'r') as file:
            with open('LLM/llm_filteration_response_5_12_2.txt', 'r') as file:
                llm_response = file.read()

            llm_response = self.response_string_cleaning(llm_response)
            llm_response = llm_response.strip()
            # response_json = json.loads(llm_response)
            response_json = ast.literal_eval(llm_response)

            latex_formula = repr(response_json["Latex_Formula"]['Formula'])
            latex_formula = latex_formula.replace('\\x0c', '\\\\f')

            # Remove the extra quotes added by repr()
            latex_formula = latex_formula[1:-1]
            # Replacing \forall with ∀ character (weird handling of "\forall" in the frontend)
            latex_formula = re.sub('\\\\\\\\forall', '∀', latex_formula)
            latex_formula = latex_formula.replace('\\\\', '\\')

            print("latex_formula", latex_formula)
            print("response_json ", response_json)

            self.solution_status["Function_Code"] = response_json["Function_Code"]
            self.solution_status["Latex_Formula"] = {}
            self.solution_status["Latex_Formula"]["Variables"] = response_json["Latex_Formula"]["Variables"]
            self.solution_status["Latex_Formula"]["Formula"] = latex_formula.replace('\\\\', '\\')


            # self.solution_status["Latex_Formula"]["Formula"] = latex_formula
            # print("self.solution_status[Latex_Formula][Formula]", self.solution_status["Latex_Formula"]["Formula"])
            # print("response_json[Latex_Formula][Formula]", response_json["Latex_Formula"]["Formula"])


        except Exception as e:
            print(f"LLM Response has invalid format: {e}")
            self.solution_status["Latex_Formula"] = {}
            self.solution_status["Latex_Formula"]["Variables"] = {}
            self.solution_status["Latex_Formula"]["Formula"] = "Parsing_Failed"
            self.solution_status["LLM_Request_Execution"] = "Unfulfilled"

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
            # ZV.zones_from_dict(ZE.zone_disct)
            return

    def load_zoning_with_llm_function(self, input_folder, zone_map_paths, ZE, ZV):
        for zone_path in zone_map_paths:
            self.solution_status["LLM_Request_Execution"] = "Unfulfilled"
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
                    llm_fulfilled = ZE.requested_function()
                except Exception as e:
                    llm_fulfilled = False
                    self.solution_status["LLM_Request_Execution"] = "Unable to Run"
                    print(f"An error occurred, proceeding without executing the requested function. Error: {e}")
                    break
                if llm_fulfilled:
                    self.solution_status["zone_dict"] = ZE.zone_dict
                    self.solution_status["LLM_Request_Execution"] = "Fulfilled"
                    # ZV.zones_from_dict(ZE.zone_dict)
                    return
        return False
    def filter_zones(self):
        DZ = DesignZones(config=self.config)
        # ZV = ZoneVisualizer(self.config["level"])
        ZV = {}
        ZE = Zone_Eval(DZ)


        input_folder = "Generated_Zones/Zones_" + str(self.config["Z"]) + "/FRL_Dev_0." + str(self.config["FRL_Dev"])
        # Sort zone maps in ascending order of their boundary cost
        zone_map_paths = sorted(
            [f for f in os.listdir(input_folder)], #if f.endswith('.pkl')
            key=lambda x: float(x.split('_')[1].replace('.pkl', ''))
        )

        if "Function_Code" not in self.solution_status:
            self.load_zoning_without_llm_function(input_folder, zone_map_paths, ZE, ZV)
        else:
            self.load_zoning_with_llm_function(input_folder, zone_map_paths, ZE, ZV)
            if self.solution_status["LLM_Request_Execution"] != "Fulfilled":
                print("We couldn't meet your additional constraints, but here's a solution that fits your fixed settings from the dashboard.")
                self.load_zoning_without_llm_function(input_folder, zone_map_paths, ZE, ZV)

        ZE.build_zone_list(self.solution_status["zone_dict"])
        self.solution_status["racial_dict"] = ZE.compute_racial_pcnt()


if __name__ == "__main__":
    user_inputs = {}
    user_inputs["FRL_Dev"] = 20
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
