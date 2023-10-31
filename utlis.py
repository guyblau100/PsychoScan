import cv2
import numpy as np
import json
import math


def preProccesing(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    imgThresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 91, 10)
    return imgThresh

def cornersDetaction(canny):
    contourCounter = 0
    points1 = []
    points2 = []
    contours, _ = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 700000:
            epsilon = 0.001 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            for point in approx:
                x, y = point[0]
                if contourCounter == 0:
                    points1.append((x, y))
                elif contourCounter == 1:
                    points2.append((x, y))
            contourCounter += 1
    if contourCounter != 2:
        raise Exception(f"the number of big contours detacted is {contourCounter}")
    return points1 , points2

#order all corners to be ready for the wrap function(quartet)
def cornersSort(lst1,lst2):
    lst1 = sorted(lst1, key=lambda point: (point[1]))          #sort by the points' y cordinate
    lst2 = sorted(lst2, key=lambda point: (point[1]))
    lst1 = couplesSort(lst1)                                   #sort every couple of points by their x cordinate
    lst2 = couplesSort(lst2)
    if lst1[0][0] < lst2[0][0]:
        points = np.concatenate((lst1, lst2))
    else:
        points = np.concatenate((lst2, lst1))
    points[31][0] -= 15                                         #adjusment of problematic points
    points[1][0] -= 15
    points[19][0] -= 15
    points[21][0] -= 15
    return points

def couplesSort(lst):
    for i in range(0,len(lst)-1,2):
        if lst[i][0] > lst[i + 1][0]:
            lst[i], lst[i+1] = lst[i+1], lst[i]
    return lst

def redundantPointsRemove(points):
    filtered_points = []
    removed_points = set()
    for i in range(len(points)):
        if i not in removed_points:
            x1, y1 = points[i]
            keep_point = True
            for j in range(len(points)):
                if i != j and j not in removed_points:
                    x2, y2 = points[j]
                    distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                    if distance < 50:
                        keep_point = False
                        removed_points.add(i)
                        break
            if keep_point:
                filtered_points.append((x1, y1))
    return filtered_points

def wrapPrespective(src,points):
    boxes = []
    for k in range(0, len(points) - 1, 4):
        pt_A = points[k]
        pt_B = points[k + 1]
        pt_C = points[k + 2]
        pt_D = points[k + 3]
        width_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
        width_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
        maxWidth = max(int(width_AB), int(width_CD))
        height_AC = np.sqrt(((pt_A[0] - pt_C[0]) ** 2) + ((pt_A[1] - pt_C[1]) ** 2))
        height_BD = np.sqrt(((pt_B[0] - pt_D[0]) ** 2) + ((pt_B[1] - pt_D[1]) ** 2))
        maxHeight = max(int(height_AC), int(height_BD))
        input_pts = np.float32([pt_A, pt_B, pt_C, pt_D])
        output_pts = np.float32([[0, 0], [maxWidth - 1, 0], [0, maxHeight - 1], [maxWidth - 1, maxHeight - 1]])
        M = cv2.getPerspectiveTransform(input_pts, output_pts)
        out = cv2.warpPerspective(src, M, (maxWidth, maxHeight), flags=cv2.INTER_LINEAR)
        boxes.append(out)
    return boxes

def boxesThreshold(boxes):
    i = 0
    for box in boxes:
        box = cv2.cvtColor(box, cv2.COLOR_BGR2GRAY)
        box = cv2.GaussianBlur(box, (9, 9), 1)
        box = cv2.adaptiveThreshold(box, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 71, 5)
        kernel = np.ones((3, 3), np.uint8)
        box = cv2.morphologyEx(box, cv2.MORPH_CLOSE, kernel, iterations=5)
        boxes[i] = box
        i += 1
    return boxes

def adjustBoxes(boxes):
    adjustedBoxes = []
    for box in boxes:
        height, width = box.shape
        cropedBox = box[:int(height-(height % 5)),:]
        cropedBox = cropedBox[int(cropedBox.shape[0] / 5):, :]
        if width % 30 < 15:
            cropedBox = cropedBox[:, :int(width -(width % 30))]
        else:
            black_left_strip = np.zeros((cropedBox.shape[0], 30 - (width % 30)),dtype=int)
            cropedBox = np.concatenate((cropedBox, black_left_strip),axis=1)

        cropedBox[:int(cropedBox.shape[0] * 0.04), :] = 255
        cropedBox[int(cropedBox.shape[0] * 0.98):, :] = 255
        adjustedBoxes.append(cropedBox)
    return adjustedBoxes

def answersDetaction(boxes):
    allAnswers = []
    for box in boxes:
        thisSectionAnswers = []
        columns = np.hsplit(box, 30)
        for column in columns:
            bubbles = np.vsplit(column, 4)
            answer = markDetact(bubbles)
            thisSectionAnswers.append(answer)
        allAnswers.append(thisSectionAnswers)
    return allAnswers

def markDetact(bubbles):
    count = 0
    sum = 0
    smallest = float('inf')
    secondSmallest = float('inf') -1
    min_index = -1
    for bubble in bubbles:
        pixel_sum = np.sum(bubble)
        sum += pixel_sum
        if pixel_sum <= smallest:
            secondSmallest = smallest
            smallest = pixel_sum
            min_index = count
        elif pixel_sum < secondSmallest:
            secondSmallest = pixel_sum
        count += 1
    if 0.1 > ((sum/4) - (smallest))/(sum/4):                               #No answer was marked
        min_index = -1
    elif 0.1 > (secondSmallest - smallest)/(sum/4):                        #More than one answer was marked
        min_index = -1
    return min_index+1

def answersReorder(answers,orderlist):
    copy = answers.copy()
    for i in range(0,6):
        copy[i] = answers[orderlist[i]]
    return copy

def calculateAVG(answers,exam,orderlist):
    errors = []
    mathCorrect = 0
    englishCorrect = 0
    hebrewCorrect = 0
    questionCount = 0
    jsonFile = open(f"exams/{exam}.json")
    officalAnswers = json.load(jsonFile)
    for chapterCount in range(0,6):
        for question in officalAnswers["answers"][chapterCount]:
            if question == answers[chapterCount][questionCount]:
                if chapterCount < 2:
                    hebrewCorrect += 1
                elif chapterCount < 4:
                    mathCorrect += 1
                else:
                    englishCorrect += 1
            else:
                errors.append((orderlist[chapterCount],questionCount+1,answers[chapterCount][questionCount],question))
            questionCount += 1
        chapterCount += 1
        questionCount = 0
    errors = sorted(errors, key= lambda x: (x[0],x[1]))
    hebrewGrade = officalAnswers["scores"][str(hebrewCorrect)]["hebrew"]
    mathGrade = officalAnswers["scores"][str(mathCorrect)]["math"]
    englishGrade = officalAnswers["scores"][str(englishCorrect)]["english"]
    sectionsWightedAvg = (hebrewGrade * 0.4 +mathGrade * 0.4 + englishGrade * 0.2)
    roundedAvg = round(sectionsWightedAvg)
    return hebrewGrade,mathGrade,englishGrade,roundedAvg,errors

def finalScore(avg):
    lowBound, highBound = 0,0
    lowGrade, highGrade= 0,0
    if avg == 150:
        return 800
    elif avg >= 146:
        lowBound,highBound = 146,149
        lowGrade , highGrade = 762,795
    elif avg >= 141:
        lowBound,highBound = 141,145
        lowGrade , highGrade = 730,761
    elif avg >= 136:
        lowBound,highBound = 136,140
        lowGrade , highGrade = 702,729
    elif avg >= 131:
        lowBound,highBound = 131,135
        lowGrade , highGrade = 673,701
    elif avg >= 126:
        lowBound,highBound = 126,130
        lowGrade , highGrade = 645,672
    elif avg >= 121:
        lowBound,highBound = 121,125
        lowGrade , highGrade = 617,644
    elif avg >= 116:
        lowBound,highBound = 116,120
        lowGrade , highGrade = 588,616
    elif avg >= 111:
        lowBound,highBound = 111,115
        lowGrade , highGrade = 560,587
    elif avg >= 106:
        lowBound,highBound = 106,110
        lowGrade , highGrade = 532,559
    elif avg >= 101:
        lowBound,highBound = 101,105
        lowGrade , highGrade = 504,531
    elif avg >= 96:
        lowBound,highBound = 96,100
        lowGrade , highGrade = 475,503
    elif avg >= 91:
        lowBound,highBound = 91,95
        lowGrade , highGrade = 447,474
    elif avg >= 86:
        lowBound,highBound = 86,90
        lowGrade , highGrade = 419,446
    elif avg >= 81:
        lowBound,highBound = 81,85
        lowGrade , highGrade = 390,418
    elif avg >= 76:
        lowBound,highBound = 76,80
        lowGrade , highGrade = 362,389
    elif avg >= 71:
        lowBound,highBound = 71,75
        lowGrade , highGrade = 334,361
    elif avg >= 66:
        lowBound,highBound = 66,70
        lowGrade , highGrade = 305,333
    elif avg >= 61:
        lowBound,highBound = 61,65
        lowGrade , highGrade = 277,304
    elif avg >= 56:
        lowBound,highBound = 56,60
        lowGrade , highGrade = 249,276
    elif avg >= 51:
        lowBound,highBound = 51,55
        lowGrade , highGrade = 221,248
    if avg == 50:
        return 200

    precantage = (avg-lowBound)/(highBound-lowBound)
    finalScore = lowGrade + (highGrade-lowGrade)* precantage
    finalScore = round(finalScore)
    return finalScore

def printReport(hebrew,math,english,finalScore,errorsList):
    print("\x1B[4m" + "Errors Description:" + "\x1B[0m")
    for i in range(len(errorsList)):
        print(f"section {errorsList[i][0]+1} question {errorsList[i][1]} (chosen: {errorsList[i][2]}, correct: {errorsList[i][3]})")
    print("")
    print("\x1B[4m" + "Test Scores:" + "\x1B[0m")
    print(f"Hebrew: {hebrew}")
    print(f"Math: {math}")
    print(f"English: {english}")
    print("")
    print("Final Score:" + "\x1B[1m" + str(finalScore) + "\x1B[1m")









