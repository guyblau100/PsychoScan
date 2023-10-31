import cv2
import utlis
import debuging

#User Inputs:
src = cv2.imread("/Users/guy/Desktop/summer2020.JPG")
exam = "2020summer"
orderList = [0,2,1,5,3,7]



ogCopy = src.copy()

#Applying the fillters
binaryImg = utlis.preProccesing(ogCopy)

#Finding the boxes corners points
points1, points2 = utlis.cornersDetaction(binaryImg)
points1 = utlis.redundantPointsRemove(points1)
points2 = utlis.redundantPointsRemove(points2)
points = utlis.cornersSort(points1,points2)

#Applaying the prespective trnsform (view from above) for each table
boxes = utlis.wrapPrespective(src,points)

#Converting the boxes to binary image
threshBoxes = utlis.boxesThreshold(boxes)
adjustedBoxes = utlis.adjustBoxes(threshBoxes)

#Creating the answers array (list of 8 chapters, each contains list of answrers with values: 1,2,3,4)
answers = utlis.answersDetaction(adjustedBoxes)
orderedAnswers = utlis.answersReorder(answers,orderList)

hebrew,math,english, avg, errors = utlis.calculateAVG(orderedAnswers,exam,orderList)
finalScore = utlis.finalScore(avg)
utlis.printReport(hebrew,math,english, finalScore, errors)



debuging.imagePrint(src,"Original")
debuging.imagePrint(binaryImg,"PreProcesss")
debuging.circlesDrawing(ogCopy,points)
debuging.printBoxes(adjustedBoxes)
debuging.answersPrint(answers)
#debuging.printMarksBinaryValues(adjustedBoxes)





















