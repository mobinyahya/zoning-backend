from Zone_Generation.zone_eval_abstract import Zone_Eval_Abstract
import numpy as np


class Zone_Eval(Zone_Eval_Abstract):
    def __init__(self, Area_Data):
        super().__init__(Area_Data)  # Constructor of Zone_Eval_Abstract
        # self.idx2area: A dictionary, mapping each area index in our data, to its census area code
        # (keys: area index j), (values: census area code for the area with index j)
        # Example: self.idx2area[41] == census area code for the area with index 41)
        # Computation based on area_data file: self.idx2area = dict(zip(self.area_data.index, self.area_data[self.level]))
        self.idx2area = Area_Data.idx2area

        # self.area2idx: A dictionary, mapping each census area code, to its index in our data
        # (keys: census area code AA), (values: index of area AA, in our data set)
        # Example: self.area2idx[area code AA] == index of area AA in our data set
        # Note that we can access our dictionaries only using the area index, and not the area code
        # Computation based on area_data file: self.area2idx = dict(zip(self.area_data[self.level], self.area_data.index))
        self.area2idx = Area_Data.area2idx

        # Dictionary: self.neighbors
        # - Keys: unit v
        # - Values: List of indices for neighboring units to unit v
        # Example: self.neighbors[41] returns [32, 12, 52, 2], the indices of units adjacent to unit 41.
        self.neighbors = Area_Data.neighbors

        # Dictionary: self.closer_euc_neighbors
        # - Keys: a pair (unit u, zone index z)
        # - Values: List of indices for neighboring units to unit u that are closer to the centroid of zone z than unit u is
        # Example: self.closer_euc_neighbors[41, 3] returns [32, 2], indicating units adjacent to unit 41 that are closer to the centroid of zone 3 than unit 41.
        self.closer_euc_neighbors = Area_Data.closer_euc_neighbors

        # Dictionary: self.euc_distances
        # - Keys: a pair of units (u, v)
        # - Values: Euclidean distance in miles between unit u and unit v
        # Example: self.euc_distances[41, 13] returns 3.42, indicating units 41 and 13 are 3.42 miles apart.
        self.euc_distances = Area_Data.euc_distances

        self.level = Area_Data.level

    # input a dictionary, mapping each blockgroup to a school id. School ids represent separate zone centers
    def build_zone_list(self, zone_dict):

        # Find the unique school IDs and sort them (sorting is optional but helps keep consistent order)
        unique_school_ids = sorted(set(zone_dict.values()))

        # Create a dictionary to map school IDs to zone indexes
        school_id_to_zone_index = {school_id: index for index, school_id in enumerate(unique_school_ids)}

        # Initialize a list of empty lists for zones
        zones = [[] for _ in range(len(unique_school_ids))]
        zd = {}
        # Populate the zones list
        for bg, school_id in zone_dict.items():
            zone_index = school_id_to_zone_index[school_id]
            zones[zone_index].append(self.area2idx[bg])
            zd[bg] = zone_index

        self.zones = zones
        self.zone_dict = zd


    # This function constructs the boundary cost variables.
    # Boundary cost variables are used in the optimization model objective
    def set_y_boundary(self):
        boundary_cost = 0
        for u in range(self.U):
            for v in self.neighbors[u]:
                if u >= v:
                    continue
                if self.zone_dict[u] != self.zone_dict[v]:
                    boundary_cost += 1

        return boundary_cost


    def evaluate_distance(self):
        distance_cost = 0
        for z in range(self.Z):
            centroid_z = self.centroids[z]
            distance_cost += sum([self.euc_distances[u, centroid_z] ** 2 * self.studentsInArea[u] for u in self.zones[z]])
            # distance_cost += sum([(self.drive_distances[u, centroid_z] ** 2) * self.studentsInArea[u] for u in self.zones[z]])

        return distance_cost

    # remove blockgroups that are very far from the centroid of their
    # zone and make it unassigned. This is part of trimming process
    def drop_centroid_distant(self, max_distance):
        for z in range(self.Z):
            for u in self.zones[z]:
                if self.euc_distances[self.centroids[z]][u] > max_distance:
                    return False
        return True
