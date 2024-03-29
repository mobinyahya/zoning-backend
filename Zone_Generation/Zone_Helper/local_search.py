import csv
from Zone_Generation.Zone_Helper.zone_vizualization import *
from Zone_Generation.Config.Constants import *

def load_zones_from_file(file_path):
    zone_lists = []
    with open(file_path, 'r', newline='') as file:
        print("file_path ", file_path)
        csv_reader = csv.reader(file, delimiter='\t')
        for row in csv_reader:
            # Convert each element in the row to an integer and store it in the list
            zone_row = []
            for cell in row:
                # Split the cell content by commas, convert to integers, and append to the row
                cell_values = [int(val.strip()) for val in cell.split(',') if val.strip()]  #
                zone_row.extend(cell_values)
            zone_lists.append(zone_row)

    # build a zone dictionary based on zone_list
    zone_dict = {}
    for index, sublist in enumerate(zone_lists):
        for item in sublist:
            zone_dict[item] = index

    return zone_lists, zone_dict

def strong_contiguity_analysis(dz, zone_dict, mode = "evaluation"):
    # every centroid belongs to its own zone
    for z in range(dz.Z):
        level_z = dz.idx2area[dz.centroids[z]]
        if level_z in zone_dict:
            if zone_dict[level_z] != z:
                # print("for z : ", z, "  centroid location is: ", level_z,
                #       " which is assigned to zone :  ", zone_dict[level_z])
                if mode == "trimming":
                    zone_dict.pop(level_z)
                return False, zone_dict

        # in evaluation mode, all centroid blockgroups must be assigned to a blocl.
        # but in trimming mode, these blockgroups can be missing from our zone_dict
        elif mode == "evaluation":
            print("z.idx2area[dz.centroids[" + str(z) + "]] should already be in zone_dict, Error")
            print(level_z)
            return False, None


    for u in range(dz.U):
        area_u = dz.idx2area[u]
        if u in dz.centroids:
            continue
        count = 0
        if area_u in zone_dict:
            c = dz.centroids[zone_dict[area_u]]
            closer_neighbors = dz.closer_euc_neighbors[u, c]
            # closer_neighbors = dz.closer_geodesic_neighbors[j, c]

            if len(closer_neighbors) >= 1:
                for neighbor_idx in closer_neighbors:
                    if dz.idx2area[neighbor_idx] in zone_dict:
                        if zone_dict[dz.idx2area[neighbor_idx]] == zone_dict[area_u]:
                            count += 1

            if count == 0:
                if mode == "trimming":
                    if len(closer_neighbors) >= 1:
                        # print("dropping blockgroup " + str(level_j) + " that was matched to zone " +str(zone_dict[level_j]))
                        zone_dict.pop(area_u)
                elif mode == "evaluation":
                    if len(closer_neighbors) >= 1:
                        # print("moving to an undesired direction for blockgroup " + str(level_j))
                        return False, zone_dict

        elif mode == "evaluation":
            print("Error. Missing area from zone_dict: " + str(area_u))
            return False, zone_dict

    return True, zone_dict


def trim_noncontiguity(dz, zone_dict):
    while True:
        prev_size = len(zone_dict)
        isContiguous, zone_dict = strong_contiguity_analysis(dz, zone_dict, mode="trimming")
        if prev_size == len(zone_dict):
            break
    return zone_dict
def aa2bg_Zoning(dz, aa_zd):
    blockgroup_zoning = {}
    # For the given attendance area level zoning, find it's equivalent assignment on blockgroup level.
    for bg in dz.area2idx:
        if bg in dz.bg2att:
            if dz.bg2att[bg] in aa_zd:
                blockgroup_zoning[bg] = aa_zd[dz.bg2att[bg]]
            else:
                print("BG ", bg, " is in AA ", dz.bg2att[bg], " which is not included in aa zoning")


    for bg in dz.area2idx:
        neighbor_count = {}
        # look over all neighbors that are assigned to a zone so far
        for neighbor in dz.neighbors[dz.area2idx[bg]]:
            if dz.idx2area[neighbor] in blockgroup_zoning:
                # count how many neighbors of this blockgroup are from each different zone
                if blockgroup_zoning[dz.idx2area[neighbor]] in neighbor_count:
                    temp = neighbor_count[blockgroup_zoning[dz.idx2area[neighbor]]]
                    neighbor_count[blockgroup_zoning[dz.idx2area[neighbor]]] = temp + 1
                else:
                    neighbor_count[blockgroup_zoning[dz.idx2area[neighbor]]] = 1



        # some blockgroups might have been missed in bg2att dict
        # (One of the reasons: this block might not have any students --> is not included in the data, that we compute bg2att based on)
        # if all neighbors of this blockgroup are in the same zone
        # assign this blockgroup to the same zone (even if based on bg2att, we had a different outcome)
        if (bg in dz.bg2att):
            if len(neighbor_count) == 1:
                # make sure this blockgroup is not the centroid
                if bg not in [dz.idx2area[dz.centroids[z]] for z in range(dz.Z)]:
                    # select the first key in neighbor_count (we have made sure neighbor_count has only 1 key,
                    # which is the zone #of all neighbors of this blockgroup)
                    blockgroup_zoning[bg] = list(neighbor_count.keys())[0]



    # if evaluate_contiguity(dz, blockgroup_zoning) == False:
    #     print("Pre-initalization is not strongly contiguis. We smooth the boundaries further, so that we get a strongly contiguis zone assignment in blockgroup level")
    # if evaluate_contiguity(dz, blockgroup_zoning) == True:
    #     print("strong contiguity test is satisfied")
    return blockgroup_zoning



def load_initial_assignemt(dz, name, path, load_level='attendance_area'):
    if load_level == "attendance_area":
        aa_zl, aa_zd = load_zones_from_file(path + name + "_AA.csv")

        aa_zv = ZoneVisualizer('attendance_area')
        # aa_zv.visualize_zones_from_dict(aa_zoning, centroid_location=dz.centroid_location, save_name= name + "_AA")
        aa_zv.zones_from_dict(aa_zd, centroid_location=dz.centroid_location)
        # dz.distance_and_neighbors_telemetry(centroid_choices)

        dz.zone_dict = aa2bg_Zoning(dz, aa_zd)

def drop_boundary(dz, zone_dict):
    sketchy_boundary = []
    for u in range(dz.U):
        area = dz.idx2area[u]
        if area in zone_dict:
            neighbors = dz.neighbors[u]
            if len(neighbors) >= 1:
                seperated_neighbors = 0
                for neighbor_idx in neighbors:
                    if dz.idx2area[neighbor_idx] in zone_dict:
                        if zone_dict[dz.idx2area[neighbor_idx]] != zone_dict[area]:
                            seperated_neighbors += 1
                if seperated_neighbors >= len(neighbors)/5:
                    sketchy_boundary.append(area)

    for area in sketchy_boundary:
        zone_dict.pop(area, None)

    return zone_dict


def initialize_preassigned_units(dz, zone_dict):
    for u in range(dz.U):
        for z in range(dz.Z):
            if u not in dz.valid_units_per_zone[z]:
                print("Error Potential: Unit ", u, " is not supposed to be assigned to zone ", z)
                continue
            bg_u = dz.idx2area[u]
            if bg_u in zone_dict:
                if zone_dict[bg_u] == z:
                    dz.m.addConstr(dz.x[u, z] == 1)
                else:
                    dz.m.addConstr(dz.x[u, z] == 0)