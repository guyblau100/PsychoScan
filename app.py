import utlis
from flask import Flask, jsonify, request
import DB_Management


app = Flask(__name__)

@app.route("/health", methods=['GET'])
def home():
    return jsonify("OK")




@app.route('/getUserAvailableTests', methods=['GET'])
def get_user_tests():
    userEmail = request.json['user_email']
    testYear = request.json['test_year']
    try:
        tests = DB_Management.getUserAvailableTestsToDo(userEmail,testYear)
        return jsonify(tests)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400


@app.route('/getTestFirstQuestions', methods=['GET'])
def get_test_first_questions():
    testSeasonMonth = request.json['test_season_or_month']
    testYear = request.json['test_year']
    questions = DB_Management.getSimulationSectionsFirstQuestions(testYear, testSeasonMonth)
    return jsonify(questions), 200


@app.route('/getUserGraphs', methods=['GET'])
def get_graph_page_data():
    userEmail = request.json['user_email']
    try:
        data = DB_Management.getStatisticsPageData(userEmail)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400


@app.route('/getUserTests', methods=['GET'])
def get_test_report():
    userEmail = request.json['user_email']
    examYear = request.json['test_year']
    examSeasonOrMonth = request.json['test_season_or_month']
    try:
        resultJson = DB_Management.getSimulationReport(userEmail, examYear, examSeasonOrMonth)
        return jsonify(resultJson)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400



@app.route('/insertNewTest', methods=['POST'])
def insert_test():
    userEmail = request.json['user_email']
    examYear = request.json['test_year']
    examSeasonOrMonth = request.json['test_season_or_month']
    orderList = request.json['order_list']
    encoded_image = request.json['image']
    try:
        orderedAnswers = utlis.MajorFunction(encoded_image,orderList)
        DB_Management.insertSimulation(userEmail, examYear, examSeasonOrMonth, orderedAnswers)
        resultJson = DB_Management.getSimulationReport(userEmail,examYear,examSeasonOrMonth)
        return jsonify(resultJson)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400






@app.route('/insertNewUser', methods=['POST'])
def create_user():
    userEmail = request.json['user_email']
    userName = request.json['user_name']
    password = request.json['password']
    try:
        DB_Management.insertUser(userEmail, userName, password)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400
    else:
        return jsonify({"message": f"the user {userName} created successfully"}), 200



if __name__ == '__main__':
    app.run()
























