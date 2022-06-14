######
# Author : Siyeop Yoon
# Last Update : May 26, 2022
# https://cardiacmr.hms.harvard.edu/
######


import numpy
import pydicom
import pydicom._storage_sopclass_uids
import os
import numpy as np
import glob
import scipy.ndimage


import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp,QMenuBar, QShortcut,QButtonGroup, QRadioButton, QPushButton, QComboBox
from PyQt5.QtWidgets import QFileDialog, QVBoxLayout,QHBoxLayout,QWidget,QSlider,QLabel
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence

from PyQt5.QtCore import Qt
from PIL import Image
import qimage2ndarray
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import cv2




class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title= "LineDrawer"
        top=400
        left=400
        width=1536
        height=1024


        self.setWindowTitle(self.title)
        self.setGeometry(top,left,width,height)


        self.ButtonLayout = QHBoxLayout()
        self.ButtonLayout.setAlignment(Qt.AlignCenter)
        self.SlideLayout = QHBoxLayout()
        self.SlideLayout.setAlignment(Qt.AlignCenter)

        self.RadioLayout = QHBoxLayout()
        self.RadioLayout.setAlignment(Qt.AlignCenter)

        self.RadioViews = QVBoxLayout()
        self.RadioViews.setAlignment(Qt.AlignCenter)

        self.RadioSlices = QVBoxLayout()
        self.RadioSlices.setAlignment(Qt.AlignCenter)


        self.RadioPhases = QVBoxLayout()
        self.RadioPhases.setAlignment(Qt.AlignCenter)

        self.ComboLinesBOX = QVBoxLayout()
        self.ComboLinesBOX.setAlignment(Qt.AlignCenter)


        self.RadioLayout.addLayout(self.RadioViews)
        self.RadioLayout.addLayout(self.RadioSlices)
        self.RadioLayout.addLayout(self.RadioPhases)
        self.RadioLayout.addLayout(self.ComboLinesBOX)

        self.ImagesLayout = QHBoxLayout()
        self.ImagesLayout.setAlignment(Qt.AlignCenter)

        self.PageLayout = QVBoxLayout()

        self.PageLayout.addLayout(self.ButtonLayout)
        self.PageLayout.addLayout(self.RadioLayout)

        self.PageLayout.addLayout(self.SlideLayout)
        self.PageLayout.addLayout(self.ImagesLayout)

        self.shortcut_center = QShortcut(QKeySequence('`'), self)
        self.shortcut_line1 = QShortcut(QKeySequence('1'), self)
        self.shortcut_line2 = QShortcut(QKeySequence('2'), self)
        self.shortcut_line3 = QShortcut(QKeySequence('3'), self)
        self.shortcut_line4 = QShortcut(QKeySequence('q'), self)
        self.shortcut_line5 = QShortcut(QKeySequence('w'), self)
        self.shortcut_line6 = QShortcut(QKeySequence('e'), self)

        self.widget = QWidget()
        self.widget.setLayout(self.PageLayout)



        self.setCentralWidget(self.widget)

        self.ViewMode = 0
        self.SliceMode = 0
        self.PhaseMode = 0

        self.drawingMode = 0
        self.isButtonPressed = False
        self.center_selected = False

        self.line_selected=[False,False,False,False,False,False]
        self.line_ColorSet=[(0,0,255),(0,255,0),(255,0,0),(0,255,255),(255,0,255),(255,255,0)]

        self.currentLocation = (0, 0)

        self.ptCenter=(0,0)

        self.segPoints=[[(0,0),(0,0)],[(0,0),(0,0)],[(0,0),(0,0)],[(0,0),(0,0)],[(0,0),(0,0)],[(0,0),(0,0)]]


        self.button = QPushButton ("Load Dicoms",self)
        self.button2 = QPushButton("Save Segments", self)
        self.button3 = QPushButton("Save X-t line", self)

        self.ViewName=['SAX','2ch','4ch']
        self.radioSAX=QRadioButton("SAX ",self)
        self.radio2ch=QRadioButton("2ch ",self)
        self.radio4ch=QRadioButton("4ch ",self)

        self.SliceName = ['Basal', 'Mid', 'Apical']
        self.radioBasal = QRadioButton("Basal ", self)
        self.radioMid = QRadioButton("Mid ", self)
        self.radioApical = QRadioButton("Apical", self)

        self.PhaseName = ['EndDiastole', 'EndSystole']
        self.radioEndDiastole = QRadioButton("EndDiastole", self)
        self.radioEndSystole = QRadioButton("EndSystole ", self)

        self.LineName = ['Center','1st', '2nd', '3rd', '4th', '5th', '6th']
        self.comboLines=QComboBox(self)
        self.comboLines.addItems(self.LineName)




        self.sliceSlider = QSlider(self)
        self.phaseSlider = QSlider(self)
        self.labelslice = QLabel("slice: "+'0', self)
        self.labelslice.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labelslice.setMinimumWidth(80)

        self.labelphase = QLabel("phase: "+'0', self)
        self.labelphase.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labelphase.setMinimumWidth(80)


        self.exitAction=QAction('Exit', self)
        self.menubar = QMenuBar()
        self.filemenu = self.menubar.addMenu('&File')

        self.dispay_dim = (800, 800)

        self.maxCardiacPhase=1
        self.maxSlices = 1

        self.image_view1 = QLabel(self)
        self.image_view1.mousePressEvent = self.getPos_pressed
        self.image_view1.mouseMoveEvent = self.getPos_moved
        self.image_view1.mouseReleaseEvent = self.getPos_released
        self.initUI()

    def initUI(self):

        self.ButtonLayout.addWidget(self.button)
        self.ButtonLayout.addWidget(self.button2)
        self.ButtonLayout.addWidget(self.button3)

        self.button.clicked.connect(self.getFolder)
        self.button2.clicked.connect(self.SaveResult_segments)
        self.button3.clicked.connect(self.SaveResult_xtprofile)

        self.btngroupViews = QButtonGroup()
        self.btngroupViews.addButton(self.radioSAX)
        self.btngroupViews.addButton(self.radio2ch)
        self.btngroupViews.addButton(self.radio4ch)

        self.RadioViews.addWidget(self.radioSAX)
        self.RadioViews.addWidget(self.radio2ch)
        self.RadioViews.addWidget(self.radio4ch)

        self.radioSAX.toggled.connect(self.updateViewMode)
        self.radio2ch.toggled.connect(self.updateViewMode)
        self.radio4ch.toggled.connect(self.updateViewMode)

        self.btngroupSlices = QButtonGroup()
        self.btngroupSlices.addButton(self.radioBasal)
        self.btngroupSlices.addButton(self.radioMid)
        self.btngroupSlices.addButton(self.radioApical)

        self.RadioSlices.addWidget(self.radioBasal)
        self.RadioSlices.addWidget(self.radioMid)
        self.RadioSlices.addWidget(self.radioApical)

        self.radioBasal.toggled.connect(self.updateSliceMode)
        self.radioMid.toggled.connect(self.updateSliceMode)
        self.radioApical.toggled.connect(self.updateSliceMode)


        self.btngroupPhases = QButtonGroup()
        self.btngroupPhases.addButton(self.radioEndDiastole)
        self.btngroupPhases.addButton(self.radioEndSystole)

        self.RadioPhases.addWidget(self.radioEndDiastole)
        self.RadioPhases.addWidget(self.radioEndSystole)
        self.radioEndDiastole.toggled.connect(self.updatePhaseMode)
        self.radioEndSystole.toggled.connect(self.updatePhaseMode)


        self.ComboLinesBOX.addWidget(self.comboLines)
        self.comboLines.currentIndexChanged.connect(self.updateLineSelection)

        self.sliceSlider.setOrientation(QtCore.Qt.Horizontal)
        self.sliceSlider.setTickInterval(1)
        self.sliceSlider.setTickPosition(QSlider.TicksBelow)
        self.phaseSlider.setOrientation(QtCore.Qt.Horizontal)
        self.phaseSlider.setTickInterval(1)
        self.phaseSlider.setTickPosition(QSlider.TicksBelow)

        self.phaseSlider.valueChanged.connect(self.updateCurrentFigure)
        self.sliceSlider.valueChanged.connect(self.updateCurrentFigure)
        self.SlideLayout.addWidget(self.sliceSlider)
        self.SlideLayout.addWidget(self.labelslice)
        self.SlideLayout.addWidget(self.phaseSlider)
        self.SlideLayout.addWidget(self.labelphase)

        self.ImagesLayout.addWidget(self.image_view1)

        self.shortcut_center.activated.connect(self.ModeSelection_center)
        self.shortcut_line1.activated.connect(self.ModeSelection_line1)
        self.shortcut_line2.activated.connect(self.ModeSelection_line2)
        self.shortcut_line3.activated.connect(self.ModeSelection_line3)
        self.shortcut_line4.activated.connect(self.ModeSelection_line4)
        self.shortcut_line5.activated.connect(self.ModeSelection_line5)
        self.shortcut_line6.activated.connect(self.ModeSelection_line6)

        self.sliceSlider.valueChanged.connect(self.updateLabels)
        self.phaseSlider.valueChanged.connect(self.updateLabels)

        self.exitAction.triggered.connect(qApp.quit)

        self.setMenuBar(self.menubar)
        self.menubar.setNativeMenuBar(True)

        self.filemenu.addAction(self.exitAction)

        img1 = Image.new('RGB', self.dispay_dim, color=(0, 0, 0))
        img1 = np.array(img1)
        img1 = qimage2ndarray.array2qimage(img1)

        self.image_view1.setBackgroundRole(QPalette.Dark)
        self.image_view1.setPixmap(QPixmap.fromImage(img1))

        self.ImageResize=4

    lineId=0

    def updateViewMode(self):
        viewstr=self.btngroupViews.checkedButton().text().lower()

        if 'sax' in viewstr:
            self.ViewMode=0
        elif '2ch' in viewstr:
            self.ViewMode=1
        elif '4ch' in viewstr:
            self.ViewMode=2

    def updateSliceMode(self):
        slicestr = self.btngroupSlices.checkedButton().text().lower()
        if 'ba' in slicestr:
            self.SliceMode=0
        elif 'mid' in slicestr:
            self.SliceMode=1
        elif 'ap' in slicestr:
            self.SliceMode=2

    def updatePhaseMode(self):
        phasestr = self.btngroupPhases.checkedButton().text().lower()
        if 'dia' in phasestr:
            self.PhaseMode = 0
        elif 'sys' in phasestr:
            self.PhaseMode = 1

    def updateLineSelection(self):
        linestr = self.comboLines.currentText()
        if 'Center' in linestr:
            self.ModeSelection_center()
        elif '1st' in linestr:
            self.ModeSelection_line1()
        elif '2nd' in linestr:
            self.ModeSelection_line2()
        elif '3rd' in linestr:
            self.ModeSelection_line3()
        elif '4th' in linestr:
            self.ModeSelection_line4()
        elif '5th' in linestr:
            self.ModeSelection_line5()
        elif '6th' in linestr:
            self.ModeSelection_line6()


    def updateLabels(self):
        self.labelslice.setText("slice: "+str(self.sliceSlider.value()))
        self.labelphase.setText("phase: "+str(self.phaseSlider.value()))

    def getPos_pressed(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.isButtonPressed=True



        if self.drawingMode == 0:
            self.ptCenter=(x,y)
            self.center_selected=True
        else:
            segId=self.drawingMode-1
            self.segPoints[segId][0]=(x, y)
            self.line_selected[segId]=True



        self.updateCurrentFigure()


    def getPos_moved(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if self.drawingMode == 0:
            self.ptCenter = (x, y)
        else:
            segId = self.drawingMode - 1
            self.segPoints[segId][1] = (x, y)

        self.updateCurrentFigure()

    def getPos_released(self, event):
        x = event.pos().x()
        y = event.pos().y()
        self.isButtonPressed = False

        if self.drawingMode == 0:
            self.ptCenter = (x, y)
        else:
            segId = self.drawingMode - 1
            self.segPoints[segId][1] = (x, y)

        self.updateCurrentFigure()


    def getFolder(self):
        self.InFolder = str(QFileDialog.getExistingDirectory(self, "In Patient Directory"))
        self.caseID = os.path.basename(self.InFolder)
        if len(self.InFolder)>0:

            self.maxCardiacPhase=1
            self.maxSlices=1
            self.ndImage = [self.ReadFiles(self.InFolder)]
            self.updateSliderLimit()
            self.updateDisplaceDim()
            self.updateCurrentFigure()

    def updateSliderLimit(self):
        self.phaseSlider.setMaximum(self.maxCardiacPhase-1)
        self.sliceSlider.setMaximum(self.maxSlices-1)

    def updateDisplaceDim(self):
        self.dispay_dim=(self.ndImage[0].shape[-2],self.ndImage[0].shape[-1])

    def ReadFiles(self,InFolder):

        print ("loading "+ InFolder)
        LRs = glob.glob(InFolder + "/*.dcm")
        Spatiotemporal_LR = []


        for i in range(len(LRs)):
            pathLR = LRs[i]

            dicom_LR = pydicom.dcmread(pathLR)
            Spatiotemporal_LR.append(dicom_LR)

            if self.maxCardiacPhase<dicom_LR.CardiacNumberOfImages:
                self.maxCardiacPhase=dicom_LR.CardiacNumberOfImages

        self.maxSlices=len(LRs)//self.maxCardiacPhase

        Spatiotemporal_LR = sorted(Spatiotemporal_LR,key=lambda s: s.TriggerTime)
        Spatiotemporal_LR = sorted(Spatiotemporal_LR,key=lambda s: s.SliceLocation)
        Spatiotemporal_4D=[]

        for islc in range(len(LRs)// self.maxCardiacPhase):
            Spatiotemporal = []

            for iphase in range( self.maxCardiacPhase):
                idx=iphase+islc*self.maxCardiacPhase
                img_LR = Spatiotemporal_LR[idx].pixel_array.astype(np.float32)
                slice=self.PercentileRescaler(img_LR)
                Spatiotemporal.append(slice)

            Spatiotemporal_4D.append(Spatiotemporal)

        print("complete load " + InFolder)
        return np.array(Spatiotemporal_4D)

    def updateCurrentFigure(self):

        img1 = 255 * np.array(self.ndImage[0][self.sliceSlider.value(), self.phaseSlider.value(), :, :])
        img1 = cv2.resize(img1, dsize=(img1.shape[1] * self.ImageResize, img1.shape[0] * self.ImageResize), interpolation=cv2.INTER_CUBIC)
        img1 = cv2.cvtColor(img1, cv2.COLOR_GRAY2RGB)

        if self.center_selected:
            cv2.circle(img1, self.ptCenter, 4, (127, 255, 127), 2)

        for lineIdx in range(6):
            if self.line_selected[lineIdx]:
                cv2.line(img1, self.segPoints[lineIdx][0], self.segPoints[lineIdx][1], self.line_ColorSet[lineIdx], 2)

        img1 = qimage2ndarray.array2qimage(img1)
        self.image_view1.setBackgroundRole(QPalette.Dark)
        self.image_view1.setPixmap(QPixmap.fromImage(img1))

    def PercentileRescaler(self,Arr):
        minval = np.percentile(Arr, 0, axis=None, out=None, overwrite_input=False, interpolation='linear',
                               keepdims=False)
        maxval = np.percentile(Arr, 100, axis=None, out=None, overwrite_input=False, interpolation='linear',
                               keepdims=False)

        Arr = (Arr - minval) / (maxval - minval)
        Arr = np.clip(Arr, 0.0, 1.0)
        return Arr

    def ModeSelection_center(self):
        self.drawingMode=0
        self.center_selected = False
        self.comboLines.setCurrentIndex(0)

    def ModeSelection_line1(self):
        self.drawingMode=1
        self.line_selected[self.drawingMode-1] = False
        self.comboLines.setCurrentIndex(1)

    def ModeSelection_line2(self):
        self.drawingMode=2
        self.line_selected[self.drawingMode-1] = False
        self.comboLines.setCurrentIndex(2)


    def ModeSelection_line3(self):
        self.drawingMode=3
        self.line_selected[self.drawingMode-1] = False
        self.comboLines.setCurrentIndex(3)

    def ModeSelection_line4(self):
        self.drawingMode=4
        self.line_selected[self.drawingMode-1] = False
        self.comboLines.setCurrentIndex(4)

    def ModeSelection_line5(self):
        self.drawingMode=5
        self.line_selected[self.drawingMode-1] = False

        self.comboLines.setCurrentIndex(5)

    def ModeSelection_line6(self):
        self.drawingMode=6
        self.line_selected[self.drawingMode-1] = False
        self.comboLines.setCurrentIndex(6)



    def SaveResult_segments(self):

        PairedProfile =[]
        PairedGrad = []
        for setID in range(len(self.ndImage)):

            num = 50

            dist=[0,0,0,0,0,0]
            Profile = [None, None, None, None, None, None]
            grad=numpy.zeros(shape=6, dtype=object)
            minGrad = numpy.zeros(shape=6, dtype=object)
            minGradIdx = [0, 0, 0, 0, 0, 0]
            for lineIdx in range(6):

                dist2ctr1 = np.linalg.norm(np.array(self.segPoints[lineIdx][0])-np.array(self.ptCenter))
                dist2ctr2 = np.linalg.norm(np.array(self.segPoints[lineIdx][1])-np.array(self.ptCenter))
                dist[lineIdx] = (np.linalg.norm(np.array(self.segPoints[lineIdx][1]) - np.array(self.segPoints[lineIdx][0])))/float(self.ImageResize)

                if dist2ctr1>dist2ctr2:
                    startpt=self.segPoints[lineIdx][1]
                    endpt=self.segPoints[lineIdx][0]
                else:
                    startpt=self.segPoints[lineIdx][0]
                    endpt=self.segPoints[lineIdx][1]

                x = np.linspace(startpt[0] / self.ImageResize, endpt[0] / self.ImageResize, num)
                y = np.linspace(startpt[1] / self.ImageResize, endpt[1] / self.ImageResize, num)


                Profile[lineIdx] = scipy.ndimage.map_coordinates(
                    np.transpose(self.ndImage[setID][self.sliceSlider.value(),self.phaseSlider.value(),:,:]),
                                                    np.vstack((x, y)))  # THIS SEEMS TO WORK CORRECTLY

                grad[lineIdx] = np.gradient(Profile[lineIdx]) * float(num) / (dist[lineIdx])
                minGradIdx[lineIdx] = np.argmin(grad[lineIdx])
                minGrad[lineIdx] = grad[lineIdx][minGradIdx[lineIdx]]

            fig, axes = plt.subplots(nrows=2, ncols=3)

            PairedProfile.append(Profile)
            PairedGrad.append(grad)
            axes[0, 0].plot(Profile[0], 'b')
            axes[0, 0].plot(grad[0], 'r')
            axes[0, 0].plot(minGradIdx[0],minGrad[0], 'go')

            axes[0, 1].plot(Profile[1], 'b')
            axes[0, 1].plot(grad[1], 'r')
            axes[0, 1].plot(minGradIdx[1],minGrad[1], 'go')

            axes[0, 2].plot(Profile[2], 'b')
            axes[0, 2].plot(grad[2], 'r')
            axes[0, 2].plot(minGradIdx[2],minGrad[2], 'go')

            axes[1, 0].plot(Profile[3], 'b')
            axes[1, 0].plot(grad[3], 'r')
            axes[1, 0].plot(minGradIdx[3], minGrad[3], 'go')

            axes[1, 1].plot(Profile[4], 'b')
            axes[1, 1].plot(grad[4], 'r')
            axes[1, 1].plot(minGradIdx[4], minGrad[4], 'go')

            axes[1, 2].plot(Profile[5], 'b')
            axes[1, 2].plot(grad[5], 'r')
            axes[1, 2].plot(minGradIdx[5], minGrad[5], 'go')

            FigureName = "Figure_" + self.caseID +"_"+ self.ViewName[self.ViewMode] + '_' + self.SliceName[
                self.SliceMode] + '_' + self.PhaseName[self.PhaseMode]
            fig.savefig(FigureName+'.png')

            logline = self.caseID  + ' '  + self.ViewName[self.ViewMode] + ' ' + self.SliceName[
                self.SliceMode] + ' ' + self.PhaseName[self.PhaseMode] + ' ' + \
                      str(abs(minGrad[0])) + ' ' + str(abs(minGrad[1])) + ' ' + str(abs(minGrad[2])) + ' ' + str(
                abs(minGrad[3])) + ' ' + str(abs(minGrad[4])) + ' ' + str(abs(minGrad[5])) + '\n'

            AllogFile = open('ImageSharpness.txt', "a")
            AllogFile.write(logline)
            AllogFile.close()

            for co in range(0, 6):
                FileName = "Profile_" +self.caseID + "_"+ self.ViewName[self.ViewMode] + '_' + self.SliceName[
                    self.SliceMode] + '_' + self.PhaseName[self.PhaseMode] + str(co+1) + '.txt'
                np.savetxt(FileName, Profile[co])




    def SaveResult_xtprofile(self):
        img1 = np.array(self.ndImage[0][self.sliceSlider.value(), :, self.ptCenter[1] // 4, :])
        FileName = "X-t plot_" + self.caseID + "_"+self.ViewName[self.ViewMode] + '_' + self.SliceName[
            self.SliceMode] + '_' + self.PhaseName[self.PhaseMode]
        plt.imsave( FileName+ '.png', img1, cmap='gray')




if __name__ == '__main__':

    app = QApplication(sys.argv)  # QApplication eats argv in constructor
    window = MainWindow()
    window.setWindowTitle('Viewer Project')
    window.show()
    sys.exit(app.exec_())








