import cv2
from cvzone.HandTrackingModule import HandDetector
from cvzone.ClassificationModule import Classifier
import math
import numpy as numpy
import time

class ATS:
    def __init__(self):
        self.flag = 0
        self.cap = cv2.VideoCapture(0)
        self.handDect = HandDetector(maxHands=1)
        self.classifier = Classifier("Model/keras_model.h5","Model/labels.txt")
        self.offset = 20
        self.imageSize = 300
        self.folder = "images/Stop"
        self.counter = 0
        self.labels = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q", "R", "S"
                    "T", "U", "V", "W", "X", "Y", "STOP"]
    
    def start(self):
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
                prediction, index = self.classifier.getPrediction(img)
                print(prediction, index)
            else:
                k = self.imageSize/w 
                newHeight = int(math.ceil(k*h))
                newImgSize = cv2.resize(imgCrop, (self.imageSize, newHeight))
                hGap = int(math.ceil((self.imageSize - newHeight) / 2))
                imgWhite[hGap:hGap+newHeight, :] = newImgSize
                

            
            
            cv2.imshow("imageCrop",imgCrop)
            cv2.imshow("imageWhite", imgWhite)
            
        cv2.imshow("image", imga)
        key = cv2.waitKey(1)
        # Pressing t while start saving images


    