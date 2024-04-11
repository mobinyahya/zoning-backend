from Zone_Generation.Config.Constants import *

class Zone_Eval_Abstract(object):
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


        # It is a list of zones. i.e. self.zones[0] is a list of units assigned to zone 0
        self.zones = Area_Data.zones


    # Enforce school quality balance constraint, using "AvgColorIndex" metric, which is:
    # Average of ela_color, math_color, chronic_color, and suspension_color, where Red=1 and Blue=5
    # Make sure all zones are within score_dev percerntage deviation of average of AvgColorIndex for each zone
    def _color_quality_const(self, score_dev=-1):
        if not (1 > score_dev > -1):
            return
        color_scores = self.units_data["AvgColorIndex"].fillna(value=0)
        school_average = sum(color_scores) / sum(self.schools)

        for z in range(self.Z):
            # Total AvgColorIndex quality for zone z
            zone_quality = sum([color_scores[u] for u in self.zones[z]])
            # Number of schools in zone z
            zone_schools = sum([self.schools[u] for u in self.zones[z]])

            if zone_quality < (1 - score_dev) * school_average * zone_schools:
                return False
            if zone_quality > (1 + score_dev) * school_average * zone_schools:
                return False
        return True


    # Enforce a balance in english score over schools of different zones as follows:
    # Compute the average: average english score over all schools in the district.
    # Sum up english scores for schools of each zone. Divide the english score for each zone,
    # by total number of schools within that zone.
    # Make sure the average english score for each zone,
    # is between (1-score_dev) * average and (1+score_dev) * average
    def _school_eng_score_quality_const(self, score_dev=-1):
        if not (1 > score_dev > -1):
            return
        eng_scores = self.units_data["english_score"]
        school_average = sum(eng_scores) / sum(self.schools)

        for z in range(self.Z):
            zone_sum = sum([eng_scores[v] for v in self.zones[z]])
            # Number of schools in zone z
            zone_schools = sum([self.schools[u] for u in self.zones[z]])
            if zone_sum < (1 - score_dev) * school_average * zone_schools:
                return False
            if zone_sum > (1 + score_dev) * school_average * zone_schools:
                return False
        return True

    def _school_math_score_quality_const(self, score_dev=-1):
        if not (1 > score_dev > -1):
            return

        math_score = self.units_data["math_score"].fillna(value=0)
        school_average = sum(math_score) / sum(self.schools)

        for z in range(self.Z):
            zone_sum = sum([math_score[v] for v in self.zones[z]])
            zone_schools = sum([self.schools[v] for v in self.zones[z]])
            if zone_sum < (1 - score_dev) * school_average * zone_schools:
                return False
            if zone_sum > (1 + score_dev) * school_average * zone_schools:
                return False
        return True

    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # This following constraint makes sure all zones have almost similar number of schools.
    # First compute the average number of schools per zone,
    # by computing the total number of schools in the city and dividing it by the number of zones.
    # Next, add a constraint to make sure the number of schools in each zone
    # is within average number of schools per zone + or - 1
    def _school_count_const(self):
        avg_school_count = sum(self.schools) / self.Z + 0.0001

        # note: although we enforce max deviation of 1 from avg, in practice,
        # no two zones will have more than 1 difference in school count
        # Reason: school count is int. Observe the avg_school_count +-1,
        # if avg_school_count is not int, and see how the inequalities will look like
        # * I implemented the code this way (instead of pairwise comparison), since it is faster
        for z in range(self.Z):
            zone_schools = sum([self.schools[v] for v in self.zones[z]])
            if zone_schools < avg_school_count - 1:
                return False
            if zone_schools > avg_school_count + 1:
                return False

        # if K8 schools are included,
        # make sure no zone has more than one K8 schools
        if self.include_k8:
            for z in range(self.Z):
                zone_k8_count = sum([self.units_data["K-8"][v] for v in self.zones[z]])
                if zone_k8_count > 1:
                    return False
        return True

    def _aalpi_const(self, aalpi_dev):
        district_average = sum(self.units_data["AALPI Score"]) / self.N
        for z in range(self.Z):
            zone_sum = sum([self.units_data["AALPI Score"][v] for v in self.zones[z]])
            district_students = sum([self.studentsInArea[v] for v in self.zones[z]])

            if zone_sum >= (district_average - aalpi_dev) * district_students:
                return False
            if zone_sum <= (district_average + aalpi_dev) * district_students:
                return False
        return True

    # Make sure students of low socioeconomic status groups are fairly distributed among zones.
    # Our only metric to measure socioeconomic status, is FRL, which is the students eligibility for
    # Free or Reduced Price Lunch.
    # make sure the total FRL for students in each zone, is within an additive
    #  frl_dev% of average FRL over zones..
    def _frl_const(self, frl_dev=1):
        for z in range(self.Z):
            zone_sum = sum([self.units_data["FRL"][u] for u in self.zones[z]])
            district_students = sum([self.studentsInArea[u] for u in self.zones[z]])

            if zone_sum < (self.F - frl_dev) * district_students:
                return False
            if zone_sum > (self.F + frl_dev) * district_students:
                return False
        return True




    # Make sure students with ethnicities "Black or African American",  and students with ethnicities "Asian"
    #  are fairly distributed among zones: make sure the percentage of students in each zone, is within an additive
    #  race_dev% of percentage of total students of that race.
    def _racial_const(self, race_dev=1):
        ETHNICITY_COLS = ["Ethnicity_Black_or_African_American", "Ethnicity_Asian"]
        for race in ETHNICITY_COLS:
            race_ratio = sum(self.units_data[race]) / float(self.N)

            for z in range(self.Z):
                zone_sum = sum([self.units_data[race][v] for v in self.zones[z]])
                district_students = sum([self.studentsInArea[v] for v in self.zones[z]])
                if zone_sum < (race_ratio - race_dev) * district_students:
                    return False
                if zone_sum > (race_ratio + race_dev) * district_students:
                    return False
        return True
                


    # ---------------------------------------------------------------------------
    # ---------------------------------------------------------------------------
    # All programs proportional shortage for each zone =
    # percentage of all-program-students in the zone, that don't get any seat from all-program-capacities.
    # all-program-students =
    # (Total number of students, across all program types, in the zones)
    # all-program-capacities =
    # (Total number of seats for all programs (not just GE) in schools within the zone)
    # The following constraint makes sure no zone has an All programs proportional shortage
    # larger than the given input percentage, shorage_pct
    def _all_cap_prop_shortage_const(self, shorage_pct):
        # No zone has shortage more than all_cap_shortage percentage of its total student population
        for z in range(self.Z):
            zone_all_cap_students = sum([self.units_data["all_prog_students"][v] for v in self.zones[z]])
            zone_all_cap_seats = sum([self.units_data["all_prog_capacity"][v] for v in self.zones[z]])
            zone_all_cap_shortage =  zone_all_cap_students - zone_all_cap_seats
            if zone_all_cap_shortage > shorage_pct * zone_all_cap_students:
                return False
        return True

    # proportional shortage for each zone =
    # percentage of students (GE students) in the zone, that don't get any seat (from GE capacities)
    # students in the zone
    # The following constraint makes sure no zone has a shortage
    # larger than the given input "shortage"
    def _prop_shortage_const(self, shorage_pct):
        # No zone has shortage more than shortage percentage of its population
        for z in range(self.Z):
            zone_students =  sum([self.studentsInArea[v] for v in self.zones[z]])
            zone_seats =  sum([self.seats[v] for v in self.zones[z]])
            zone_shortage = zone_students - zone_seats
            
            if zone_shortage > shorage_pct * zone_students:
                return False
        return True

    def _absolute_shortage_const(self, shortage_count):
        # each zone has at least the shortage
        for z in range(self.Z):
            zone_students = sum([self.studentsInArea[v] for v in self.zones[z]])
            zone_seats = sum([self.seats[v] for v in self.zones[z]])
            zone_shortage = zone_students - zone_seats

            if zone_shortage > shortage_count:
                return False
        return True

    # Enforce zones to have almost the same number of students
    # Make sure the deviation in number of GE students is within dev_count of average
    def _absolute_pop_const(self, dev_count=1000):
        # average number of GE students in the zone
        pop_avg = sum(self.studentsInArea) / self.Z

        for z in range(self.Z):
            zone_students = sum([self.studentsInArea[v] for v in self.zones[z]])
            if zone_students < pop_avg - dev_count:
                return False
            if zone_students > pop_avg + dev_count:
                return False
        return True













