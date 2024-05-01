import yaml, ast, json, pickle
import types, textwrap
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
            self.solution_status["Function_Code"] = ""
            self.solution_status["Latex_Formula"] = ""
            return

        # llm_response = make_api_call(self.config["request_constraint"])
        # with open('LLM/llm_filteration_response.txt', 'w') as file:
        #     file.write(llm_response)


        with open('LLM/llm_filteration_response.txt', 'r') as file:
            llm_response = file.read()


        response_json = ast.literal_eval(llm_response)
        self.solution_status["Function_Code"] = response_json["Function_Code"]
        self.solution_status["Latex_Formula"] = response_json["Latex_Formula"]
        # TODO replace // with / before returning the latex

        # divided_string = llm_response.split('"')
        # self.solution_status["Function_Code"] = divided_string[3]


    def update_config(self, user_inputs):
        with open("Zone_Generation/Config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        self.config["centroids_type"] = str(user_inputs["number_of_zones"]) + "-zone"
        self.config["shortage"] = user_inputs["shortage"]
        self.config["Z"] = user_inputs["number_of_zones"]
        self.config["request_constraint"] = user_inputs["request_constraint"]


    def filter_zones(self):
        DZ = DesignZones(config=self.config)
        ZV = ZoneVisualizer(self.config["level"])
        ZE = Zone_Eval(DZ)

        input_folder = "Generated_Zones/Zones_" + str(self.config["Z"]) + "/Shortage_" + str(self.config["shortage"])
        # Sort zone maps in ascending order of their boundary cost
        zone_map_paths = sorted(
            [f for f in os.listdir(input_folder) if f.endswith('.pkl')],
            key=lambda x: int(x.split('_')[1].replace('.pkl', ''))
        )

        isValid = True
        for zone_path in zone_map_paths:
            print("zone_path ", zone_path)
            with open(os.path.expanduser(input_folder + "/" + zone_path), 'rb') as file:
                zone_dict = pickle.load(file)
                ZE.build_zone_list(zone_dict)
                # isValid = ZE.requested_function()
                # print(isValid)
                # exit()

                if self.solution_status["Function_Code"] != "":
                    try:
                        Function_Code = textwrap.dedent(self.solution_status["Function_Code"])
                        # Change the Function_Code string into an executable function for Integer_Program class
                        local_scope = {}
                        exec(Function_Code, globals(), local_scope)
                        requested_function = local_scope['requested_function']
                        ZE.requested_function = types.MethodType(requested_function, ZE)
                        isValid = ZE.requested_function()

                        self.solution_status["LLM_Request_Execution"] = True
                    except Exception as e:
                        print(f"An error occurred, proceeding without executing the requested function. Error: {e}")
                        self.solution_status["LLM_Request_Execution"] = False
                        isValid = False
                        break
                if isValid:
                    ZV.zones_from_dict(ZE.zone_dict)
                    break
        if isValid == False:
            print("We couldn't meet your additional constraints, but here's a solution that fits your fixed settings from the dashboard.")
            with open(os.path.expanduser(input_folder + "/" + zone_map_paths[0]), 'rb') as file:
                zone_dict = pickle.load(file)
                ZE.build_zone_list(zone_dict)
                ZV.zones_from_dict(ZE.zone_dict)


if __name__ == "__main__":
    user_inputs = {}
    user_inputs["shortage"] = 0.2
    user_inputs["number_of_zones"] = 6
    user_inputs["request_constraint"] = ("Write a function in python to make sure the average school"
                                      " quality across zones is within 20% deviation. Use Math"
                                      "Score at school level to compute school quality.")
    # user_inputs["request_constraint"] = ""
    RH = Filter_Request(user_inputs)
    RH.fetch_llm_response()
    RH.filter_zones()
