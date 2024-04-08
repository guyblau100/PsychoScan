import pyodbc
import os
import json
import utlis

class CustomError(Exception):
    def __init__(self, message="This is a custom exception"):
        self.message = message
        super().__init__(self.message)

#DB connecting stuff
server = "psycho-scan-server.database.windows.net"
database = "PSYCHO-SCAN-DB"
username = "guybl"
password = "Djokovic2021"
driver = "{ODBC Driver 18 for SQL Server}"
conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
conn = pyodbc.connect(conn_str)




#functions for self use to update the db with new official tests that will be published in the future
def readAllJsons():
    jsonsList = []
    folder_path = os.path.join(os.path.dirname(__file__), 'exams')
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                jsonsList.append(json_data)
    return jsonsList

def updateOfficialTests():
    updateAllTestsNames()
    updateAllTestsSections()
    updateAllTestsAnswers()
    updateAllTestsScores()

def updateAllTestsNames():
    dataToInsert = []
    jsons = readAllJsons()
    for testJson in jsons:
        testTuple = (testJson['year'], testJson['month/season'])
        dataToInsert.append(testTuple)

    with pyodbc.connect(conn_str) as conn, conn.cursor() as cursor:
        insert_test_name_query = "INSERT INTO official_tests (test_year,test_season_month) VALUES (?,?) "
        try:
            cursor.executemany(insert_test_name_query, dataToInsert)
        except pyodbc.IntegrityError:
            pass
        except pyodbc.Error as ex:
            sqlstate = ex.args[1]
            raise CustomError(f"Database error with SQLSTATE {sqlstate}: {str(ex)}")
        except Exception as e:
            raise CustomError(f"An unexpected error occurred: {str(e)}")
        else:
            conn.commit()

def updateAllTestsSections():
    cursor = conn.cursor()
    getTestIdQuery = "SELECT test_id FROM offical_tests where test_year = ? AND test_season_month = ?"
    jsons = readAllJsons()
    for testJson in jsons:
        dataToInsert = []
        cursor.execute(getTestIdQuery, (testJson['year'], testJson['month/season']))
        for row in cursor.fetchall():
            test_id = row[0]
        question_list = testJson["first_questions"]
        for i in range(6):
            sectionTuple = (test_id, i+1, question_list[i])
            dataToInsert.append(sectionTuple)
        insertSectionsQuery = "INSERT INTO official_sections (test_id,section_number,first_question) VALUES (?,?,?)"
        try:
            cursor.executemany(insertSectionsQuery, dataToInsert)
        except pyodbc.IntegrityError:
            pass
        except Exception as e:
            raise CustomError(e)
        else:
            conn.commit()

def updateAllTestsAnswers():
    cursor = conn.cursor()
    jsons = readAllJsons()
    for testJson in jsons:
        sectionIds = []
        dataToInsert = []
        getSectionsIdsQuery = "SELECT section_id " \
                              "FROM official_sections " \
                              "JOIN official_tests on(official_sections.test_id = official_tests.test_id) " \
                              "WHERE test_year = ? AND test_season_month = ? " \
                              "ORDER BY section_number"
        try:
            cursor.execute(getSectionsIdsQuery,(testJson['year'], testJson['month/season']))
        except Exception as e:
            raise CustomError(f"couldn't get {testJson['month/season']}{str(testJson['year'])}. {str(e)}")
        else:
            for row in cursor.fetchall():
                section_id = row[0]
                sectionIds.append(section_id)

            answers_array = testJson["answers"]
            for i in range(len(answers_array)):
                for j in range(len(answers_array[i])):
                    questionTuple = (sectionIds[i], j+1, answers_array[i][j])
                    dataToInsert.append(questionTuple)

            createQuestionQuery = "INSERT INTO official_questions (section_id,question_number,correct_answer) " \
                                  "VALUES (?,?,?)"
            try:
                cursor.executemany(createQuestionQuery, (dataToInsert))
            except pyodbc.IntegrityError:
                pass
            except Exception as e:
                raise CustomError(str(e))
            else:
                conn.commit()

def updateAllTestsScores():
    cursor = conn.cursor()
    jsons = readAllJsons()
    for testJson in jsons:
        getTestIdQuery = "select test_id from official_tests where test_year = ? and test_season_month = ?"
        cursor.execute(getTestIdQuery, (testJson['year'], testJson['month/season']))
        for row in cursor.fetchall():
            test_id = row[0]
        dataToInsert = []
        scores = testJson["scores"]
        for i in range(47):
            scoresTuple = (test_id, i, scores.get(f'{i}').get('hebrew'), scores.get(f'{i}').get('math'), scores.get(f'{i}').get('english'))
            dataToInsert.append(scoresTuple)
        insertScoresQuery = "INSERT INTO official_test_scores (test_id,raw_score,hebrew_score,math_score,english_score) VALUES(?,?,?,?,?)"
        try:
            cursor.executemany(insertScoresQuery, dataToInsert)
        except pyodbc.IntegrityError:
            pass
        except Exception as e:
            raise CustomError(f"{str(e)}")
        else:
            conn.commit()


#functions for get requests
def getUserAvailableTestsToDo(userEmail, testYear):
    testsDict = {}
    cursor = conn.cursor()
    getAllTestsQuery = "select test_season_month from official_tests where test_year = ?"
    cursor.execute(getAllTestsQuery, testYear)
    for row in cursor.fetchall():
        testsDict.update({f"{row[0]}": True})
    geAllUserTestsQuery = "select test_season_month from tests join official_tests on(official_tests.test_id = tests.official_test_id) where user_email = ? and test_year = ?"
    cursor.execute(geAllUserTestsQuery, (userEmail, testYear))
    for row in cursor.fetchall():
        testsDict[f"{row[0]}"] = False
    return testsDict

def getSimulationSectionsFirstQuestions(testYear, testSeasonOrMonth):
    cursor = conn.cursor()
    questions = []
    getQuestionQuery = "select first_question " \
                       "from official_sections " \
                       "join official_tests on(official_sections.test_id = official_tests.test_id)" \
                       "where test_year = ? and test_season_month = ? " \
                       "order by section_number"
    cursor.execute(getQuestionQuery,(testYear, testSeasonOrMonth))
    for row in cursor.fetchall():
        questions.append(row[0])
    return questions

def getStatisticsPageData(userEmail):
    cursor = conn.cursor()
    userJson = {}

    getBulletsDataQuery = "select count(test_id) as count,avg(final_score) as avg, Min(DATEDIFF(DAY, test_date, GETDATE()))+1 AS daysSince from tests where user_email = ? group by user_email"
    try:
        cursor.execute(getBulletsDataQuery,(userEmail))
    except Exception as e:
        raise CustomError(f"Internal db error. {str(e)}")
    row = cursor.fetchone()
    if row is None:
        raise CustomError(f"the user ({userEmail}) took no tests up to date.")
    userJson.update({"testCount": row.count})
    userJson.update({"avgScore": row.avg})
    userJson.update({"daysSinceLastTest": row.daysSince})

    getAllGraphsDataQuery = "SELECT test_year, test_season_month, FORMAT(test_date,'dd/MM'), final_score,hebrew_score,math_score, english_score FROM tests join official_tests on(tests.official_test_id = official_tests.test_id) where user_email = ? order by test_date"
    try:
        cursor.execute(getAllGraphsDataQuery, (userEmail))
    except Exception as e:
        raise CustomError(f"Couldn't load {userEmail} tests scores for the graphs. The reason: {str(e)}")
    else:
        tests = {}
        for row in cursor.fetchall():
            test = {}
            test.update({"testDate": row[2]})
            test.update({"finalScore": row[3]})
            semiTest = {}
            semiTest.update({"hebrewScore": row[4]})
            semiTest.update({"mathScore": row[5]})
            semiTest.update({"englishScore": row[6]})
            test.update({"semiScores":semiTest})
            tests.update({f"{row[1]} {row[0]}":test})
        userJson.update({"tests": tests})
        cursor.close()
        return userJson

def getAllUserReports(userEmail):
    try:
        cursor = conn.cursor()
        getTestsQuery = "select test_year, test_season_month, FORMAT(test_date,'dd/MM/yyyy') from tests join official_tests on(tests.official_test_id = official_tests.test_id) where user_email = ?"
        cursor.execute(getTestsQuery,(userEmail))
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        if sqlstate == '08001':
            raise CustomError("There is a problem with the db. Please try again later.")
    else:
        result = []
        for row in cursor.fetchall():
            test = {}
            test.update({"testName": f"{row[1]} {row[0]}"})
            test.update({"testDate": row[2]})
            result.append(test)
        return result
    finally:
        cursor.close()

def getSimulationReport(userEmail,test_year,test_season_month):
    reportJson = {}
    scoresDict = {}
    try:
        cursor = conn.cursor()
        getSimulationQuery = "select test_year, test_season_month, FORMAT(test_date,'dd/MM/yy'), final_score, hebrew_score, math_score, english_score from tests join official_tests on(official_tests.test_id = tests.official_test_id) where test_year = ? and test_season_month = ? and user_email = ?"
        cursor.execute(getSimulationQuery, (test_year, test_season_month, userEmail))
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        if sqlstate == '08001':
            raise CustomError("There is a problem with the db. Please try again later.")
        else:
            raise CustomError(f"Can't get {test_season_month} {test_year} simulation details. {str(ex)}")
    except Exception as e:
        raise CustomError("Unknown error occurred. " + str(e))
    else:
        rows = cursor.fetchall()
        for row in rows:
            reportJson.update(({"testDate":row[2]}))
            scoresDict.update({"final": row[3]})
            scoresDict.update({"hebrew": row[4]})
            scoresDict.update({"math": row[5]})
            scoresDict.update({"english": row[6]})

    selectErrorsQuery = "SELECT section_number,questions.question_number,answer, correct_answer " \
                        "FROM tests join sections on (tests.test_id = sections.test_id) " \
                                   "join questions on (sections.section_id = questions.section_id) " \
                                   "join official_questions on (official_questions.question_id = questions.official_question_id) " \
                                   "join official_tests on(official_tests.test_id = tests.official_test_id)"\
                        "where tests.user_email = ? and test_year = ? and test_season_month = ? and answer != correct_answer"
    try:
        cursor.execute(selectErrorsQuery,(userEmail,test_year, test_season_month))
    except pyodbc.Error as ex:
        raise CustomError(f"Can't get the wrong answer questions. {str(ex)}")
    else:
        sectionsDict = {}
        for i in range(1,7):
            sectionDict = {}
            sectionDict.update({"mistakes":[]})
            sectionsDict.update({i:sectionDict})
        for row in cursor.fetchall():
            questionDict = {}
            section_number = row[0]
            questionDict.update({"question number":row[1]})
            questionDict.update({"user mark": row[2]})
            questionDict.update({"correct answer": row[3]})
            sectionsDict[section_number]["mistakes"].append(questionDict)

        sectionsDict[1].update({"correct": f"({23 - len(sectionsDict[1]['mistakes'])}/23)"})
        sectionsDict["Hebrew 1"] = sectionsDict.pop(1)
        sectionsDict[2].update({"correct": f"({23-len(sectionsDict[2]['mistakes'])}/23)"})
        sectionsDict["Hebrew 2"] = sectionsDict.pop(2)
        sectionsDict[3].update({"correct": f"({20 - len(sectionsDict[3]['mistakes'])}/20)"})
        sectionsDict["Math 1"] = sectionsDict.pop(3)
        sectionsDict[4].update({"correct": f"({20 - len(sectionsDict[4]['mistakes'])}/20)"})
        sectionsDict["Math 2"] = sectionsDict.pop(4)
        sectionsDict[5].update({"correct": f"({22 - len(sectionsDict[5]['mistakes'])}/22)"})
        sectionsDict["English 1"] = sectionsDict.pop(5)
        sectionsDict[6].update({"correct": f"({22 - len(sectionsDict[6]['mistakes'])}/22)"})
        sectionsDict["English 2"] = sectionsDict.pop(6)

        reportJson.update({"scores":scoresDict})
        reportJson.update({"sections": sectionsDict})
        return reportJson
    finally:
        cursor.close()


#function for put requests
def insertUser(userEmail,userName,password = None):
    try:
        cursor = conn.cursor()
        insertUserQuery = "INSERT INTO users (user_email,user_name,password) VALUES (?,?,?)"
        cursor.execute(insertUserQuery, (userEmail,userName,password))
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        if sqlstate == '08001':
            raise CustomError("There is a problem with the server. Please try again later.")
        if sqlstate == '23000':
            raise CustomError(f"There is already a user match to {userEmail}")
    except Exception as e:
        raise CustomError(str("Unknown error occurred." + str(e)))
    else:
        conn.commit()
    finally:
        cursor.close()

def insertSimulation(userEmail, testYear, testSeasonOrMonth, marks):
    cursor = conn.cursor()
    sectionsIds = []
    officialQuestionsIds = []
    finaleDataToInsert = []
    rawScores = []

    getOfficialTestIdQuery = "SELECT test_id FROM official_tests where test_year = ? and test_season_month = ?"
    try:
        cursor.execute(getOfficialTestIdQuery, (testYear, testSeasonOrMonth))
    except Exception as e:
        raise CustomError(str(f"failed to get {testYear}{testSeasonOrMonth} id." + str(e)))
    else:
        for row in cursor.fetchall():
            official_test_id = row[0]
    insertTestQuery = "INSERT INTO tests (official_test_id,user_email) VALUES (?,?)"
    try:
        cursor.execute(insertTestQuery, (official_test_id,userEmail))
    except Exception as e:
        raise CustomError(f"Simulation creation failed. The user {userEmail} already has {testSeasonOrMonth}{testYear} simulation documented")
    getTestIdQuery = "SELECT test_id FROM tests where official_test_id = ? and user_email = ?"
    try:
        cursor.execute(getTestIdQuery, (official_test_id,userEmail))
    except Exception as e:
        raise CustomError(str("failed to get the new simulation id." + str(e)))
    for row in cursor.fetchall():
        test_id = row[0]
    insertSectionQuery = "INSERT INTO sections (test_id,section_number) VALUES (?,?)"
    dataToInsert = [(test_id, 1), (test_id, 2), (test_id, 3), (test_id, 4), (test_id, 5), (test_id, 6)]
    try:
        cursor.executemany(insertSectionQuery, dataToInsert)
    except Exception as e:
        raise CustomError(str("failed to update test sections." + str(e)))
    getSectionIdQuery = "SELECT section_id FROM sections where test_id = ? order by section_number"
    try:
        cursor.execute(getSectionIdQuery, test_id)
    except Exception as e:
        raise CustomError(str("failed to get the test new sections ids." + str(e)))
    for row in cursor.fetchall():
        section_id = row[0]
        sectionsIds.append(section_id)
    getOfficialQuestionIdQuery = "SELECT question_id " \
                                 "FROM official_questions " \
                                 "JOIN official_sections on(official_sections.section_id = official_questions.section_id) " \
                                 "JOIN official_tests on(official_tests.test_id = official_sections.test_id) " \
                                 "WHERE official_tests.test_id = ? " \
                                 "ORDER BY section_number,question_number"
    try:
        cursor.execute(getOfficialQuestionIdQuery, (official_test_id))
    except Exception as e:
        raise CustomError(str("failed to get official questions ids." + str(e)))
    for row in cursor.fetchall():
        official_question_id = row[0]
        officialQuestionsIds.append(official_question_id)

    for i in range(130):
        if i <= 22:
            currentSectionFirstQuestion = -1
            sectionNumber = 1
        elif i <= 45:
            currentSectionFirstQuestion = 22
            sectionNumber = 2
        elif i <= 65:
            currentSectionFirstQuestion = 45
            sectionNumber = 3
        elif i <= 85:
            currentSectionFirstQuestion = 65
            sectionNumber = 4
        elif i <= 107:
            currentSectionFirstQuestion = 85
            sectionNumber = 5
        elif i <= 129:
            currentSectionFirstQuestion = 107
            sectionNumber = 6
        tuple1 = (officialQuestionsIds[i],i-currentSectionFirstQuestion,sectionsIds[sectionNumber-1],marks[sectionNumber-1][i-currentSectionFirstQuestion-1])
        finaleDataToInsert.append(tuple1)
    insertQuestionQuery = "INSERT INTO questions (official_question_id,question_number,section_id,answer) VALUES (?,?,?,?)"
    try:
        cursor.executemany(insertQuestionQuery, finaleDataToInsert)
    except Exception as e:
        raise CustomError(str("failed to insert the user marks." + str(e)))
    getRawScoresQuery = f"EXECUTE selectRawScores @user_email ='{userEmail}', @test_id ='{test_id}'"
    try:
        cursor.execute(getRawScoresQuery)
    except Exception as e:
        raise CustomError(str("failed to calaculate the raw scores." + str(e)))
    for row in cursor.fetchall():
        rawScores.append(row[0])

    hebrewQuery = "select hebrew_score from official_test_scores where test_id = ? and raw_score = ?"
    try:
        cursor.execute(hebrewQuery,(official_test_id,rawScores[0]))
    except Exception as e:
        raise CustomError(str("failed to calaculate the hebrew score." + str(e)))
    for row in cursor.fetchall():
        hebrewScore = row[0]

    mathQuery = "select math_score from official_test_scores where test_id = ? and raw_score = ?"
    try:
        cursor.execute(mathQuery,(official_test_id,rawScores[1]))
    except Exception as e:
        raise CustomError(str("failed to calaculate the math score." + str(e)))
    for row in cursor.fetchall():
        mathScore = row[0]

    englishQuery = "select english_score from official_test_scores where test_id = ? and raw_score = ?"
    try:
        cursor.execute(englishQuery, (official_test_id, rawScores[2]))
    except Exception as e:
        raise CustomError(str("failed to calaculate the english score." + str(e)))
    for row in cursor.fetchall():
        englishScore = row[0]

    subjectsScoresAvg = (hebrewScore * 0.4 + mathScore * 0.4 + englishScore * 0.2)
    roundedAvg = round(subjectsScoresAvg)
    finalScore = utlis.finalScore(roundedAvg)

    updateScoreQuery = "update tests set final_score = ?, hebrew_score = ?,math_score = ?,english_score = ? where test_id = ? and user_email = ? "
    try:
        cursor.execute(updateScoreQuery,(finalScore,hebrewScore,mathScore,englishScore,test_id,userEmail))
    except Exception as e:
        raise CustomError(str("failed to update the test scores." + str(e)))
    conn.commit()
    cursor.close()





