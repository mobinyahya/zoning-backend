import gurobipy as gp
import pandas as pd
import random, math, gc, os, csv
import numpy as np
from gurobipy import GRB
from collections import defaultdict
from Config.Constants import *

class Integer_Program_Abstract(object):
    def __init__(self, Area_Data):
        # Number of zones. We are trying to divide the city into self.Z number of zones
        self.Z = Area_Data.Z

        # self.N: Total number of GE students.
        # Computation based on units_data file: self.N = sum(self.units_data["ge_students"])
        self.N = Area_Data.N

        # self.U: Total number of units (number of distinct unit indices)
        # Computation based on units_data file: self.U = len(self.units_data.index)
        self.U = Area_Data.U

        # Variable: self.F
        # Description: Represents the average percentage of students eligible for Free or Reduced Price Lunch (FRL).
        # Computation: Calculated as the sum of the FRL percentages in `self.units_data["FRL"]` divided by total units N.
        self.F = Area_Data.F

        # whether K8 schools be considered into the calculations or not
        self.include_k8 = Area_Data.include_k8

        # Dictionary: self.studentsInArea
        # - Keys: unit v (e.g., 41)
        # - Values: Number of GE students in unit v
        # Example: self.studentsInArea[41] returns the number of GE students in unit 41
        # Computed from: self.units_data["ge_students"]
        self.studentsInArea = Area_Data.studentsInArea

        # Dictionary: self.seats
        # - Keys: unit v (e.g., 41)
        # - Values: Number of seats for GE students in unit v
        # Example: self.seats[41] returns the number of seats for GE students in unit 41
        # Computed from: self.units_data["ge_capacity"].to_numpy()
        self.seats = Area_Data.seats

        # Dictionary: self.schools
        # - Keys: unit v (e.g., 41)
        # - Values: Number of schools in unit v (usually 0 or 1)
        # Example: self.schools[41] returns the number of schools in unit 41 (usually 0 or 1)
        # Computed from: self.units_data['num_schools']
        self.schools = Area_Data.schools
        self.school_df = Area_Data.school_df

        # Each row, represent a unit.
        # Example: self.units_data['ge_students'][41] == number of GE students in unit 41.

        # DataFrame: self.units_data
        # Purpose: Central and comprehensive dataset containing metrics for units.
        # Structure:
        #     - Columns: Metrics for units (e.g., ge_capacity, ge_capacity, num_schools, seats).
        #     - Rows: Represent individual units.
        # Example: self.units_data['ge_students'][41] returns the number of GE students in unit 41.
        self.units_data = Area_Data.units_data

        self.centroids = Area_Data.centroids

        # Dictionary: self.euc_distances
        # - Keys: a pair of units (u, v)
        # - Values: Euclidean distance in miles between unit u and unit v
        # Example: self.euc_distances[41, 13] returns 3.42, indicating units 41 and 13 are 3.42 miles apart.
        self.euc_distances = Area_Data.euc_distances

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

        self.level = Area_Data.level



    def _initializs_feasiblity_constraints(self, max_distance=float('inf')):

        valid_assignments = []
        # if a max distance constraint is given, allow units to be matched only to
        # zone centroids that are closer than max_distance
        for z in range(self.Z):
            centroid_z = self.centroids[z]
            for u in range(self.U):
                if (self.euc_distances[centroid_z][u] < max_distance):
                    valid_assignments.append((u,z))


        # Initialize a dictionary to hold valid unit for each zone
        # (keys: zone z), (values: a list [], of unit that are allowed to be matched to zone z). Lists are pre-generated based on distance limitations.
        self.valid_units_per_zone = defaultdict(list)
        # Initialize a dictionary to hold valid zones for each unit
        # (keys: unit u), (values: a list [], of zone indices that unit u is  allowed to be matched to). Lists are pre-generated based on distance limitations.
        self.valid_zones_per_unit = defaultdict(list)

        # Populate the dictionary with valid zones for each unit
        for u, z in valid_assignments:
            self.valid_units_per_zone[z].append(u)
            self.valid_zones_per_unit[u].append(z)

        self.m = gp.Model("Zone model")

        # Variable self.x[u,z]: is a binary variable. It indicates
        # whether unit with index u is assigned to zone z or not.
        # Example: if self.x[41,2] == 0, it means unit with index 41 is not assigned to zone 2.
        self.x = self.m.addVars(valid_assignments, vtype=GRB.BINARY, name="x")

        # Feasiblity Constraint: every unit must  belong to exactly one zone
        self.m.addConstrs(
            (gp.quicksum(self.x[u, z] for z in self.valid_zones_per_unit[u]) == 1
             for u in range(self.U)
             ),
        )

    # This function constructs the boundary cost variables.
    # Boundary cost variables are used in the optimization model objective
    def set_y_boundary(self):
        neighboring_tuples = []
        for u in range(self.U):
            for v in self.neighbors[u]:
                if u >= v:
                    continue
                neighboring_tuples.append((u,v))

        # self.b[u, v]: a binary boundary variable. This variable will be 1,
        # if unit u, and unit v, are adjacent units, that
        # are assigned to different zones (hence, they will be part of boundary cost)
        self.b = self.m.addVars(neighboring_tuples, vtype=GRB.BINARY, name="boundary_vars")
        y_boundary = self.m.addVar(lb=0, vtype=GRB.CONTINUOUS, name="boundary distortion")
        self.m.addConstr(gp.quicksum(self.b[u, v] for u, v in neighboring_tuples) == y_boundary)
        self._add_boundary_constraint()
        return y_boundary

    def _add_boundary_constraint(self):
        # if u and v are neighbors, check if they are boundaries of different zones
        for u in range(self.U):
            for v in self.neighbors[u]:
                if u >= v:
                    continue
                for z in range(self.Z):
                    if (u in self.valid_units_per_zone[z]) and (v in self.valid_units_per_zone[z]):
                        self.m.addConstr(gp.quicksum([self.x[u, z], -1 * self.x[v, z]]) <= self.b[u, v])
                        self.m.addConstr(gp.quicksum([-1 * self.x[u, z], self.x[v, z]]) <= self.b[u, v])
                    elif (u in self.valid_units_per_zone[z]):
                        self.m.addConstr(self.x[u, z] <= self.b[u, v])
                    elif (v in self.valid_units_per_zone[z]):
                        self.m.addConstr(self.x[v, z] <= self.b[u, v])


    def _set_objective_model(self):
        y_boundary = self.set_y_boundary()
        # set the objective of the Integer Program.
        # The integer program will try to minimize the cost of boundary,
        # which will result into compact and nice looking shapes for zones.
        self.m.setObjective(y_boundary, GRB.MINIMIZE)



    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # All programs proportional shortage for each zone =
    # percentage of all-program-students in the zone, that don't get any seat from all-program-capacities.
    # all-program-students =
    # (Total number of students, across all program types, in the zones)
    # all-program-capacities =
    # (Total number of seats for all programs (not just GE) in schools within the zone)
    # The following constraint makes sure no zone has an All programs proportional shortage
    # larger than the given input, all_cap_shortage
    def _all_cap_proportional_shortage_constraint(self, all_cap_shortage):
        # No zone has shortage more than all_cap_shortage percentage of its total student population
        for z in range(self.Z):
            self.m.addConstr(
                gp.quicksum(
                    [(self.units_data["all_prog_students"][v] - self.units_data["all_prog_capacity"][v]) * self.x[v, z]
                     for v in self.valid_units_per_zone[z]]
                )
                <=
                all_cap_shortage *
                gp.quicksum(
                    [self.units_data["all_prog_students"][v] * self.x[v, z]
                     for v in self.valid_units_per_zone[z]]
                )
            )


    # proportional shortage for each zone =
    # percentage of students (GE students) in the zone, that don't get any seat (from GE capacities)
    # students in the zone
    # The following constraint makes sure no zone has a shortage
    # larger than the given input "shortage"
    def _proportional_shortage_constraint(self, shortage):
        # No zone has shortage more than shortage percentage of its population
        for z in range(self.Z):
            self.m.addConstr(
                (1 - shortage) *
                gp.quicksum(
                    [self.studentsInArea[v] * self.x[v, z]
                     for v in self.valid_units_per_zone[z]]
                )
                <=
                gp.quicksum(
                    [self.seats[v] * self.x[v, z]
                     for v in self.valid_units_per_zone[z]]
                )
            )

    def _absolute_shortage_const(self, shortage):
        # each zone has at least the shortage
        for z in range(self.Z):
            self.m.addConstr(
                gp.quicksum(
                    [(self.studentsInArea[u] - self.seats[u]) * self.x[u, z]
                     for u in self.valid_units_per_zone[z]]
                )
                <= shortage)


    # Enforce zones to have almost the same number of students
    # Make sure the difference between total population of GE students
    # among two different zone is at most _balance.
    def _absolute_population_constraint(self, _balance=1000):
        # add number of students balance constraint
        for z in range(self.Z):
            firstZone = gp.quicksum(
                [self.studentsInArea[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            for q in range(z + 1, self.Z):
                secondZone = gp.quicksum(
                    [self.studentsInArea[v] * self.x[v, q] for v in self.valid_units_per_zone[z]]
                )
                self.m.addConstr(firstZone - secondZone <= _balance)
                self.m.addConstr(firstZone - secondZone >= -_balance)


    # Enforce zones to have almost the same number of students
    # Make sure the average population of each zone, is within a given
    # population_dev% of average population over zones
    def _proportional_population_constraint(self, population_dev=1):
        average_population = sum(self.units_data["all_prog_students"])/self.Z
        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [self.units_data["all_prog_students"][v] * self.x[v, z] for v in self.valid_units_per_zone[z]])

            self.m.addConstr(zone_sum >= (1 - population_dev) * average_population, name= "Population LB")
            self.m.addConstr(zone_sum <= (1 + population_dev) * average_population, name= "Population UB")


    # Make sure students of racial groups are fairly distributed among zones.
    # For specific racial minority, make sure the percentage of students in each zone, is within an additive
    #  race_dev% of percentage of total students of that race.
    def _add_racial_constraint(self, race_dev=1):
        for race in ETHNICITY_COLS:
            race_ratio = sum(self.units_data[race]) / float(self.N)

            for z in range(self.Z):
                zone_sum = gp.quicksum(
                    [self.units_data[race][v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
                )
                district_students = gp.quicksum(
                    [self.studentsInArea[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
                )
                self.m.addConstr(zone_sum >= (race_ratio - race_dev) * district_students, name= str(race) + " LB")
                self.m.addConstr(zone_sum <= (race_ratio + race_dev) * district_students, name= str(race) + " UB")


    # Make sure students of low socioeconomic status groups are fairly distributed among zones.
    # Our only metric to measure socioeconomic status, is FRL, which is the students eligibility for
    # Free or Reduced Price Lunch.
    # make sure the total FRL for students in each zone, is within an additive
    #  frl_dev% of average FRL over zones..
    def _add_frl_constraint(self, frl_dev=1):
        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [self.units_data["FRL"][v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            district_students = gp.quicksum(
                [self.studentsInArea[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            self.m.addConstr(zone_sum >= (self.F - frl_dev) * district_students, name="FRL LB")
            self.m.addConstr(zone_sum <= (self.F + frl_dev) * district_students, name="FRL UB")




    def _add_aalpi_constraint(self, aalpi_dev):
        print("units_data.columns", self.units_data.columns)
        district_average = sum(self.units_data["AALPI Score"]) / self.N
        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [self.units_data["AALPI Score"][v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )

            district_students = gp.quicksum(
                [self.studentsInArea[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )

            self.m.addConstr(zone_sum >= (district_average - aalpi_dev) * district_students, name="AALPI LB")
            self.m.addConstr(zone_sum <= (district_average  + aalpi_dev) * district_students, name="AALPI UB")


    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # This following constraint makes sure all zones have almost similar number of schools.
    # First compute the average number of schools per zone,
    # by computing the total number of schools in the city and dividing it by the number of zones.
    # Next, add a constraint to make sure the number of schools in each zone
    # is within average number of schools per zone + or - 1
    def _add_school_count_constraint(self):
        zone_school_count = {}
        avg_school_count = sum([self.schools[v] for v in range(self.U)]) / self.Z + 0.0001
        print("avg_school_count", avg_school_count)

        # note: although we enforce max deviation of 1 from avg, in practice,
        # no two zones will have more than 1 difference in school count
        # Reason: school count is int. Observe the avg_school_count +-1,
        # if avg_school_count is not int, and see how the inequalities will look like
        # * I implemented the code this way (instead of pairwise comparison), since it is faster
        for z in range(self.Z):
            zone_school_count[z] = gp.quicksum([self.schools[v] * self.x[v, z] for v in self.valid_units_per_zone[z]])
            self.m.addConstr(zone_school_count[z] <= avg_school_count + 1)
            self.m.addConstr(zone_school_count[z] >= avg_school_count - 1)

        # if K8 schools are included,
        # make sure no zone has more than one K8 schools
        if self.include_k8:
            zone_k8_count = {}
            for z in range(self.Z):
                zone_k8_count[z] = gp.quicksum([self.units_data["K-8"][v] * self.x[v, z]
                                                for v in self.valid_units_per_zone[z]])
                self.m.addConstr(zone_k8_count[z] <= 1)


    # Enforce a balance in english score over schools of different zones as follows:
    # Compute the average: average english score over all schools in the district.
    # Sum up english scores for schools of each zone. Divide the english score for each zone,
    # by total number of schools within that zone.
    # Make sure the average english score for each zone,
    # is between (1-score_dev) * average and (1+score_dev) * average
    def _add_school_eng_score_quality_constraint(self, score_dev=-1):
        if not (1 > score_dev > -1):
            return
        eng_scores = self.units_data["english_score"].fillna(value=0)
        school_average = sum(eng_scores) / sum(self.schools)

        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [eng_scores[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            zone_schools = gp.quicksum(
                [self.schools[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            self.m.addConstr(zone_sum >= (1 - score_dev) * school_average * zone_schools)
            self.m.addConstr(zone_sum <= (1 + score_dev) * school_average * zone_schools)

    def _add_school_math_score_quality_constraint(self, score_dev=-1):
        if not (1 > score_dev > -1):
            return

        math_scores = self.units_data["math_score"].fillna(value=0)
        school_average = sum(math_scores) / sum(self.schools)

        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [math_scores[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            zone_schools = gp.quicksum(
                [self.schools[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )

            self.m.addConstr(zone_sum >= (1 - score_dev) * school_average * zone_schools)
            self.m.addConstr(zone_sum <= (1 + score_dev) * school_average * zone_schools)



    # Enforce school quality balance constraint, using "AvgColorIndex" metric, which is:
    # Average of ela_color, math_color, chronic_color, and suspension_color, where Red=1 and Blue=5
    # Make sure all zones are within min_pct and max_pct of average of AvgColorIndex for each zone
    # min_pct: min percentage. max_pct: max percentage
    def _add_color_quality_constraint(self, score_dev=-1, topX=0):
        if not (1 > score_dev > -1):
            return
        color_scores = self.units_data["AvgColorIndex"].fillna(value=0)
        school_average = sum(color_scores) / sum(self.schools)

        for z in range(self.Z):
            zone_sum = gp.quicksum(
                [color_scores[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )
            zone_schools = gp.quicksum(
                [self.schools[v] * self.x[v, z] for v in self.valid_units_per_zone[z]]
            )

            self.m.addConstr(zone_sum >= (1 - score_dev) * school_average * zone_schools)
            self.m.addConstr(zone_sum <= (1 + score_dev) * school_average * zone_schools)
