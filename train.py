import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import math
import numpy as numpy
import time

'''
Hey guys [1] -
How are you? [2] -
Thank you, [3] - 
this is [4] -
Ready to get started? [5] -
very cool. [6] -
No [7] - 
not yet, [8] -
could you [9] 
please [10] - 
help me? [11] -
Darren, [12] -
Moroti [13] - 
and [14] - 
thank you [15]
voicebox. [16]
send [17]
'''

cap = cv2.VideoCapture(0)
handDect = HandDetector(maxHands=1)
classifier = Classifier("/Users/wnr/test/Model/keras_model.h5","/Users/wnr/test/Model/labels.txt")
offset = 20
imageSize = 300
folder = "images/15"
counter = 0
labels = ["YES", "PLEASE"]

#fix the error where it crashes if the hand gets too close
while True:
    success, imga = cap.read()
    hands, img = handDect.findHands(img= imga)
    if hands:
        hand = hands[0]
        x,y,w,h = hand ['bbox']

        imgWhite = numpy.ones((imageSize,imageSize,3), numpy.uint8) * 255

        imgCrop = img[y - offset:y + h + offset, x- offset:x + w+ offset]

        imgCropShape = imgCrop.shape

        aspectRat = h/w
        #tweak it so horizontal size is also adjusted
        if aspectRat > 1:
            k = imageSize/h
            newWidth = int(math.ceil(k*w))
            newImgSize = cv2.resize(imgCrop, (newWidth, imageSize))
            wGap = int(math.ceil((imageSize - newWidth) / 2))
            imgWhite[:, wGap:wGap+newWidth] = newImgSize
            prediction, index = classifier.getPrediction(imgWhite)
            print(prediction, index)
        else:
            k = imageSize/w 
            newHeight = int(math.ceil(k*h))
            newImgSize = cv2.resize(imgCrop, (imageSize, newHeight))
            hGap = int(math.ceil((imageSize - newHeight) / 2))
            imgWhite[hGap:hGap+newHeight, :] = newImgSize
            prediction, index = classifier.getPrediction(imgWhite)
            print(prediction, index)



        cv2.imshow("imageCrop",imgCrop)
        cv2.imshow("imageWhite", imgWhite)



    cv2.imshow("image", imga)
    key = cv2.waitKey(1)
    if(key) == ord("s"):
        cv2.imwrite(f'{folder}/image{time.time()}.jpg',imgWhite)
        counter += 1
        print(counter)
    # Pressing t while start saving images