import cv2
import numpy as np


def imagePrint(img,imgName):
    cv2.imwrite(f"/Users/guy/Desktop/{imgName}.jpg",img)

def circlesPrint(img,points):
    for point in points:
        cv2.circle(img, point, 15, (0, 255, 0, -1), -1)
    imagePrint(img,"Detected Corners")

def answersPrint(answers):
    for i in range(0,len(answers)):
        for q in range(len(answers[i])):
            print(f"the chosen answer for section {i+1}, question {q+1} is {answers[i][q]}")

def printMarksBinaryValues(boxes):
    answers = []
    for box in boxes:
        tableAnswers = []
        columns = np.hsplit(box, 30)
        for column in columns:
            bubbles = np.vsplit(column, 4)
            answer = calculateBinaryValues(bubbles)
            tableAnswers.append(answer)
        answers.append(tableAnswers)
    printValues(answers)


#sub functions (should be private)
def calculateBinaryValues(bubbles):
    results = []
    for bubble in bubbles:
        pixel_sum = np.sum(bubble)
        results.append(pixel_sum)
    return results

def printValues(result):
    count = 1
    for i in result:
        print(f"section {count}:")
        print("")
        count1 = 1
        for j in i:
            print(f"q{count1} is: {j}")
            print("")
            count1 += 1
        count += 1


