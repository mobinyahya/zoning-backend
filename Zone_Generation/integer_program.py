from Zone_Generation.integer_program_abstract import Integer_Program_Abstract
import gurobipy as gp
import numpy as np
from gurobipy import GRB


class Integer_Program(Integer_Program_Abstract):
    def __init__(self, Area_Data):
        super().__init__(Area_Data)  # Constructor of Integer_Program_Minimized
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

        # self.sch2area: A dictionary, mapping each school id, to its census area code
        # Example: self.sch2area[644] == sensus area code for the school, with school id 644
        # Computation based on area_data file: self.sch2area = dict(zip(self.school_df["school_id"], self.school_df[self.level]))
        self.sch2area = Area_Data.sch2area

    def set_y_distance(self):
        y_distance = self.m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="distance distortion")

        for z in range(self.Z):
            zone_dist_sum = gp.quicksum([((self.euc_distances[self.centroids[z]][v]) ** 2) * self.x[v, z] for v in range(self.U)])
            # zone_dist_sum = gp.quicksum([((self.drive_distances.loc[centroid_unit, str(self.idx2unit[v])]) ** 2) * self.x[v, z] for v in range(self.U)])
            self.m.addConstr(zone_dist_sum <= y_distance)
        return y_distance

    def set_y_balance(self):
        y_balance = self.m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="balance distortion")

        # minimize the maximum distortion from average number of students (across zones)
        for z in range(self.Z):
            zone_stud = gp.quicksum([self.studentsInArea[v] * self.x[v, z] for v in range(self.U)])
            self.m.addConstr(self.N / self.Z - zone_stud <= y_balance)
            self.m.addConstr(zone_stud - self.N / self.Z <= y_balance)
        return y_balance

    def set_y_shortage(self):
        y_shortage = self.m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="shortage distortion")

        # minimize the maximum distortion from average student
        # deficit (student capacity -  number of seats) (across zones)
        for z in range(self.Z):
            zone_stud = gp.quicksum([self.studentsInArea[v] * self.x[v, z] for v in range(self.U)])
            zone_seats = gp.quicksum([self.seats[v] * self.x[v, z] for v in range(self.U)])
            self.m.addConstr(zone_stud - zone_seats <= y_shortage)
        return y_shortage


    def _set_objective_model(self):
        # y_distance = self.set_y_distance()
        # distance_coef = 1
        #
        # y_balance = self.set_y_balance()
        # balance_coef = 0
        #
        # y_shortage = self.set_y_shortage()
        # shortage_coef = 2

        y_boundary = self.set_y_boundary()

        # set the objective of the Integer Program.
        # The integer program will try to minimize the cost of boundary,
        # which will result into compact and nice looking shapes for zones.
        self.m.setObjective(y_boundary, GRB.MINIMIZE)
        # self.m.setObjective(1 , GRB.MINIMIZE)
        # self.m.setObjective(distance_coef * y_distance +  shortage_coef * y_shortage +
        #                      balance_coef * y_balance + boundary_coef * y_boundary , GRB.MINIMIZE)



    # Designing contiguous school zones is desirable for practical reasons,
    # i.e. school commutes and policy communication.
    # Make sure units assigned to each zone form a contiguous zone as follows:
    # assign unit j to zone with centroid unit z, only if
    # there is a ‘path’ of closer neighboring units also assigned
    # to the same zone that connects unit j to the centroid unit z.
    def _add_contiguity_constraint(self):
        # initialization - every centroid belongs to its own zone
        for z in range(self.Z):
            self.m.addConstr(
                self.x[self.centroids[z], z] == 1, name="Centroids to Zones"
            )

        # Constraint: (x[v,z] (an indicator that unit v is assigned to zone z)) < (sum of all x[i,z] where i is in self.closer_neighbors_per_centroid[v,c] where c is centroid for z)
        for u in range(self.U):
            for z in range(self.Z):
                if self.centroids[z] == u:
                    continue
                if self.centroids[z] in self.neighbors[u]:
                    continue
                if u not in self.valid_units_per_zone[z]:
                    continue
                # only impose the contiguity if the unit v has a neighbor that is closer to centroid z.
                # otherwise, just make sure v has at least another neighbor assigned tot the same zone z, so that
                # v is not an island assigned to z.
                if len(self.closer_euc_neighbors[u, self.centroids[z]]) >= 1:
                    neighbor_sum = gp.quicksum(
                        self.x[k, z]
                        for k in self.closer_euc_neighbors[u, self.centroids[z]]
                        if k in self.valid_units_per_zone[z]
                    )
                    self.m.addConstr(self.x[u, z] <= neighbor_sum, name="Contiguity")
                else:
                    any_neighbor_sum = gp.quicksum(
                        [
                            self.x[k, z]
                            for k in self.neighbors[u] if k in self.valid_units_per_zone[z]
                        ]
                    )
                    self.m.addConstr(self.x[u, z] <= any_neighbor_sum, name="Contiguity")


    # percentage of students (GE students) in the zone, that we need to add to fill all the GE seats in the zone
    def _proportional_overage_constraint(self, overage):
        # No zone has overage more than overage percentage of its population
        for z in range(self.Z):
            self.m.addConstr(
                gp.quicksum(
                    [(-self.studentsInArea[u] + self.seats[u]) * self.x[u, z]
                     for u in self.valid_units_per_zone[z]]
                )
                <=
                overage *
                gp.quicksum(
                    [self.studentsInArea[u] * self.x[u, z]
                     for u in self.valid_units_per_zone[z]]
                )
            )
    def _shortage_constraints(self, shortage=0.15, overage=0.2, all_cap_shortage=0.8):
        # self.fixed_shortage_const()
        if shortage <= 1:
            self._proportional_shortage_constraint(shortage)
        if overage <= 1:
            self._proportional_overage_constraint(overage)
        if all_cap_shortage <= 1:
            self._all_cap_proportional_shortage_constraint(all_cap_shortage)


    # Add constraints related to diversity such as: racial balance,
    # frl balance (balance in free or reduced priced lunch eligibility)
    # and aalpi balance, across all the zones.
    def _add_diversity_constraints(self, racial_dev=1, frl_dev=1, aalpi_dev=1):
        # racial balance constraint
        if racial_dev < 1:
            self._add_racial_constraint(racial_dev)

        # frl constraint
        if frl_dev < 1:
                self._add_frl_constraint(frl_dev)

        # aalpi constraint
        if aalpi_dev < 1:
            self._add_aalpi_constraint(aalpi_dev)

    def _add_color_quality_top_schools(self, topX=1):
        color_scores = self.units_data["AvgColorIndex"].fillna(value=0)
        top_schools = np.zeros([self.U])
        top = np.percentile(color_scores, 100 * (1 - self.Z / self.U) - 0.05)
        top = np.percentile(color_scores, topX)
        print(top)
        for v in range(self.U):
            if color_scores[v] > top:
                top_schools[v] = 1
        for z in range(self.Z):
            topz = gp.quicksum(
                [self.x[v, z] * top_schools[v] for v in self.valid_units_per_zone[z]]
            )
            self.m.addConstr(topz >= 0.8)

    def requested_function(self):
        district_ratio = sum(self.units_data["Ethnicity_Hispanic/Latinx"]) / float(self.N)
        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [self.units_data["Ethnicity_Hispanic/Latinx"][v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            district_students = gp.quicksum(
                [self.studentsInArea[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            self.m.addConstr(zone_sum >= (0.8 * district_ratio) * district_students)
            self.m.addConstr(zone_sum <= (1.2 * district_ratio) * district_students)