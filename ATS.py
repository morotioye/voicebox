import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import math
import numpy as numpy


class ATS:
    def __init__(self) -> None:
        self.cap = cv2.VideoCapture(0)
        self.handDect = HandDetector(maxHands=1)
        self.classifier = Classifier("Model/keras_model.h5","Model/labels.txt")        
        self.offset = 20
        self.imageSize = 300
        self.temptHand = -1
        self.index = -1
        self.t = 0
        self.tempGesture = -1
        self.folder = "images/Please"
        self.counter = 0
        self.labels = ["hello ","bye " ,"goood ","What's your name ","my name is ","thank you ","logan ","."]
        self.message = ""

    def start(self):
        self.message = ""
        self.message_array = []
        self.t = 0
        self.temptHand = -1
        self.index = -1
        while True:
            success, imga = self.cap.read()
            hands, img = self.handDect.findHands(img= imga)
            if hands:
                hand = hands[0]
                x,y,w,h = hand ['bbox']

                imgWhite = numpy.ones((self.imageSize,self.imageSize,3), numpy.uint8) * 255

                imgCrop = img[y - self.offset:y + h + self.offset, x- self.offset:x + w+ self.offset]

                imgCropShape = imgCrop.shape

                aspectRat = h/w
                #tweak it so horizontal size is also adjusted
                if aspectRat > 1:
                    k = self.imageSize/h
                    newWidth = int(math.ceil(k*w))
                    newImgSize = cv2.resize(imgCrop, (newWidth, self.imageSize))
                    wGap = int(math.ceil((self.imageSize - newWidth) / 2))
                    imgWhite[:, wGap:wGap+newWidth] = newImgSize
                    prediction, self.index = self.classifier.getPrediction(imgWhite)
                else:
                    k = self.imageSize/w 
                    newHeight = int(math.ceil(k*h))
                    newImgSize = cv2.resize(imgCrop, (self.imageSize, newHeight))
                    hGap = int(math.ceil((self.imageSize - newHeight) / 2))
                    imgWhite[hGap:hGap+newHeight, :] = newImgSize
                    prediction, self.index = self.classifier.getPrediction(imgWhite)

                if self.tempGesture == self.index:
                    t += .3
                    if t > 2:

                        t = 0
                        if self.labels[self.index] == ".":
                            return self.message_array
                        self.message_array.append(self.labels[self.index])

                else:
                    self.tempGesture = self.index
                    t = 0
                print(t)



                cv2.imshow("imageCrop",imgCrop)
                cv2.imshow("imageWhite", imgWhite)



            cv2.imshow("image", imga)
            key = cv2.waitKey(1)
            if(key) == ord("s"):
                print("yooyo")
                return self.message
            # Pressing t while start saving images