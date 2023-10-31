import cv2
import numpy as np


def imagePrint(img,imgName):
    cv2.imshow(imgName,img)
    cv2.waitKey()

def circlesDrawing(img,points):
    for point in points:
        cv2.circle(img, point, 15, (0, 255, 0, -1), -1)
    imagePrint(img,"Detected Corners")

def printBoxes(boxes):
    question = 23
    for i in range(len(boxes)):
        cv2.imwrite(f" table number {i+1}.jpg", boxes[i])
        if i == 4:
            lenth = boxes[i].shape[1]
            cut = boxes[i][:,int(lenth/30 * (question-1)):int(lenth/30 * question)]
            cv2.imwrite(f"section {i+1} question {question} .jpg", cut)

def answersPrint(answers):
    for i in range(0,len(answers)):
        for k in range(0,23):
            print(f"the chosen answer for section {i+1}, question {k+1} is {answers[i][k]}")

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