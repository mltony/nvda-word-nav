# -*- coding: UTF-8 -*-
#A part of  WordNav addon for NVDA
#Copyright (C) 2020 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import api
import bisect
import collections
import config
import controlTypes
import core
import copy
import ctypes
from ctypes import create_string_buffer, byref
import cursorManager
import documentBase
import functools
import editableText
import globalPluginHandler
import gui
from gui import guiHelper, nvdaControls
from gui.settingsDialogs import SettingsPanel
import inputCore
import itertools
import json
import keyboardHandler
from logHandler import log
import NVDAHelper
from NVDAObjects import behaviors
from NVDAObjects.window import winword
import nvwave
import operator
import os
import re
from scriptHandler import script, willSayAllResume
import speech
import struct
import textInfos
import threading
import time
import tones
import types
import ui
import watchdog
import wave
import winUser
import wx

winmm = ctypes.windll.winmm

try:
    REASON_CARET = controlTypes.REASON_CARET
except AttributeError:
    REASON_CARET = controlTypes.OutputReason.CARET



debug = False
if debug:
    import threading
    LOG_FILE_NAME = "C:\\Users\\tony\\Dropbox\\1.txt"
    f = open(LOG_FILE_NAME, "w")
    f.close()
    LOG_MUTEX = threading.Lock()
    def mylog(s):
        with LOG_MUTEX:
            f = open(LOG_FILE_NAME, "a", encoding='utf-8')
            print(s, file=f)
            #f.write(s.encode('UTF-8'))
            #f.write('\n')
            f.close()
else:
    def mylog(*arg, **kwarg):
        pass

def myAssert(condition):
    if not condition:
        raise RuntimeError("Assertion failed")

module = "wordNav"
def initConfiguration():
    defaultBulkyRegexp = r'$|(^|(?<=[\s\(\)]))[^\s\(\)]|\b(:\d+)+\b'
    confspec = {
        "overrideMoveByWord" : "boolean( default=True)",
        "enableInBrowseMode" : "boolean( default=True)",
        "leftControlAssignmentIndex": "integer( default=3, min=0, max=5)",
        "rightControlAssignmentIndex": "integer( default=1, min=0, max=5)",
        "leftControlWindowsAssignmentIndex": "integer( default=2, min=0, max=5)",
        "rightControlWindowsAssignmentIndex": "integer( default=4, min=0, max=5)",
        "bulkyWordPunctuation" : f"string( default='():')",
        "bulkyWordRegex" : f"string( default='{defaultBulkyRegexp}')",
        "wordCount": "integer( default=5, min=1, max=1000)",
        "applicationsBlacklist" : f"string( default='')",
    }
    config.conf.spec[module] = confspec

def getConfig(key):
    value = config.conf[module][key]
    return value
def setConfig(key, value):
    config.conf[module][key] = value


addonHandler.initTranslation()
initConfiguration()


# Regular expression for the beginning of a word. Matches:
#  1. End of string
# 2. Beginning of any word: \b\w
# 3. Punctuation mark preceded by non-punctuation mark: (?<=[\w\s])[^\w\s]
# 4. Punctuation mark preceded by beginning of the string
wordReString = r'$|\b\w|(?<=[\w\s])[^\w\s]|^[^\w\s]'
wordRe = re.compile(wordReString)

# Regular expression for beginning of fine word. This word definition breaks
# camelCaseIdentifiers  and underscore_separated_identifiers into separate sections for easier editing.
# Includes all conditions for wordRe plus additionally:
# 5. Word letter, that is not  underscore, preceded by underscore.
#6. Capital letter preceded by a lower-case letter.
wordReFineString = wordReString + "|(?<=_)(?!_)\w|(?<=[a-z])[A-Z]"
wordReFineString += r"|(?<=\d)[a-zA-Z]|(?<=[a-zA-Z])\d"
wordReFine = re.compile(wordReFineString)

# Regular expression for bulky words. Treats any punctuation signs as part of word.
# Matches either:
# 1. End of string, or
# 2.     Non-space character preceded either by beginning of the string or a space character.
regexpEscapeSet = set(r". \ + * ? [ ^ ] $ ( ) { } = ! < > | : -".split())
def escapeRegex(s):
    def escapeCharacter(c):
        if c in regexpEscapeSet:
            return f"\\{c}"
        return c
    return "".join(map(escapeCharacter, s))
def generateWordReBulky(punctuation=None):
    if punctuation is None:
        punctuation = getConfig("bulkyWordPunctuation")
    punctuation = escapeRegex(punctuation)
    space = f"\\s{punctuation}"
    wordReBulkyString = f"$|(^|(?<=[{space}]))[^{space}]"
    wordReBulky = re.compile(wordReBulkyString)
    return wordReBulky

def generateWordReCustom():
    wordReBulkyString = getConfig("bulkyWordRegex")
    wordReBulky = re.compile(wordReBulkyString)
    return wordReBulky

# These constants map command assignment combo box index to actual functions
# w stands for navigate by word
# b and f stand for navigate by bulky/fine word
# 0 stands for unassigned
leftControlFunctions = "wwwwwbfwwbf"
rightControlFunctions = "wwwbfwwbfww"
controlWindowsFunctions = "0bf0000fbfb"

def getRegexByFunction(index):
    if index == 1:
        return wordRe,1
    elif index == 2:
        return generateWordReBulky(),1
    elif index == 3:
        return wordReFine,1
    elif index == 4:
        return generateWordReBulky(), getConfig("wordCount")
    elif index == 5:
        return generateWordReCustom(), 1
    else:
        return None, None

class SettingsDialog(SettingsPanel):
    # Translators: Title for the settings dialog
    title = _("WordNav")
    controlAssignmentText = [
        _("Default NVDA word navigation (WordNav disabled)"),
        _("Notepad++ style navigation"),
        _("Bulky word navigation"),
        _("Fine word navigation - good for programming"),
        _("MultiWord navigation - reads multiple words at once"),
        _("Custom regular expression word navigation"),
    ]
    controlWindowsAssignmentText = [
        _("Unassigned"),
    ] + controlAssignmentText[1:]

    def makeSettings(self, settingsSizer):
        sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
      # checkbox override move by word
        # Translators: Checkbox for override move by word
        label = _("Enable WordNav in editables")
        self.overrideMoveByWordCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.overrideMoveByWordCheckbox.Value = getConfig("overrideMoveByWord")
      # checkbox enableInBrowseMode
        # Translators: Checkbox for enableInBrowseMode
        label = _("Enable WordNav in browse mode.")
        self.enableInBrowseModeCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.enableInBrowseModeCheckbox.Value = getConfig("enableInBrowseMode")
      # left control assignment Combo box
        # Translators: Label for left control assignment combo box
        label = _("Left control behavior:")
        self.leftControlAssignmentCombobox = sHelper.addLabeledControl(label, wx.Choice, choices=self.controlAssignmentText)
        self.leftControlAssignmentCombobox.Selection = getConfig("leftControlAssignmentIndex")
      # right control assignment Combo box
        # Translators: Label for right control assignment combo box
        label = _("Right control behavior:")
        self.rightControlAssignmentCombobox = sHelper.addLabeledControl(label, wx.Choice, choices=self.controlAssignmentText)
        self.rightControlAssignmentCombobox.Selection = getConfig("rightControlAssignmentIndex")
      # Left Control+Windows assignment Combo box
        # Translators: Label for control+windows assignment combo box
        label = _("Left Control+Windows behavior:")
        self.leftControlWindowsAssignmentCombobox = sHelper.addLabeledControl(label, wx.Choice, choices=self.controlWindowsAssignmentText)
        self.leftControlWindowsAssignmentCombobox.Selection = getConfig("leftControlWindowsAssignmentIndex")

      # Right Control+Windows assignment Combo box
        # Translators: Label for control+windows assignment combo box
        label = _("Right Control+Windows behavior:")
        self.rightControlWindowsAssignmentCombobox = sHelper.addLabeledControl(label, wx.Choice, choices=self.controlWindowsAssignmentText)
        self.rightControlWindowsAssignmentCombobox.Selection = getConfig("rightControlWindowsAssignmentIndex")
      # bulkyWordPunctuation
        # Translators: Label for bulkyWordPunctuation edit box
        self.bulkyWordPunctuationEdit = sHelper.addLabeledControl(_("Bulky word separators:"), wx.TextCtrl)
        self.bulkyWordPunctuationEdit.Value = getConfig("bulkyWordPunctuation")

      # bulkyWordPunctuation
        # Translators: Label for bulkyWordPunctuation edit box
        self.customWordRegexEdit = sHelper.addLabeledControl(_("Custom word regular expression:"), wx.TextCtrl)
        self.customWordRegexEdit.Value = getConfig("bulkyWordRegex")
      # MultiWord word count
        # Translators: Label for multiWord wordCount edit box
        self.wordCountEdit = sHelper.addLabeledControl(_("Word count for multiWord navigation:"), wx.TextCtrl)
        self.wordCountEdit.Value = str(getConfig("wordCount"))

      # applicationsBlacklist edit
        # Translators: Label for blacklisted applications edit box
        self.applicationsBlacklistEdit = sHelper.addLabeledControl(_("Disable WordNav in applications (comma-separated list)"), wx.TextCtrl)
        self.applicationsBlacklistEdit.Value = getConfig("applicationsBlacklist")

    def onSave(self):
        try:
            if int(self.wordCountEdit.Value) <= 1:
                raise Exception()
        except:
            self.wordCountEdit.SetFocus()
            ui.message(_("WordCount must be a positive integer greater than 2."))
            return
        setConfig("overrideMoveByWord", self.overrideMoveByWordCheckbox.Value)
        setConfig("enableInBrowseMode", self.enableInBrowseModeCheckbox.Value)
        setConfig("leftControlAssignmentIndex", self.leftControlAssignmentCombobox.Selection)
        setConfig("rightControlAssignmentIndex", self.rightControlAssignmentCombobox.Selection)
        setConfig("leftControlWindowsAssignmentIndex", self.leftControlWindowsAssignmentCombobox.Selection)
        setConfig("rightControlWindowsAssignmentIndex", self.rightControlWindowsAssignmentCombobox.Selection)
        setConfig("bulkyWordPunctuation", self.bulkyWordPunctuationEdit.Value)
        setConfig("bulkyWordRegex", self.customWordRegexEdit.Value)
        setConfig("wordCount", int(self.wordCountEdit.Value))
        setConfig("applicationsBlacklist", self.applicationsBlacklistEdit.Value)



class Beeper:
    BASE_FREQ = speech.IDT_BASE_FREQUENCY
    def getPitch(self, indent):
        return self.BASE_FREQ*2**(indent/24.0) #24 quarter tones per octave.

    BEEP_LEN = 10 # millis
    PAUSE_LEN = 5 # millis
    MAX_CRACKLE_LEN = 400 # millis
    MAX_BEEP_COUNT = MAX_CRACKLE_LEN // (BEEP_LEN + PAUSE_LEN)

    def __init__(self):
        self.player = nvwave.WavePlayer(
            channels=2,
            samplesPerSec=int(tones.SAMPLE_RATE),
            bitsPerSample=16,
            outputDevice=config.conf["speech"]["outputDevice"],
            wantDucking=False
        )



    def fancyCrackle(self, levels, volume):
        levels = self.uniformSample(levels, self.MAX_BEEP_COUNT )
        beepLen = self.BEEP_LEN
        pauseLen = self.PAUSE_LEN
        pauseBufSize = NVDAHelper.generateBeep(None,self.BASE_FREQ,pauseLen,0, 0)
        beepBufSizes = [NVDAHelper.generateBeep(None,self.getPitch(l), beepLen, volume, volume) for l in levels]
        bufSize = sum(beepBufSizes) + len(levels) * pauseBufSize
        buf = ctypes.create_string_buffer(bufSize)
        bufPtr = 0
        for l in levels:
            bufPtr += NVDAHelper.generateBeep(
                ctypes.cast(ctypes.byref(buf, bufPtr), ctypes.POINTER(ctypes.c_char)),
                self.getPitch(l), beepLen, volume, volume)
            bufPtr += pauseBufSize # add a short pause
        self.player.stop()
        self.player.feed(buf.raw)

    def simpleCrackle(self, n, volume):
        return self.fancyCrackle([0] * n, volume)


    NOTES = "A,B,H,C,C#,D,D#,E,F,F#,G,G#".split(",")
    NOTE_RE = re.compile("[A-H][#]?")
    BASE_FREQ = 220
    def getChordFrequencies(self, chord):
        myAssert(len(self.NOTES) == 12)
        prev = -1
        result = []
        for m in self.NOTE_RE.finditer(chord):
            s = m.group()
            i =self.NOTES.index(s)
            while i < prev:
                i += 12
            result.append(int(self.BASE_FREQ * (2 ** (i / 12.0))))
            prev = i
        return result

    def fancyBeep(self, chord, length, left=10, right=10):
        beepLen = length
        freqs = self.getChordFrequencies(chord)
        intSize = 8 # bytes
        bufSize = max([NVDAHelper.generateBeep(None,freq, beepLen, right, left) for freq in freqs])
        if bufSize % intSize != 0:
            bufSize += intSize
            bufSize -= (bufSize % intSize)
        self.player.stop()
        bbs = []
        result = [0] * (bufSize//intSize)
        for freq in freqs:
            buf = ctypes.create_string_buffer(bufSize)
            NVDAHelper.generateBeep(buf, freq, beepLen, right, left)
            bytes = bytearray(buf)
            unpacked = struct.unpack("<%dQ" % (bufSize // intSize), bytes)
            result = map(operator.add, result, unpacked)
        maxInt = 1 << (8 * intSize)
        result = map(lambda x : x %maxInt, result)
        packed = struct.pack("<%dQ" % (bufSize // intSize), *result)
        self.player.feed(packed)

    def uniformSample(self, a, m):
        n = len(a)
        if n <= m:
            return a
        # Here assume n > m
        result = []
        for i in range(0, m*n, n):
            result.append(a[i  // m])
        return result
    def stop(self):
        self.player.stop()


def executeAsynchronously(gen):
    """
    This function executes a generator-function in such a manner, that allows updates from the operating system to be processed during execution.
    For an example of such generator function, please see GlobalPlugin.script_editJupyter.
    Specifically, every time the generator function yilds a positive number,, the rest of the generator function will be executed
    from within wx.CallLater() call.
    If generator function yields a value of 0, then the rest of the generator function
    will be executed from within wx.CallAfter() call.
    This allows clear and simple expression of the logic inside the generator function, while still allowing NVDA to process update events from the operating system.
    Essentially the generator function will be paused every time it calls yield, then the updates will be processed by NVDA and then the remainder of generator function will continue executing.
    """
    if not isinstance(gen, types.GeneratorType):
        raise Exception("Generator function required")
    try:
        value = gen.__next__()
    except StopIteration:
        return
    l = lambda gen=gen: executeAsynchronously(gen)
    if value == 0:
        wx.CallAfter(l)
    else:
        wx.CallLater(value, l)

def makeVkInput(vkCodes):
    result = []
    if not isinstance(vkCodes, list):
        vkCodes = [vkCodes]
    for vk in vkCodes:
        input = winUser.Input(type=winUser.INPUT_KEYBOARD)
        input.ii.ki.wVk = vk
        result.append(input)
    for vk in reversed(vkCodes):
        input = winUser.Input(type=winUser.INPUT_KEYBOARD)
        input.ii.ki.wVk = vk
        input.ii.ki.dwFlags = winUser.KEYEVENTF_KEYUP
        result.append(input)
    return result


releaserCounter = 0
cachedTextInfo = None
cachedOffset = 0
cachedCollapseDirection = None
controlModifiers = [
    winUser.VK_LCONTROL, winUser.VK_RCONTROL,
    winUser.VK_LSHIFT, winUser.VK_RSHIFT,
    winUser.VK_LMENU, winUser.VK_RMENU,
    winUser.VK_LWIN, winUser.VK_RWIN,
]
kbdRight = keyboardHandler.KeyboardInputGesture.fromName("RightArrow")
kbdLeft = keyboardHandler.KeyboardInputGesture.fromName("LeftArrow")
def asyncPressRightArrowAfterControlIsReleased(localReleaserCounter, selectionInfo, offset):
    global releaserCounter, cachedTextInfo, cachedOffset, cachedCollapseDirection, suppressSelectionMessages
    while True:
        if releaserCounter != localReleaserCounter:
            return
        status = [
            winUser.getKeyState(k) & 32768
            for k in controlModifiers
        ]
        if not any(status):
            collapseDirection = cachedCollapseDirection
            cachedTextInfo = None
            cachedOffset = 0
            cachedCollapseDirection = None
            input = []
            if collapseDirection is not None:
                input += makeVkInput([winUser.VK_RIGHT if collapseDirection > 0 else winUser.VK_LEFT])
            input += makeVkInput([winUser.VK_RIGHT if offset >= 0 else winUser.VK_LEFT]) * abs(offset)
            with keyboardHandler.ignoreInjection():
                winUser.SendInput(input)
            return
            if False:
                # This old method with selecting pretext doesn't work as well
              #Step 0. Don't announce Selected/unselected for a while.
                suppressSelectionMessages= True
              # Step 1: Select from start to new cursor
                selectionInfo.updateSelection()
              # Step 2. Clear selection to the right thus setting the caret in the right place.
                if len(selectionInfo.text) > 0:
                    # First wait until selection appears
                    t0 = time.time()
                    while True:
                        if time.time() - t0 > 0.050:
                            raise Exception("Timeout 50ms: Couldn't select pretext!")
                        if selectionInfo._startObj.IAccessibleTextObject.nSelections  > 0:
                            break
                        yield 1

                    # kbdRight.send()
                    # The previous line causes a deadlock sometimes - also somehow it triggers NVDA internal response to this keystroke, so we need to fool NVDA.
                    with keyboardHandler.ignoreInjection():
                        winUser.SendInput(makeVkInput([winUser.VK_RIGHT]))
                else:
                    #kbdLeft.send()
                    with keyboardHandler.ignoreInjection():
                        winUser.SendInput(makeVkInput([winUser.VK_LEFT]))

                yield 20
              # Step 4. Now restore announcing selection messages and return
                suppressSelectionMessages = False
                return
        yield 1



originalSpeakSelectionChange = None
suppressSelectionMessages = False
def preSpeakSelectionChange(oldInfo, newInfo, *args, **kwargs):
    global suppressSelectionMessages
    if suppressSelectionMessages:
        return False
    return originalSpeakSelectionChange(oldInfo, newInfo, *args, **kwargs)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("WordNav")

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        self.createMenu()
        self.injectHooks()
        self.beeper = Beeper()

    def createMenu(self):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(SettingsDialog)

    def terminate(self):
        self.removeHooks()
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(SettingsDialog)

    def injectHooks(self):
        global originalSpeakSelectionChange
        self.originalMoveByWord = editableText.EditableText.script_caret_moveByWord
        editableText.EditableText.script_caret_moveByWord = lambda selfself, gesture, *args, **kwargs: self.script_caretMoveByWord(selfself, gesture, *args, **kwargs)
        editableText.EditableText.script_caret_moveByWordEx = lambda selfself, gesture, *args, **kwargs: self.script_caretMoveByWordEx(selfself, gesture, *args, **kwargs)
        editableText.EditableText._EditableText__gestures["kb:control+Windows+leftArrow"] = "caret_moveByWordEx",
        editableText.EditableText._EditableText__gestures["kb:control+Windows+RightArrow"] = "caret_moveByWordEx",
        self.originalMoveBack = cursorManager.CursorManager.script_moveByWord_back
        self.originalMoveForward = cursorManager.CursorManager.script_moveByWord_forward
        cursorManager.CursorManager.script_moveByWord_back = lambda selfself, gesture, *args, **kwargs: self.script_cursorMoveByWord(selfself, gesture, *args, **kwargs)
        cursorManager.CursorManager.script_moveByWord_forward = lambda selfself, gesture, *args, **kwargs: self.script_cursorMoveByWord(selfself, gesture, *args, **kwargs)
        cursorManager.CursorManager.script_cursorMoveByWordEx = lambda selfself, gesture, *args, **kwargs: self.script_cursorMoveByWordEx(selfself, gesture, *args, **kwargs)
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+leftArrow"] = "cursorMoveByWordEx",
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+RightArrow"] = "cursorMoveByWordEx",
        originalSpeakSelectionChange = speech.speakSelectionChange
        speech.speakSelectionChange = preSpeakSelectionChange



    def  removeHooks(self):
        editableText.EditableText.script_caret_moveByWord = self.originalMoveByWord
        del editableText.EditableText.script_caret_moveByWordEx
        del editableText.EditableText._EditableText__gestures["kb:control+Windows+leftArrow"]
        del editableText.EditableText._EditableText__gestures["kb:control+Windows+RightArrow"]
        cursorManager.CursorManager.script_moveByWord_back = self.originalMoveBack
        cursorManager.CursorManager.script_moveByWord_forward = self.originalMoveForward
        del cursorManager.CursorManager.script_cursorMoveByWordEx
        del cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+leftArrow"]
        del cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+RightArrow"]
        speech.speakSelectionChange = originalSpeakSelectionChange

    def isBlacklistedApp(self):
        focus = api.getFocusObject()
        appName = focus.appModule.appName
        if appName.lower() in getConfig("applicationsBlacklist").lower().strip().split(","):
            return True
        return False

    def getControl(self, gesture):
        for modVk, modExt in gesture.generalizedModifiers:
            if modVk == winUser.VK_CONTROL:
                if not modExt:
                    # Left control
                    return "left"
                else:
                    # Right control
                    return "right"
        raise Exception("Control is not pressed - please don't reassign WordNav keystrokes!")

    @functools.lru_cache(maxsize=100)
    def computeBoundariesCached(self, text, wordRe):
        boundaries = [m.start() for m in wordRe.finditer(text)]
        boundaries = sorted(list(set(boundaries)))
        return boundaries
    def script_caretMoveByWord(self, selfself, gesture):
        option = f"{self.getControl(gesture)}ControlAssignmentIndex"
        regex, wordCount = getRegexByFunction(getConfig(option))
        if not regex or self.isBlacklistedApp() or not getConfig('overrideMoveByWord'):
            return self.originalMoveByWord(selfself, gesture)
        onError = lambda e: self.originalMoveByWord(selfself, gesture)
        return self.caretMoveByWordImpl(gesture, regex, onError, wordCount)


    def script_caretMoveByWordEx(self, selfself, gesture):
        option = f"{self.getControl(gesture)}ControlWindowsAssignmentIndex"
        regex, wordCount = getRegexByFunction(getConfig(option))
        if self.isBlacklistedApp() or not getConfig('overrideMoveByWord') or regex is None:
            gesture.send()
            return
        def onError(e):
            raise e
        return self.caretMoveByWordImpl(gesture, regex, onError, wordCount)

    def caretMoveByWordImpl(self, gesture, wordRe, onError, wordCount):
        # Implementation in editables
        global cachedTextInfo, cachedOffset, cachedCollapseDirection
        chromeHack = False
        vsCodeHack = False
        def preprocessText(lineText):
            return lineText.replace("\r\n", "\n").replace("\r", "\n") # Fix for Visual Studio, that has a different definition of paragraph, that often contains newlines written in \r\n format
        def moveByCharacter(textInfo, adjustment, endPoint=None):
            if not vsCodeHack:
                return textInfo.move(textInfos.UNIT_CHARACTER, adjustment, endPoint)
            else:
                # We don't do any sanity checking here - assuming that it's possible to perform such move
                # NVDA splits move by N characters into N separate moves by single character.
                # This is too slow in VS Code, so optimizing
                offset = textInfo._start._startOffset
                offset += adjustment
                if endPoint is None:
                    textInfo._start._startOffset = offset
                    textInfo._end._startOffset = offset
                textInfo._start._endOffset = offset
                textInfo._end._endOffset = offset
                return 0

        try:
            if 'leftArrow' == gesture.mainKeyName:
                direction = -1
            elif 'rightArrow' == gesture.mainKeyName:
                direction = 1
            else:
                return onError(None)

            focus = api.getFocusObject()
            if focus.appModule.appName == 'chrome':
                chromeHack = True
            if 'vs code' in focus.appModule.appName:
                vsCodeHack = True
            if focus.appModule.appName == "devenv":
                # In visual Studio paragraph textInfo returns the whole document.
                # Therefore use UNIT_LINE instead
                unit = textInfos.UNIT_LINE
            else:
                unit = textInfos.UNIT_PARAGRAPH
            mylog(f"direction={direction} unit={unit}")
            if chromeHack and cachedTextInfo is not None:
                caretInfo = cachedTextInfo.copy()
                offset = cachedOffset
                mylog(f"CC: cachedOffset={cachedOffset}")
            else:
                caretInfo = focus.makeTextInfo(textInfos.POSITION_SELECTION)
                if caretInfo.isCollapsed:
                    cachedCollapseDirection = None
                else:
                    cachedCollapseDirection = 1 if direction > 0 else -1
                caretInfo.collapse(end=(direction > 0))
                offset = 0

            lineInfo = caretInfo.copy()
            lineInfo.expand(unit)
            offsetInfo = lineInfo.copy()
            offsetInfo.setEndPoint(caretInfo, 'endToEnd')
            caret = len(preprocessText(offsetInfo.text))
            for lineAttempt in range(100):
                lineText = lineInfo.text.rstrip('\r\n')
                lineText = preprocessText(lineText)
                mylog(f"lineAttempt={lineAttempt}; paragraph:")
                mylog(lineText)
                isEmptyLine = len(lineText.strip()) == 0
                boundaries = self.computeBoundariesCached(lineText, wordRe)
                mylog(f"boundaries={boundaries}, isEmptyLine={isEmptyLine}")
                if direction > 0:
                    newWordIndex = bisect.bisect_right(boundaries, caret)
                else:
                    newWordIndex = bisect.bisect_left(boundaries, caret) - 1
                mylog(f"newWordIndex={newWordIndex}, len(boundaries)={len(boundaries)}")
                if not isEmptyLine and (0 <= newWordIndex < len(boundaries)):
                    # Next word found in the same paragraph
                    mylog("This para!")
                    if lineAttempt == 0:
                        if wordCount > 1:
                            # newWordIndex at this point already implies that we moved by 1 word. If requested to move by wordCount words, need to move by (wordCount - 1) more.
                            newWordIndex += (wordCount - 1) * direction
                            newWordIndex = max(0, newWordIndex)
                            newWordIndex = min(newWordIndex, len(boundaries) - 1)
                        adjustment = boundaries[newWordIndex] - caret
                        mylog(f"adjustment={adjustment}=boundaries[newWordIndex] - caret={boundaries[newWordIndex]} - {caret}")
                        offset += adjustment
                        mylog(f"CC_sameLine: offset += adjustment; now offset={offset}")
                        
                        newInfo = caretInfo
                        moveByCharacter(newInfo, adjustment)
                    else:
                        newInfo = lineInfo
                        adjustment =  boundaries[newWordIndex]
                        mylog(f"adjustment={adjustment}")
                        if direction > 0:
                            offset += adjustment
                            mylog(f"CC_nextLine: offset += adjustment; now offset={offset}")
                        else:
                            offset -= len(lineText) - adjustment
                            mylog(f"CC_prevLine: offset -= len() + adjustment; now offset={offset}")
                        newInfo.collapse(end=False)
                        
                        moveByCharacter(newInfo, adjustment)
                    if newWordIndex + 1 < len(boundaries):
                        mylog("This is not the end of line word, so need to make a non-empty textInfo")
                        followingWordIndex = newWordIndex + wordCount
                        followingWordIndex = max(0, followingWordIndex)
                        followingWordIndex = min(followingWordIndex, len(boundaries) - 1)
                        moveByCharacter(
                            newInfo,
                            boundaries[followingWordIndex] - boundaries[newWordIndex],
                            endPoint='end',
                        )
                    speech.speakTextInfo(newInfo, unit=textInfos.UNIT_WORD, reason=REASON_CARET)
                    newInfo.collapse()
                    if not chromeHack:
                        newInfo.updateCaret()
                    else:
                        # Due to a bug in chromium we need to perform a workaround:
                        # https://bugs.chromium.org/p/chromium/issues/detail?id=1260726#c2
                        global releaserCounter
                        cachedTextInfo = newInfo
                        api.cti = cachedTextInfo
                        cachedOffset = offset
                        selectionInfo = newInfo.copy()
                        allInfo = focus.makeTextInfo(textInfos.POSITION_ALL)
                        selectionInfo.setEndPoint(allInfo, which='startToStart')
                        releaserCounter += 1
                        executeAsynchronously(asyncPressRightArrowAfterControlIsReleased(releaserCounter, selectionInfo, offset))

                    return
                else:
                    # New word found in the next para!
                    mylog("Next para!")
                    lineInfo.collapse()
                    if lineAttempt == 0:
                        if direction > 0:
                            offset += len(lineText) - caret
                            mylog(f"CC_firstNextLine: offset = {offset}")
                        else:
                            offset -= caret
                            mylog(f"CC_firstPrevLine: offset = {offset}")
                    else:
                        offset += direction * len(lineText)
                        mylog(f"CC_followingNextPrevLine: offset = {offset}")
                    # Also don't forget about newline character itself:
                    offset += direction
                    mylog(f"CC_newLineCharacter: offset = {offset}")
                    result = lineInfo.move(unit, direction)
                    if result != 0:
                        result2 = 1
                        if direction > 0:
                            # In Visual Studio 2019 when we are in the last paragraph/line, it still allows us to move further by another paragraph/line.
                            # In this case the cursor just jumps to the end of that line, but the result ==1,
                            # Making us believe that we just found another line.
                            # As a result, subsequent call to expand will just return us back to the beginning of that same line.
                            # In order to avoid this, we need to try moving forward by one more character,
                            # in order to test whether there is something there.
                            tempInfo = lineInfo.copy()
                            result2 = tempInfo.move(textInfos.UNIT_CHARACTER, 1)
                    if result == 0 or result2 == 0:
                        self.beeper.fancyBeep('HF', 100, left=25, right=25)
                        return
                    lineInfo.expand(unit)
                    # now try to find next word again on next/previous line
                    if direction > 0:
                        caret = -1
                    else:
                        caret = len(lineInfo.text)
            #raise Exception('Failed to find next word')
            self.beeper.fancyBeep('HF', 100, left=25, right=25)
        except NotImplementedError as e:
            return onError(e)

    def script_cursorMoveByWord(self, selfself, gesture):
        if 'leftArrow' == gesture.mainKeyName:
            onError = lambda e:  self.originalMoveBack(selfself, gesture)
        elif 'rightArrow' == gesture.mainKeyName:
            onError = lambda e:  self.originalMoveForward(selfself, gesture)
        else:
            raise Exception("Impossible!")
        option = f"{self.getControl(gesture)}ControlAssignmentIndex"
        regex, wordCount = getRegexByFunction(getConfig(option))
        if not regex or self.isBlacklistedApp() or not getConfig('enableInBrowseMode'):
            return onError(None)
        return self.cursorMoveByWordImpl(selfself, gesture, regex, onError, wordCount)

    def script_cursorMoveByWordEx(self, selfself, gesture):
        option = f"{self.getControl(gesture)}ControlWindowsAssignmentIndex"
        regex, wordCount = getRegexByFunction(getConfig(option))
        if self.isBlacklistedApp() or not getConfig('enableInBrowseMode') or regex is None:
            gesture.send()
            return
        def onError(e):
            raise e
        return self.cursorMoveByWordImpl(selfself, gesture, regex, onError, wordCount)

    def cursorMoveByWordImpl(self, selfself, gesture, wordRe, onError, wordCount=1):
        # Implementation in browse mode
        try:
            if 'leftArrow' == gesture.mainKeyName:
                direction = -1
            elif 'rightArrow' == gesture.mainKeyName:
                direction = 1
            else:
                return onError(None)
            mylog(f"Moving direction={direction}")
            caretInfo = selfself.makeTextInfo(textInfos.POSITION_CARET)
            caretInfo.collapse(end=(direction > 0))
            lineInfo = caretInfo.copy()
            lineInfo.expand(textInfos.UNIT_PARAGRAPH)
            offsetInfo = lineInfo.copy()
            offsetInfo.setEndPoint(caretInfo, 'endToEnd')
            caret = len(offsetInfo.text)
            for lineAttempt in range(100):
                lineText = lineInfo.text.rstrip('\r\n')
                mylog("current paragraph:")
                mylog(lineText)
                isEmptyLine = len(lineText.strip()) == 0
                boundaries = self.computeBoundariesCached(lineText, wordRe)
                if lineAttempt > 0:
                    # we need to update caret, since this is not the original paragraph we're in
                    if direction > 0:
                        caret = -1
                    else:
                        caret = boundaries[-1]
                mylog(f"isEmptyLine={isEmptyLine}")
                mylog("boundaries=" + ",".join(map(str, boundaries)))
                mylog(f"len(boundaries)={len(boundaries)}")
                mylog(f"caret={caret}")
                if direction > 0:
                    newWordIndex = bisect.bisect_right(boundaries, caret)
                else:
                    newWordIndex = bisect.bisect_left(boundaries, caret) - 1
                mylog(f"newWordIndex={newWordIndex}")
                if not isEmptyLine and (0 <= newWordIndex < len(boundaries) - 1):
                    # Next word is found in this paragraph
                    mylog("this para!")
                    if lineAttempt == 0:
                        if wordCount > 1:
                            # newWordIndex at this point already implies that we moved by 1 word. If requested to move by wordCount words, need to move by (wordCount - 1) more.
                            newWordIndex += (wordCount - 1) * direction
                            newWordIndex = max(0, newWordIndex)
                            newWordIndex = min(newWordIndex, len(boundaries) - 2)
                        adjustment = boundaries[newWordIndex] - caret
                        newInfo = caretInfo
                        newInfo.move(textInfos.UNIT_CHARACTER, adjustment)
                    else:
                        newInfo = lineInfo
                        if True:#direction > 0:
                            adjustment =  boundaries[newWordIndex]
                            newInfo.collapse(end=False)
                        else:
                            adjustment =  boundaries[newWordIndex] - len(lineInfo.text)
                            newInfo.collapse(end=True)

                        result = newInfo.move(textInfos.UNIT_CHARACTER, adjustment)
                    if newWordIndex + 1 < len(boundaries):
                        followingWordIndex = newWordIndex + wordCount
                        followingWordIndex = max(0, followingWordIndex)
                        followingWordIndex = min(followingWordIndex, len(boundaries) - 1)
                        newInfo.move(
                            textInfos.UNIT_CHARACTER,
                            boundaries[followingWordIndex] - boundaries[newWordIndex],
                            endPoint='end',
                        )
                    speech.speakTextInfo(newInfo, unit=textInfos.UNIT_WORD, reason=REASON_CARET)
                    newInfo.collapse()
                    newInfo.updateCaret()
                    return
                else:
                    # Next word will be found in the following paragraph
                    mylog("next para!")
                    lineInfo.collapse()
                    result = lineInfo.move(textInfos.UNIT_PARAGRAPH, direction)
                    if result == 0:
                        self.beeper.fancyBeep('HF', 100, left=25, right=25)
                        return
                    lineInfo.expand(textInfos.UNIT_PARAGRAPH)
                    # now try to find next word again on next/previous line
            #raise Exception('Failed to find next word')
            self.beeper.fancyBeep('HF', 100, left=25, right=25)
        except NotImplementedError as e:
            return onError(e)