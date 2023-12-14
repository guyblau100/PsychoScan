import utlis
from flask import Flask, jsonify, request
import DB_Management


app = Flask(__name__)



@app.route('/userTests', methods=['GET'])
def get_user_tests():
    userEmail = request.json['email']
    testYear = request.json['test_year']
    try:
        tests = DB_Management.getUserAvailableTestsToDo(userEmail,testYear)
        return jsonify(tests)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400


@app.route('/test/getFirstQuestions', methods=['GET'])
def get_test_first_questions():
    testSeasonMonth = request.json['testSeasonMonth']
    testYear = request.json['testYear']
    questions = DB_Management.getSimulationSectionsFirstQuestions(testYear, testSeasonMonth)
    return jsonify(questions), 200

@app.route('/user/<string:userEmail>', methods=['GET'])
def get_graph_page_data(userEmail):
    try:
        data = DB_Management.getStatisticsPageData(userEmail)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400


@app.route('/createTest', methods=['POST'])
def insert_test():
    data = request.get_json()
    userEmail = data.get('email', '')
    examYear = data.get('test_year', '')
    examSeasonOrMonth = data.get('test_seasonOrMonth', '')
    orderList = data.get('order_list', [])
    encoded_image = data.get('image', '')
    try:
        orderedAnswers = utlis.MajorFunction(encoded_image,orderList)
        DB_Management.insertSimulation(userEmail, examYear, examSeasonOrMonth, orderedAnswers)
        resultJson = DB_Management.getSimulationReport(userEmail,examYear,examSeasonOrMonth)
        return jsonify(resultJson), 200
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400

@app.route('/createUser', methods=['POST'])
def create_user():
    data = request.get_json()
    userEmail = data.get('email', '')
    userName = data.get('userName', '')
    password = data.get('password', '')
    try:
         DB_Management.insertUser(userEmail,userName,password)
    except Exception as e:
        return jsonify({'error': {'code': 400, 'message': str(e)}}), 400
    else:
        return jsonify({"message": f"the user {userName} created successfully"}), 200





if __name__ == '__main__':
    app.run()























