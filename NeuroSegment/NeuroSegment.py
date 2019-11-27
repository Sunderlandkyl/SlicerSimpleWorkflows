import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from slicer.util import VTKObservationMixin

#
# NeuroSegment
#

class NeuroSegment(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  # Setting attributes
  currentDirectoryAttribute = "NeuroSeg/CurrentDirectory"
  subjectNameParameter = "subjectName"
  sessionNameParameter = "SessionName"

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "NeuroSegment"
    self.parent.categories = ["Examples"]
    self.parent.dependencies = ["Data"]
    self.parent.contributors = ["Kyle Sunderland (Perk Lab, Queen's University)"]
    self.parent.helpText = """
This is a module that organizes a workflow for brain segmentation.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Kyle Sunderland (Perk Lab, Queen's University), and was partially funded by Brigham and Women’s Hospital through NIH grant R01MH112748
"""
    if not slicer.app.commandOptions().noMainWindow :
      slicer.app.connect("startupCompleted()", self.initializeModule)

  def initializeModule(self):
    widget = slicer.modules.neurosegment.widgetRepresentation().self()
    qt.QTimer.singleShot(1, widget.showLoadSessionDialog)

    moduleWidget = slicer.modules.neurosegment.widgetRepresentation().self()

    loadSessionIcon = qt.QIcon(moduleWidget.resourcePath('Icons/LoadSession.png'))
    self.loadSessionAction = slicer.util.mainWindow().findChild("QToolBar").addAction("")
    self.loadSessionAction.setIcon(loadSessionIcon)
    self.loadSessionAction.triggered.connect(moduleWidget.showLoadSessionDialog)

    saveSessionIcon = qt.QIcon(moduleWidget.resourcePath('Icons/SaveSession.png'))
    self.saveSessionAction = slicer.util.mainWindow().findChild("QToolBar").addAction("")
    self.saveSessionAction.setIcon(saveSessionIcon)
    self.saveSessionAction.triggered.connect(moduleWidget.showSaveSessionDialog)

class LoadSessionDialog(qt.QDialog):
  def __init__(self, parent):
    qt.QDialog.__init__(self, parent)
    self.setWindowTitle("Load session")

    layout = qt.QVBoxLayout()
    self.setLayout(layout)

    moduleWidget = slicer.modules.neurosegment.widgetRepresentation().self()
    uiWidget = slicer.util.loadUI(moduleWidget.resourcePath('UI/LoadSessionWidget.ui'))
    layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    settings = qt.QSettings()
    self.ui.directoryButton.directory = settings.value(NeuroSegment.currentDirectoryAttribute, slicer.mrmlScene.GetRootDirectory())

    # Connections
    self.ui.directoryButton.directoryChanged.connect(self.onDirectoryChanged)
    self.ui.loadButton.clicked.connect(self.loadSelectedSession)
    self.ui.treeWidget.itemSelectionChanged.connect(self.onTreeSelectionChanged)

    self.onDirectoryChanged()

  def onDirectoryChanged(self):
    path = self.ui.directoryButton.directory
    directory = qt.QDir(path)

    self.ui.treeWidget.clear()
    subjectInfoList = directory.entryInfoList(qt.QDir.Dirs | qt.QDir.NoDotAndDotDot)

    settings = qt.QSettings()
    settings.setValue(NeuroSegment.currentDirectoryAttribute, path)

    for subjectInfo in subjectInfoList:
      subjectName = subjectInfo.fileName()
      subjectItem = qt.QTreeWidgetItem();
      subjectItem.setData(0, qt.Qt.UserRole, subjectName)
      subjectItem.setData(0, qt.Qt.UserRole, subjectName)
      subjectItem.setText(0, subjectName)
      subjectItem.setText(2, subjectInfo.lastModified().toString())
      self.ui.treeWidget.addTopLevelItem(subjectItem)

      subjectPath = self.ui.directoryButton.directory + "/" + subjectInfo.fileName()
      subjectDir = qt.QDir(subjectPath)
      sessionInfoList = subjectDir.entryInfoList(qt.QDir.Dirs | qt.QDir.NoDotAndDotDot)
      for sessionInfo in sessionInfoList:
        sessionName = sessionInfo.fileName()
        scenePath = subjectPath + "/" + sessionName + "/scene.mrml"
        if not os.access(scenePath, os.F_OK):
          continue

        sessionItem = qt.QTreeWidgetItem();
        sessionItem.setData(0, qt.Qt.UserRole, subjectName)
        sessionItem.setData(0, qt.Qt.UserRole + 1, sessionName)
        sessionItem.setText(1, sessionName)
        sessionItem.setText(2, sessionInfo.lastModified().toString())
        subjectItem.addChild(sessionItem)

  def onTreeSelectionChanged(self):
    selectedItems = self.ui.treeWidget.selectedItems()
    sessionName = None
    if len(selectedItems) > 0:
      selectedItem = selectedItems[0]
      sessionName = selectedItem.data(0, qt.Qt.UserRole + 1)
    self.ui.loadButton.enabled = not sessionName is None

  def loadSelectedSession(self):
    selectedItems = self.ui.treeWidget.selectedItems()
    if len(selectedItems) > 0:
      selectedItem = selectedItems[0]
      subjectName = selectedItem.data(0, qt.Qt.UserRole)
      sessionName = selectedItem.data(0, qt.Qt.UserRole + 1)

    if subjectName == "" or sessionName == "":
      return

    moduleLogic = slicer.modules.neurosegment.widgetRepresentation().self().logic
    if moduleLogic.loadSession(self.ui.directoryButton.directory, subjectName, sessionName):
      self.close()
    else:
      slicer.util.errorDisplay("Error loading session!")

class SaveSessionDialog(qt.QDialog):
  def __init__(self, parent):
    qt.QDialog.__init__(self, parent)
    self.setWindowTitle("Save session")

    layout = qt.QVBoxLayout()
    self.setLayout(layout)

    moduleWidget = slicer.modules.neurosegment.widgetRepresentation().self()
    uiWidget = slicer.util.loadUI(moduleWidget.resourcePath('UI/SaveSessionWidget.ui'))
    layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    settings = qt.QSettings()
    self.ui.directoryButton.directory = settings.value(NeuroSegment.currentDirectoryAttribute, slicer.app.defaultScenePath)

    widget = slicer.modules.neurosegment.widgetRepresentation().self()
    logic = widget.logic
    parameterNode = logic.getParameterNode()
    if parameterNode:
      subjectName = parameterNode.GetParameter(NeuroSegment.subjectNameParameter)
      if subjectName is not None:
        self.ui.subjectNameEdit.text = subjectName
      sessionName = parameterNode.GetParameter(NeuroSegment.sessionNameParameter)
      if sessionName is not None:
        self.ui.sessionNameEdit.text = sessionName

    # Connections
    self.ui.saveButton.clicked.connect(self.saveCurrentSession)
    self.ui.subjectNameEdit.textChanged.connect(self.onSubjectSessionNameChanged)
    self.onSubjectSessionNameChanged()

  def onSubjectSessionNameChanged(self):
    subjectName = self.ui.subjectNameEdit.text
    sessionName = self.ui.sessionNameEdit.text
    self.ui.saveButton.enabled = subjectName != "" and sessionName != ""

  def progressCallback(progressDialog, progressLabel, progressValue):
    progressDialog.labelText = progressLabel
    slicer.app.processEvents()
    progressDialog.setValue(progressValue)
    slicer.app.processEvents()
    return progressDialog.wasCanceled

  def saveCurrentSession(self):
    subjectName = self.ui.subjectNameEdit.text
    if subjectName == "":
      return
    sessionName = self.ui.sessionNameEdit.text
    if sessionName == "":
      return

    sessionDirectory = self.ui.directoryButton.directory + "/" + subjectName + "/" + sessionName + "/scene.mrml"
    if os.access(sessionDirectory, os.F_OK) and not slicer.util.confirmOkCancelDisplay("Session already exists! Do you want to overwrite?"):
      return

    progressDialog = slicer.util.createProgressDialog(parent=self, value=0, maximum=100)
    progressCallbackFunction = lambda progressLabel, progressValue, progressDialog=progressDialog: SaveSessionDialog.progressCallback(progressDialog, progressLabel, progressValue)

    qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
    moduleLogic = slicer.modules.neurosegment.widgetRepresentation().self().logic
    success = moduleLogic.saveSession(self.ui.directoryButton.directory, subjectName, sessionName, progressCallbackFunction)
    qt.QApplication.restoreOverrideCursor()

    if success:
      self.close()
      slicer.util.infoDisplay("Saving successful!")
    else:
      slicer.util.errorDisplay("Error saving session!")

#
# Regular QWidget do not emit a signal when closed
# Need to subclass to emit a signal on closeEvent
#
class UndockedViewWidget(qt.QSplitter):

  closed = qt.Signal()
  def closeEvent(self, event):
    self.closed.emit()
    event.accept()

#
# NeuroSegmentWidget
#

class NeuroSegmentWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  NEURO_SEGMENT_WIDGET_LAYOUT_ID = 5612

  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)

  def showLoadSessionDialog(self):
    loadSessionDialog = LoadSessionDialog(slicer.util.mainWindow())
    loadSessionDialog.deleteLater()
    loadSessionDialog.exec_()

  def showSaveSessionDialog(self):
     saveSessionDialog = SaveSessionDialog(slicer.util.mainWindow())
     saveSessionDialog.deleteLater()
     saveSessionDialog.exec_()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = NeuroSegmentLogic()

    uiWidget = slicer.util.loadUI(self.resourcePath('UI/NeuroSegment.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)
    self.ui.segmentEditorWidget.connect("masterVolumeNodeChanged (vtkMRMLVolumeNode *)", self.onMasterVolumeNodeChanged)
    self.ui.undockSliceViewButton.connect('clicked()', self.toggleSliceViews)
    self.ui.infoExpandableWidget.setVisible(False)

    self.segmentationNodeComboBox = self.ui.segmentEditorWidget.findChild(
      slicer.qMRMLNodeComboBox, "SegmentationNodeComboBox")
    self.segmentationNodeComboBox.nodeAddedByUser.connect(self.onNodeAddedByUser)

    self.selectSegmentEditorParameterNode()
    uiWidget.setMRMLScene(slicer.mrmlScene)

    self.mainViewWidget3DButton = qt.QPushButton("3D")
    self.mainViewWidget3DButton.setCheckable(True)
    self.mainViewWidget3DButton.connect('clicked()', self.updateMainView)

    self.mainSliceViewName = "Main"
    self.main3DViewName = "ViewM"
    self.secondarySliceViewNames = ["Red2", "Green2", "Yellow2"]
    self.allSliceViewNames = [self.mainSliceViewName] + self. secondarySliceViewNames

    self.sliceViewWidget = None
    self.setupLayout()

    layoutManager = slicer.app.layoutManager()
    layoutManager.connect('layoutChanged(int)', self.onLayoutChanged)
    self.previousLayout = layoutManager.layout
    if self.previousLayout == NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID:
      self.previousLayout = 0

    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndImportEvent, self.onSceneEndImport)

    self.clickedView = None
    self.clickTimer = qt.QTimer()
    self.clickTimer.setInterval(300)
    self.clickTimer.setSingleShot(True)
    self.clickTimer.timeout.connect(self.switchMainView)   
    self.clickNonResponsive = False
    self.clickNonResponseTimer = qt.QTimer()
    self.clickNonResponseTimer.setInterval(200)
    self.clickNonResponseTimer.setSingleShot(True)
    self.clickNonResponseTimer.timeout.connect(self.clickNonResponseOff)
    self.sliceViewClickObservers = []

    self.defaultSegmentationFileName = self.getPath() + "/Resources/Segmentations/DefaultSegmentation.seg.nrrd"

  def getPath(self):
    return os.path.dirname(slicer.modules.neurosegment.path)

  def enter(self):
    self.selectSegmentEditorParameterNode()
    # Allow switching between effects and selected segment using keyboard shortcuts
    layoutManager = slicer.app.layoutManager()
    if layoutManager.layout == NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID:
      self.ui.segmentEditorWidget.installKeyboardShortcuts(self.sliceViewWidget)
    else:
      self.ui.segmentEditorWidget.installKeyboardShortcuts()
    self.ui.segmentEditorWidget.setupViewObservations()
    self.ui.segmentEditorWidget.updateWidgetFromMRML()

  def exit(self):
    self.ui.segmentEditorWidget.setActiveEffect(None)
    self.ui.segmentEditorWidget.removeViewObservations()
    self.ui.segmentEditorWidget.uninstallKeyboardShortcuts()

  def onSceneStartClose(self, caller, event):
    self.ui.segmentEditorWidget.setSegmentationNode(None)
    self.ui.segmentEditorWidget.removeViewObservations()

  def onSceneEndClose(self, caller, event):
    if self.parent.isEntered:
      self.selectSegmentEditorParameterNode()
      self.ui.segmentEditorWidget.updateWidgetFromMRML()

  def onSceneEndImport(self, caller, event):
    if self.parent.isEntered:
      self.selectSegmentEditorParameterNode()
      self.ui.segmentEditorWidget.updateWidgetFromMRML()

  def onNodeAddedByUser(self, node):
    if not node.AddDefaultStorageNode():
      return
    storageNode = node.GetStorageNode()
    oldFileName = storageNode.GetFileName()
    storageNode.SetFileName(self.defaultSegmentationFileName)
    storageNode.ReadData(node)
    storageNode.SetFileName(oldFileName)

  def selectSegmentEditorParameterNode(self):
    # Select parameter set node if one is found in the scene, and create one otherwise
    segmentEditorSingletonTag = "NeruoSegment.SegmentEditor"
    segmentEditorNode = slicer.mrmlScene.GetSingletonNode(segmentEditorSingletonTag, "vtkMRMLSegmentEditorNode")
    if segmentEditorNode is None:
      segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
      segmentEditorNode.SetSingletonTag(segmentEditorSingletonTag)
      segmentEditorNode = slicer.mrmlScene.AddNode(segmentEditorNode)
    if self.ui.segmentEditorWidget.mrmlSegmentEditorNode() == segmentEditorNode:
      # nothing changed
      return
    self.ui.segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)

  def setupLayout(self):
    layout = ('''
<layout type="horizontal">
 <item>
  <view class="vtkMRMLSliceNode" singletontag="'''+self.allSliceViewNames[0]+'''">
   <property name="orientation" action="default">Axial</property>
     <property name="viewlabel" action="default">M</property>
   <property name="viewcolor" action="default">#808080</property>
  </view>
 </item>
 <item>
  <view class="vtkMRMLSliceNode" singletontag="'''+self.allSliceViewNames[1]+'''">
   <property name="orientation" action="default">Axial</property>
     <property name="viewlabel" action="default">R</property>
   <property name="viewcolor" action="default">#F34A33</property>
  </view>
 </item>
 <item>
  <view class="vtkMRMLSliceNode" singletontag="'''+self.allSliceViewNames[2]+'''">
   <property name="orientation" action="default">Sagittal</property>
   <property name="viewlabel" action="default">G</property>
   <property name="viewcolor" action="default">#6EB04B</property>
  </view>
 </item>
 <item>
  <view class="vtkMRMLSliceNode" singletontag="'''+self.allSliceViewNames[3]+'''">
   <property name="orientation" action="default">Coronal</property>
   <property name="viewlabel" action="default">Y</property>
   <property name="viewcolor" action="default">#EDD54C</property>
  </view>
 </item>
 <item>
  <view class="vtkMRMLViewNode" singletontag="1">
   <property name="viewlabel" action="default">1</property>
  </view>
 </item>
 <item>
  <view class="vtkMRMLViewNode" singletontag="M">
   <property name="viewlabel" action="default">M</property>
  </view>
 </item>
</layout>''')
    layoutManager = slicer.app.layoutManager()
    layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(
      NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID, layout)

  def cleanup(self):
    layoutManager = slicer.app.layoutManager()
    layoutManager.setLayout(self.previousLayout)
    layoutManager.disconnect('layoutChanged(int)', self.onLayoutChanged)
    self.mainViewWidget3DButton.setParent(None)
    self.mainViewWidget3DButton = None
    self.removeObservers()

  def toggleSliceViews(self):
    if self.ui.undockSliceViewButton.checked:
      slicer.app.layoutManager().setLayout(NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID)
    else:
      slicer.app.layoutManager().setLayout(self.previousLayout)

  def updateMainView(self):
    mainSliceWidget = slicer.app.layoutManager().sliceWidget(self.mainSliceViewName)
    main3DWidget = slicer.app.layoutManager().threeDWidget(self.main3DViewName)
    if self.mainViewWidget3DButton.checked and main3DWidget is not None:
      main3DWidget.threeDController().barLayout().addWidget(self.mainViewWidget3DButton)
    else:
      mainSliceWidget.sliceController().barLayout().addWidget(self.mainViewWidget3DButton)

    # The slice view becomes unhidden if the slice intersection is modified (shift + move in other views).
    # Show/hide parent widget instead
    mainSliceWidget.parent().setVisible(not self.mainViewWidget3DButton.checked)
    if main3DWidget is not None:
      main3DWidget.setVisible(self.mainViewWidget3DButton.checked)

  def onUndockedViewClosed(self):
    widgets = []
    for sliceViewName in self.allSliceViewNames:
      widgets.append(slicer.app.layoutManager().sliceWidget(sliceViewName))
    threeDView = slicer.app.layoutManager().threeDWidget(self.main3DViewName)
    widgets.append(threeDView)

    for widget in widgets:
      if widget.window() == self.sliceViewWidget:
        widget.setParent(slicer.app.layoutManager().viewport())

    self.ui.undockSliceViewButton.setChecked(False)
    self.toggleSliceViews()

  def onLayoutChanged(self, layoutID):
    self.ui.undockSliceViewButton.setChecked(layoutID == NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID)
    if layoutID != NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID:
      self.previousLayout = layoutID
      if self.sliceViewWidget:
        self.removeSecondaryViewClickObservers()
        self.sliceViewWidget.close()
        self.ui.segmentEditorWidget.installKeyboardShortcuts()
    elif layoutID == NeuroSegmentWidget.NEURO_SEGMENT_WIDGET_LAYOUT_ID:
      self.sliceViewWidget = UndockedViewWidget(qt.Qt.Horizontal)
      self.sliceViewWidget.setAttribute(qt.Qt.WA_DeleteOnClose)
      self.sliceViewWidget.closed.connect(self.onUndockedViewClosed)
      self.ui.segmentEditorWidget.installKeyboardShortcuts(self.sliceViewWidget)

      mainViewPanel = qt.QWidget()
      mainViewLayout = qt.QHBoxLayout()
      mainViewLayout.setContentsMargins(0,0,0,0)
      mainViewPanel.setLayout(mainViewLayout)
      # The slice view becomes unhidden if the slice intersection is modified (shift + move in other views).
      # By adding it to a parent widget, we can show/hide that widget instead
      sliceViewContainer = qt.QWidget()
      sliceViewContainerLayout = qt.QHBoxLayout()
      sliceViewContainer.setLayout(sliceViewContainerLayout)
      sliceViewContainerLayout.addWidget(slicer.app.layoutManager().sliceWidget(self.mainSliceViewName))
      sliceViewContainerLayout.setContentsMargins(0,0,0,0)
      mainViewLayout.addWidget(sliceViewContainer)
      mainViewLayout.addWidget(slicer.app.layoutManager().threeDWidget(self.main3DViewName))
      self.sliceViewWidget.addWidget(mainViewPanel)

      secondaryViewPanel = qt.QWidget()
      secondaryViewLayout = qt.QVBoxLayout()
      secondaryViewLayout.setContentsMargins(0,0,0,0)
      secondaryViewPanel.setLayout(secondaryViewLayout)
      for secondaryViewName in self.secondarySliceViewNames:
        secondaryViewLayout.addWidget(slicer.app.layoutManager().sliceWidget(secondaryViewName))
      self.sliceViewWidget.addWidget(secondaryViewPanel)

      # Find the first screen that is not the main screen
      # Otherwise default to the main screen
      mainScreen = slicer.util.mainWindow().windowHandle().screen()
      widgetScreen = mainScreen
      screens = slicer.app.screens()
      if len(screens) > 1:
        for screen in screens:
          if mainScreen != screen:
            widgetScreen = screen
            break

      self.sliceViewWidget.setStretchFactor(0, 3)
      self.sliceViewWidget.setStretchFactor(1, 1)
      self.sliceViewWidget.showFullScreen() # Will not move to the other monitor with just setScreen. showFullScreen moves the window
      self.sliceViewWidget.windowHandle().setScreen(widgetScreen)
      self.sliceViewWidget.showMaximized()
      self.sliceViewWidget.show()

      self.addSecondaryViewClickObservers()

      self.updateMainView()
      masterVolumeNode = self.ui.segmentEditorWidget.masterVolumeNode()
      if masterVolumeNode is not None:
        self.onMasterVolumeNodeChanged(masterVolumeNode)

  def removeSecondaryViewClickObservers(self):
    for tag, object in self.sliceViewClickObservers:
      if object is None:
        continue
      object.RemoveObserver(tag)
    self.sliceViewClickObservers = []

  def addSecondaryViewClickObservers(self):
      self.removeSecondaryViewClickObservers()
      for viewName in self.secondarySliceViewNames:
        sliceView = slicer.app.layoutManager().sliceWidget(viewName).sliceView()
        tag = sliceView.interactor().AddObserver(vtk.vtkCommand.LeftButtonDoubleClickEvent,
                                           lambda caller, event, viewName=viewName: self.onSecondaryViewDoubleClick(viewName))
        self.sliceViewClickObservers.append((tag, sliceView.interactor()))
        tag = sliceView.interactor().AddObserver(vtk.vtkCommand.LeftButtonReleaseEvent,
                                           lambda caller, event, viewName=viewName: self.onSecondaryViewClick(viewName))
        self.sliceViewClickObservers.append((tag, sliceView.interactor()))

  def switchMainView(self):
    layoutManager = slicer.app.layoutManager()
    sliceWidget = layoutManager.sliceWidget(self.clickedView)
    sliceNode = sliceWidget.mrmlSliceNode()
    mainSliceWidget = layoutManager.sliceWidget(self.mainSliceViewName)
    mainSliceNode = mainSliceWidget.mrmlSliceNode()
    mainSliceNode.GetSliceToRAS().DeepCopy(sliceNode.GetSliceToRAS())
    mainSliceNode.UpdateMatrices()

  def clickNonResponseOn(self):
    self.clickNonResponsive = True

  def clickNonResponseOff(self):
    self.clickNonResponsive = False

  def onSecondaryViewClick(self, viewName):
    if self.clickNonResponsive:
      return
    self.clickedView = viewName
    self.clickTimer.start()

  def onSecondaryViewDoubleClick(self, viewName):
    layoutManager = slicer.app.layoutManager()
    sliceWidget = layoutManager.sliceWidget(viewName)
    eventPositionWorld = [0,0,0,0]
    eventPosition = sliceWidget.sliceView().interactor().GetEventPosition()
    eventPositionXY = [eventPosition[0], eventPosition[1], 0, 1]
    sliceWidget.sliceLogic().GetSliceNode().GetXYToRAS().MultiplyPoint(eventPositionXY, eventPositionWorld);
    sliceNode = sliceWidget.mrmlSliceNode()
    sliceNode.JumpAllSlices(sliceNode.GetScene(),
                            eventPositionWorld[0], eventPositionWorld[1], eventPositionWorld[2],
                            slicer.vtkMRMLSliceNode.OffsetJumpSlice,
                            sliceNode.GetViewGroup(), sliceNode)
    self.clickTimer.stop()
    self.clickNonResponseOn()
    self.clickNonResponseTimer.start()

  def onMasterVolumeNodeChanged(self, volumeNode):
    self.ui.volumeThresholdWidget.setMRMLVolumeNode(volumeNode)
    self.ui.windowLevelWidget.setMRMLVolumeNode(volumeNode)
    layoutManager = slicer.app.layoutManager()
    sliceWidgetNames = layoutManager.sliceViewNames()

    volumeNodeID = ""
    if volumeNode is not None:
      volumeNodeID = volumeNode.GetID()

    for sliceWidgetName in sliceWidgetNames:
      sliceWidget = layoutManager.sliceWidget(sliceWidgetName)
      sliceWidget.mrmlSliceCompositeNode().SetBackgroundVolumeID(volumeNodeID)

  def showSingleModule(self, singleModule=True, toggle=False):

    if toggle:
      singleModule = not self.isSingleModuleShown

    self.isSingleModuleShown = singleModule

    if singleModule:
      # We hide all toolbars, etc. which is inconvenient as a default startup setting,
      # therefore disable saving of window setup.
      import qt
      settings = qt.QSettings()
      settings.setValue('MainWindow/RestoreGeometry', 'false')

    keepToolbars = [
      slicer.util.findChild(slicer.util.mainWindow(), 'MainToolBar'),
      slicer.util.findChild(slicer.util.mainWindow(), 'ViewToolBar'),
      slicer.util.findChild(slicer.util.mainWindow(), 'ViewersToolBar')]
    slicer.util.setToolbarsVisible(not singleModule, keepToolbars)
    slicer.util.setMenuBarsVisible(not singleModule)
    slicer.util.setApplicationLogoVisible(not singleModule)
    slicer.util.setModuleHelpSectionVisible(not singleModule)
    slicer.util.setModulePanelTitleVisible(not singleModule)
    slicer.util.setDataProbeVisible(not singleModule)
    slicer.util.setViewControllersVisible(not singleModule)

    if singleModule:
      slicer.util.setPythonConsoleVisible(False)

#
# NeuroSegmentLogic
#

class NeuroSegmentLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def loadSession(self, subjectDirectory, subjectName, sessionName):
    sessionDirectoryPath = subjectDirectory + "/" + subjectName + "/" + sessionName
    sessionDirectory = qt.QDir(sessionDirectoryPath)
    sessionDirectory.setNameFilters(["*.mrml"])

    mrmlFilesList = sessionDirectory.entryList()
    loaded = False
    if len(mrmlFilesList) > 0:
      properties = {}
      properties["clear"] = True
      try:
        slicer.util.loadScene(os.path.join(sessionDirectoryPath, mrmlFilesList[0]))
      except:
        return False

    parameterNode = self.getParameterNode()
    if parameterNode:
      parameterNode.SetParameter(NeuroSegment.subjectNameParameter, subjectName)
      parameterNode.SetParameter(NeuroSegment.sessionNameParameter, sessionName)
    return True

  def saveSession(self, subjectDirectory, subjectName, sessionName, progressCallback=None):
    sceneSaveDirectory = subjectDirectory + "/" + subjectName + "/" + sessionName
    return self.saveScene(sceneSaveDirectory, progressCallback)

  def saveScene(self, sceneSaveDirectory, progressCallback=None):
    logging.info("Saving scene to: {0}".format(sceneSaveDirectory))
    slicer.app.ioManager().addDefaultStorageNodes()

    fileNames = []

    progress = 0.0
    nodesSaved = 0
    nodes = slicer.mrmlScene.GetNodes()
    nodesToSaveCount = 0
    for node in nodes:
      if node and node.IsA("vtkMRMLStorableNode") and node.GetSaveWithScene():
        nodesToSaveCount += 1

    for node in nodes:
      if node is None:
        continue
      if not node.IsA("vtkMRMLStorableNode"):
        continue
      if not node.GetSaveWithScene():
        continue

      if progressCallback is not None and progressCallback('\nSaving node: %s' % node.GetName(), progress):
        break

      # Re-check if storageNode is still None: the node is stored in the scene XML file.
      if node.GetStorageNode() is None:
        continue

      # Disable compression of volume sequence nodes to make saving faster
      storageNode = node.GetStorageNode()
      storageNode.SetUseCompression(0)

      # Get the default write file extension from the storage nod
      defaultWriteFileExtension = "." + storageNode.GetDefaultWriteFileExtension()

      # Save node
      uniqueFileName = slicer.app.applicationLogic().PercentEncode(node.GetName());
      fileRenamed = False
      for name in fileNames:
        if uniqueFileName == name:
          fileRenamed = True
          uniqueFileName = slicer.mrmlScene.GenerateUniqueName(name)
          logging.info(
            "Filename {0} already exists for another node in the currently saving scene, {1} filename will be used instead".format(
            name + defaultWriteFileExtension, uniqueFileName + defaultWriteFileExtension))
          break

      # Save nodes in the Data folder
      if node.IsA("vtkMRMLVolumeNode"):
        nodeDirectory = os.path.join(sceneSaveDirectory, "anat")
      elif node.IsA("vtkMRMLSegmentationNode"):
        nodeDirectory = os.path.join(sceneSaveDirectory, "seg")
      else:
        nodeDirectory = os.path.join(sceneSaveDirectory, "data")
      if not os.access(nodeDirectory, os.F_OK):
        os.makedirs(nodeDirectory)

      nodeSavePath = os.path.join(nodeDirectory, uniqueFileName + defaultWriteFileExtension)
      fileNames.append(uniqueFileName)
      storageNode.SetFileName(nodeSavePath)
      nodeAlreadySavedInThisDir = os.path.isfile(nodeSavePath)
      if (not nodeAlreadySavedInThisDir) or node.GetModifiedSinceRead() or fileRenamed:
        logging.info("Saving node {0} with ID: {1}".format(node.GetName(), node.GetID()))
        if not storageNode.WriteData(node):
          logging.error("Saving node ID {0} failed".format(node.GetID()))
          logging.error("Saving failed")
          return False
        logging.info("Node with ID {0} successfully saved".format(node.GetID()))

      nodesSaved += 1
      progress = (100.0 * nodesSaved) / (nodesToSaveCount+1)

    if progressCallback is not None and progressCallback('\nSaving scene', progress):
      return False

    # Save scene file
    if not os.access(sceneSaveDirectory, os.F_OK):
      os.makedirs(sceneSaveDirectory)

    sceneName = "scene.mrml"
    if slicer.mrmlScene.GetModifiedSinceRead():
      file_path = os.path.join(sceneSaveDirectory, sceneName)
      if not slicer.mrmlScene.Commit(file_path):
        logging.error("Scene saving failed")
        return False

    if progressCallback is not None and progressCallback('\nSaving complete', 100.0):
      return False
    return True

class NeuroSegmentTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_NeuroSegment1()

  def test_NeuroSegment1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    self.delayDisplay('Test passed!')

#class NeuroSegmentFileDialog(object):
#   """This specially named class is detected by the scripted loadable
#   module and is the target for optional drag and drop operations.
#   See: Base/QTGUI/qSlicerScriptedFileDialog.h.

#   This class is used for overriding default scene save dialog
#   with simple saving the scene without asking anything.
#   """

#   def __init__(self, qSlicerFileDialog):
#     self.qSlicerFileDialog = qSlicerFileDialog
#     qSlicerFileDialog.fileType = 'NoFile'
#     qSlicerFileDialog.description = 'Save scene'
#     qSlicerFileDialog.action = slicer.qSlicerFileDialog.Write
#     self.directoriesToAdd = []

#   def execDialog(self):
#     moduleWidget = slicer.modules.neurosegment.widgetRepresentation().self()
#     moduleWidget.showSaveSessionDialog()
#     return True
