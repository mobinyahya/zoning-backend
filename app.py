from flask import Flask, send_file, jsonify, request
from flask_cors import CORS, cross_origin
from Zone_Generation.Config.Constants import *
from filter_request import Filter_Request
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
# CORS(app)  # Global CORS configuration

zone_dict = {60750102001: 0, 60750102002: 0, 60750102003: 0, 60750109003: 0, 60750110001: 0, 60750110002: 0, 60750110003: 0, 60750111001: 0, 60750126022: 0, 60750129011: 0, 60750129012: 0, 60750129021: 0, 60750129022: 0, 60750129023: 0, 60750130001: 0, 60750130002: 0, 60750130003: 0, 60750130004: 0, 60750131011: 0,
             60750131012: 0, 60750131021: 0, 60750131022: 0, 60750132001: 0, 60750132002: 0, 60750133003: 0, 60750133005: 0, 60750134001: 0, 60750134002: 0, 60750135001: 0, 60750135002: 0, 60750152001: 0, 60750152002: 0, 60750152003: 0, 60750153001: 0, 60750153002: 0, 60750154001: 0, 60750154002: 0, 60750154003: 0,
             60750154004: 0, 60750154005: 0, 60750155001: 0, 60750155002: 0, 60750155003: 0, 60750156001: 0, 60750156002: 0, 60750156003: 0, 60750157001: 0, 60750157002: 0, 60750157003: 0, 60750157004: 0, 60750158011: 0, 60750158012: 0, 60750158013: 0, 60750158021: 0, 60750158022: 0, 60750159001: 0, 60750159002: 0,
             60750161001: 0, 60750161002: 0, 60750161003: 0, 60750161004: 0, 60750165001: 0, 60750165002: 0, 60750165003: 0, 60750165004: 0, 60750451001: 0, 60750451002: 0, 60750451003: 0, 60750101001: 1, 60750101002: 1, 60750103001: 1, 60750103002: 1, 60750103003: 1, 60750104001: 1, 60750104002: 1, 60750104003: 1,
             60750104004: 1, 60750105001: 1, 60750105002: 1, 60750106001: 1, 60750106002: 1, 60750106003: 1, 60750107001: 1, 60750107002: 1, 60750107003: 1, 60750107004: 1, 60750108001: 1, 60750108002: 1, 60750108003: 1, 60750109001: 1, 60750109002: 1, 60750111002: 1, 60750111003: 1, 60750112001: 1, 60750112002: 1,
             60750112003: 1, 60750113001: 1, 60750113002: 1, 60750117001: 1, 60750117002: 1, 60750118001: 1, 60750119011: 1, 60750119012: 1, 60750119021: 1, 60750119022: 1, 60750120001: 1, 60750120002: 1, 60750121001: 1, 60750121002: 1, 60750122011: 1, 60750122012: 1, 60750122021: 1, 60750123011: 1, 60750123012: 1,
             60750123021: 1, 60750123022: 1, 60750125012: 1, 60750125021: 1, 60750125022: 1, 60750151001: 1, 60750151002: 1, 60750611001: 1, 60750611002: 1, 60750611003: 1, 60750126011: 2, 60750126021: 2, 60750127001: 2, 60750127002: 2, 60750127003: 2, 60750128001: 2, 60750128002: 2, 60750128003: 2, 60750128004: 2,
             60750132003: 2, 60750133001: 2, 60750133002: 2, 60750133004: 2, 60750134003: 2, 60750401001: 2, 60750401002: 2, 60750401003: 2, 60750401004: 2, 60750402001: 2, 60750402002: 2, 60750402003: 2, 60750402004: 2, 60750426011: 2, 60750426012: 2, 60750426021: 2, 60750426022: 2, 60750426023: 2, 60750427001: 2,
             60750427002: 2, 60750427003: 2, 60750428001: 2, 60750428002: 2, 60750428003: 2, 60750452001: 2, 60750452002: 2, 60750452003: 2, 60750452004: 2, 60750452005: 2, 60750476001: 2, 60750476002: 2, 60750476003: 2, 60750476004: 2, 60750477011: 2, 60750477012: 2, 60750477013: 2, 60750477021: 2, 60750477022: 2,
             60750477023: 2, 60750478011: 2, 60750478012: 2, 60750478013: 2, 60750478021: 2, 60750478022: 2, 60750478023: 2, 60750479011: 2, 60750479012: 2, 60750479013: 2, 60750479014: 2, 60750479015: 2, 60750479021: 2, 60750479022: 2, 60750479023: 2, 60750601001: 2, 60759802001: 2, 60750124011: 3, 60750124012: 3,
             60750124021: 3, 60750124022: 3, 60750124023: 3, 60750160001: 3, 60750162001: 3, 60750162002: 3, 60750162003: 3, 60750163001: 3, 60750163002: 3, 60750163003: 3, 60750164001: 3, 60750164002: 3, 60750166001: 3, 60750166002: 3, 60750166003: 3, 60750166004: 3, 60750167001: 3, 60750167002: 3, 60750167003: 3,
             60750167004: 3, 60750168011: 3, 60750168012: 3, 60750168013: 3, 60750168021: 3, 60750168022: 3, 60750168023: 3, 60750169001: 3, 60750169002: 3, 60750170001: 3, 60750170002: 3, 60750170003: 3, 60750171011: 3, 60750171012: 3, 60750171013: 3, 60750171021: 3, 60750171022: 3, 60750171023: 3, 60750202001: 3,
             60750204011: 3, 60750204012: 3, 60750204013: 3, 60750301011: 3, 60750301012: 3, 60750301013: 3, 60750301014: 3, 60750301021: 3, 60750301022: 3, 60750301023: 3, 60750302011: 3, 60750302012: 3, 60750302013: 3, 60750302021: 3, 60750302022: 3, 60750302023: 3, 60750303011: 3, 60750303012: 3, 60750303013: 3,
             60750303014: 3, 60750303021: 3, 60750303022: 3, 60750303023: 3, 60750304001: 3, 60750304002: 3, 60750304003: 3, 60750305001: 3, 60750305002: 3, 60750305003: 3, 60750306001: 3, 60750306002: 3, 60750306003: 3, 60750326011: 3, 60750326012: 3, 60759803001: 3, 60750125011: 4, 60750176011: 4, 60750176012: 4,
             60750176013: 4, 60750176014: 4, 60750176015: 4, 60750177001: 4, 60750177002: 4, 60750178011: 4, 60750178012: 4, 60750178021: 4, 60750178022: 4, 60750179021: 4, 60750180001: 4, 60750180002: 4, 60750201001: 4, 60750201002: 4, 60750201003: 4, 60750201004: 4, 60750202002: 4, 60750202003: 4, 60750203001: 4,
             60750203002: 4, 60750203003: 4, 60750205001: 4, 60750205002: 4, 60750206001: 4, 60750206002: 4, 60750206003: 4, 60750206004: 4, 60750207001: 4, 60750207002: 4, 60750207003: 4, 60750208001: 4, 60750208002: 4, 60750208003: 4, 60750208004: 4, 60750226001: 4, 60750226002: 4, 60750227021: 4, 60750227022: 4,
             60750227041: 4, 60750227042: 4, 60750228011: 4, 60750228012: 4, 60750228013: 4, 60750228021: 4, 60750228022: 4, 60750228032: 4, 60750228033: 4, 60750229031: 4, 60750229032: 4, 60750607001: 4, 60750607002: 4, 60750607003: 4, 60750614001: 4, 60750614002: 4, 60750614003: 4, 60750615001: 4, 60750615002: 4,
             60750615003: 4, 60750615004: 4, 60750615005: 4, 60750615006: 4, 60750204021: 5, 60750204022: 5, 60750205003: 5, 60750209001: 5, 60750209002: 5, 60750209003: 5, 60750209004: 5, 60750210001: 5, 60750210002: 5, 60750210003: 5, 60750210004: 5, 60750211001: 5, 60750211002: 5, 60750211003: 5, 60750211004: 5,
             60750212001: 5, 60750212002: 5, 60750212003: 5, 60750213001: 5, 60750213002: 5, 60750214001: 5, 60750214002: 5, 60750214003: 5, 60750215001: 5, 60750215002: 5, 60750215003: 5, 60750215004: 5, 60750215005: 5, 60750216001: 5, 60750216002: 5, 60750217001: 5, 60750217002: 5, 60750217003: 5, 60750218001: 5,
             60750218002: 5, 60750218003: 5, 60750218004: 5, 60750228031: 5, 60750229011: 5, 60750229012: 5, 60750229013: 5, 60750229021: 5, 60750229022: 5, 60750229033: 5, 60750251001: 5, 60750251002: 5, 60750251003: 5, 60750252001: 5, 60750252002: 5, 60750252003: 5, 60750252004: 5, 60750253001: 5, 60750253002: 5,
             60750253003: 5, 60750253004: 5, 60750254011: 5, 60750254012: 5, 60750254013: 5, 60750254021: 5, 60750254022: 5, 60750254023: 5, 60750254031: 5, 60750254032: 5, 60750255001: 5, 60750311001: 5, 60750304004: 6, 60750304005: 6, 60750308001: 6, 60750308004: 6, 60750308005: 6, 60750326013: 6, 60750326021: 6,
             60750326022: 6, 60750326023: 6, 60750327001: 6, 60750327002: 6, 60750327003: 6, 60750327004: 6, 60750327005: 6, 60750327006: 6, 60750327007: 6, 60750328011: 6, 60750328012: 6, 60750328013: 6, 60750328021: 6, 60750328022: 6, 60750328023: 6, 60750329011: 6, 60750329012: 6, 60750329013: 6, 60750329014: 6,
             60750329021: 6, 60750329022: 6, 60750329023: 6, 60750330001: 6, 60750330002: 6, 60750330003: 6, 60750330004: 6, 60750330005: 6, 60750330006: 6, 60750331003: 6, 60750331004: 6, 60750351001: 6, 60750351002: 6, 60750351003: 6, 60750351004: 6, 60750351005: 6, 60750351006: 6, 60750351007: 6, 60750352011: 6,
             60750352012: 6, 60750352013: 6, 60750352014: 6, 60750352015: 6, 60750352021: 6, 60750352022: 6, 60750352023: 6, 60750353001: 6, 60750353002: 6, 60750353003: 6, 60750353004: 6, 60750353005: 6, 60750353006: 6, 60750354001: 6, 60750354002: 6, 60750354003: 6, 60750354004: 6, 60750354005: 6, 60750604001: 6,
             60750230011: 7, 60750230012: 7, 60750230013: 7, 60750230031: 7, 60750230032: 7, 60750231021: 7, 60750231022: 7, 60750231031: 7, 60750231032: 7, 60750232001: 7, 60750232002: 7, 60750232003: 7, 60750233001: 7, 60750234001: 7, 60750234002: 7, 60750256001: 7, 60750256002: 7, 60750256003: 7, 60750256004: 7,
             60750257011: 7, 60750257012: 7, 60750257013: 7, 60750257021: 7, 60750257022: 7, 60750257023: 7, 60750258001: 7, 60750258002: 7, 60750259001: 7, 60750259002: 7, 60750259003: 7, 60750260022: 7, 60750264021: 7, 60750264022: 7, 60750610001: 7, 60750612001: 7, 60750612002: 7, 60759806001: 7, 60759809001: 7,
             60750255002: 8, 60750255003: 8, 60750255004: 8, 60750255005: 8, 60750255006: 8, 60750260011: 8, 60750260012: 8, 60750260021: 8, 60750260041: 8, 60750261001: 8, 60750261004: 8, 60750307001: 8, 60750307002: 8, 60750307003: 8, 60750308002: 8, 60750308003: 8, 60750309001: 8, 60750309002: 8, 60750309003: 8,
             60750309004: 8, 60750309005: 8, 60750309006: 8, 60750309007: 8, 60750310001: 8, 60750310002: 8, 60750310003: 8, 60750311002: 8, 60750311003: 8, 60750311004: 8, 60750311005: 8, 60750312011: 8, 60750312012: 8, 60750312013: 8, 60750312014: 8, 60750312021: 8, 60750312022: 8, 60750313011: 8, 60750313012: 8,
             60750313013: 8, 60750313021: 8, 60750313022: 8, 60750313023: 8, 60750314001: 8, 60750314005: 8, 60750331001: 8, 60750331002: 8, 60750332011: 8, 60750332031: 8, 60750332032: 8, 60750332041: 8, 60750332042: 8, 60750332043: 8, 60750260031: 9, 60750260032: 9, 60750260042: 9, 60750261002: 9, 60750261003: 9,
             60750262001: 9, 60750262002: 9, 60750262003: 9, 60750262004: 9, 60750262005: 9, 60750263011: 9, 60750263012: 9, 60750263013: 9, 60750263021: 9, 60750263022: 9, 60750263023: 9, 60750263031: 9, 60750263032: 9, 60750264011: 9, 60750264012: 9, 60750264023: 9, 60750264031: 9, 60750264032: 9, 60750264041: 9,
             60750264042: 9, 60750314002: 9, 60750314003: 9, 60750314004: 9, 60750605021: 9, 60750605022: 9, 60750605023: 9, 60750610002: 9, 60759805011: 9}
racial_dict = {
    0: 100,
    1: 200,
    2: 150,
    3: 100,
    4: 200,
    5: 150,
};

@app.route('/api/generate_zones_test', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones_test():
    data = request.get_json()
    print("1: generate_zones_test  was called", data)
    return send_file('Figures/zone_partition.png', mimetype='image/png')



@app.route('/api/generate_zones_test3', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones_test3():
    data = request.get_json()
    print("3: generate_zones_test3  was called", data)
    response_data = {
        'title': 'Test Title'
    }
    return jsonify(response_data)


# expected inputs:
    # data json, with data['FRLDeviation'], data['Number_of_Zones'], data['Number_of_Zones']
# expected outputs:
#     image of the zoning map
#     data json for latex file:
#         Latex_formula: {
#             'Variables': {
#                 'A': "Definition of the new variable A, in the formula (if any new variables are defined)",
#                 'B': "Definition of the new variable B, in the formula (if any new variables are defined)",
#             },
#             'Formula': 'Theoretical Latex formula, for the constraint that was requested. '
#                        'Dont make any changes to the original formula'
#         }
@app.route('/api/generate_zones', methods=['POST', 'OPTIONS'])
@cross_origin(origin='http://localhost:3000')  # Specific CORS configuration for this route
def generate_zones_backend():
    data = request.get_json()
    print("generate_zones data", data)


    user_inputs = {}
    user_inputs["number_of_zones"] = Choice2Zones[data['choices_per_zone']]
    user_inputs["FRL_Dev"] = data['FRL_Dev']
    user_inputs["request_constraint"] = data['request_constraint']

    print("Initialized user_inputs: ", user_inputs)

    Latex_Formula = {
        'Variables': {
            'var1_u': 'Definiton of Var 111.',
            'var2_u': 'Definiton of Var 2.',

        },
        'Formula': '(1-0.24) \cdot (\sum_{u \in U} mathScore_u) / Z \leq \sum_{u \in U} mathScore_u . x_{u,z}  \leq 1 + 0.24) \cdot (\sum_{u \in U} mathScore_u)/Z   \quad  ∀ z \in Z'
    }
    response_data = {}
    response_data['Latex_Formula'] = Latex_Formula
    response_data['zone_dict'] = zone_dict
    # print("response_data format ", response_data)

    time.sleep(1)
    #
    FR = Filter_Request(user_inputs)
    FR.fetch_llm_response()
    FR.filter_zones()
    FR.solution_status["racial_dict"] = racial_dict
    # print("\n FR.solution_status: ",  FR.solution_status)



    # if "Latex_Formula" in FR.solution_status:
    #     print("\n FR.solution_status[Latex_Formula]: ",  FR.solution_status["Latex_Formula"])
    # print("\n FR.solution_status[zone_dict]: ", FR.solution_status["zone_dict"])



    # Convert the dictionary to a string representation
    # dict_str = str(FR.solution_status["Latex_Formula"]) use json.dumps() instead
    # # Replace double backslashes with single backslashes in the string representation
    # dict_str = dict_str.replace("\\\\", "\\")

    return jsonify(FR.solution_status)
    # return jsonify(response_data)
    # return send_file('Figures/zone_partition.png', mimetype='image/png')



if __name__ == '__main__':
    app.run()


