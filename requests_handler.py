import yaml, ast, json
import types, textwrap
import gurobipy as gp
from Zone_Generation.design_zones import DesignZones
from Zone_Generation.integer_program import Integer_Program
from Zone_Generation.Zone_Helper.zone_vizualization import *
from Zone_Generation.Zone_Helper.util import Compute_Name
from Zone_Generation.Zone_Helper.local_search import *
from Zone_Generation.Config.Constants import *
from LLM.api_calls import make_api_call


class Requests_Handler(object):
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
        # with open('LLM/llm_response.txt', 'w') as file:
        #     file.write(llm_response)


        with open('LLM/llm_response.txt', 'r') as file:
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


    def generate_aa_zones(self):
        self.config["level"] = "attendance_area"
        DZ = DesignZones(config=self.config)
        IP = Integer_Program(DZ)
        IP._initializs_feasiblity_constraints(max_distance=max_distance[self.config["Z"]])
        return self.generate_zones(DZ, IP)

    def generate_bg_zones(self):
        self.config["level"] = "BlockGroup"

        DZ = DesignZones(self.config)
        # zv = ZoneVisualizer(self.config["level"])

        load_initial_assignemt(DZ, path=self.config["path"], name=self.name, load_level="attendance_area")
        # zv.zones_from_dict(DZ.zone_dict, centroid_location=DZ.schools_locations)

        DZ.zd = drop_boundary(DZ, DZ.zone_dict)
        # zv.zones_from_dict(DZ.zone_dict, centroid_location=DZ.centroid_location)

        DZ.zone_dict = trim_noncontiguity(DZ, DZ.zone_dict)
        # zv.zones_from_dict(DZ.zone_dict, centroid_location=DZ.centroid_location)

        IP = Integer_Program(DZ)
        IP._initializs_feasiblity_constraints(max_distance=max_distance[self.config["Z"]])
        initialize_preassigned_units(IP, DZ.zone_dict)
        return self.generate_zones(DZ, IP)



    def generate_zones(self, DZ, IP):
        IP._set_objective_model()
        IP._shortage_constraints(shortage=self.config["shortage"], overage=self.config["overage"],
                                 all_cap_shortage=self.config["all_cap_shortage"])
        IP._add_contiguity_constraint()
        IP._add_diversity_constraints(racial_dev=self.config["racial_dev"], frl_dev=self.config["frl_dev"])
        IP._add_school_count_constraint()

        if self.solution_status["Function_Code"] != "":
            try:
                Function_Code = textwrap.dedent(self.solution_status["Function_Code"])
                print("Function_Code ", Function_Code)
                # Change the Function_Code string into an executable function for Integer_Program class
                local_scope = {}
                exec(Function_Code, globals(), local_scope)
                requested_function = local_scope['requested_function']
                IP.requested_function = types.MethodType(requested_function, IP)
                IP.requested_function()
                self.solution_status["LLM_Request_Execution"] = True
            except Exception as e:
                print(f"An error occurred, proceeding without executing the requested function. Error: {e}")
                self.solution_status["LLM_Request_Execution"] = False

        solve_success = DZ.solve(IP)
        if solve_success == 1:
            self.solution_status["Solution_Generation"] = True
            DZ.save(path=self.config["path"], name=self.name+"_"+SUFFIX[self.config["level"]])
            # print("Resulting zone dictionary: ", DZ.zone_dict)

            zv = ZoneVisualizer(self.config["level"])
            zv.zones_from_dict(DZ.zone_dict,
                   save_path=self.config["path"] + self.name + "_" + SUFFIX[self.config["level"]])
        else:
            self.solution_status["Solution_Generation"] = False


if __name__ == "__main__":
    user_inputs = {}
    user_inputs["shortage"] = 0.25
    user_inputs["number_of_zones"] = 4
    # user_inputs["request_constraint"] = ("Write a function in python to make sure the average school"
    #                                   " quality across zones is within 20% deviation. Use Math"
    #                                   "Score at school level to compute school quality.")
    user_inputs["request_constraint"] = ""
    RH = Requests_Handler(user_inputs)
    RH.fetch_llm_response()
    # RH.generate_aa_zones()
    RH.generate_bg_zones()
