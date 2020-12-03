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
import sayAllHandler
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
    confspec = {
        "overrideMoveByWord" : "boolean( default=True)",
        "enableInBrowseMode" : "boolean( default=True)",
        "leftControlAssignmentIndex": "integer( default=3, min=0, max=4)",
        "rightControlAssignmentIndex": "integer( default=1, min=0, max=4)",
        "leftControlWindowsAssignmentIndex": "integer( default=2, min=0, max=4)",
        "rightControlWindowsAssignmentIndex": "integer( default=4, min=0, max=4)",
        "bulkyWordPunctuation" : f"string( default='():')",
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
def generateWordRebulky(punctuation=None):
    if punctuation is None:
        punctuation = getConfig("bulkyWordPunctuation")
    punctuation = escapeRegex(punctuation)
    space = f"\\s{punctuation}"
    wordReBulkyString = f"$|(^|(?<=[{space}]))[^{space}]"
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
        return generateWordRebulky(),1
    elif index == 3:
        return wordReFine,1
    elif index == 4:
        return generateWordRebulky(), getConfig("wordCount")
    else:
        return None, None

class SettingsDialog(SettingsPanel):
    # Translators: Title for the settings dialog
    title = _("WordNav")
    controlAssignmentText = [
        _("Default NVDA word navigation"),
        _("Notepad++ style navigation"),
        _("Bulky word navigation"),
        _("Fine word navigation"),
        _("MultiWord navigation"),
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
        self.bulkyWordPunctuationEdit = gui.guiHelper.LabeledControlHelper(self, _("Bulky word separators:"), wx.TextCtrl).control
        self.bulkyWordPunctuationEdit.Value = getConfig("bulkyWordPunctuation")
      # MultiWord word count
        # Translators: Label for multiWord wordCount edit box
        self.wordCountEdit = gui.guiHelper.LabeledControlHelper(self, _("Word count for multiWord navigation:"), wx.TextCtrl).control
        self.wordCountEdit.Value = str(getConfig("wordCount"))

      # applicationsBlacklist edit
        # Translators: Label for blacklisted applications edit box
        self.applicationsBlacklistEdit = gui.guiHelper.LabeledControlHelper(self, _("Disable SentenceNav in applications (comma-separated list)"), wx.TextCtrl).control
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
        try:
            if 'leftArrow' == gesture.mainKeyName:
                direction = -1
            elif 'rightArrow' == gesture.mainKeyName:
                direction = 1
            else:
                return onError(None)
            mylog(f"direction={direction}")
            focus = api.getFocusObject()
            caretInfo = focus.makeTextInfo(textInfos.POSITION_CARET)
            caretInfo.collapse(end=(direction > 0))
            lineInfo = caretInfo.copy()
            lineInfo.expand(textInfos.UNIT_PARAGRAPH)
            offsetInfo = lineInfo.copy()
            offsetInfo.setEndPoint(caretInfo, 'endToEnd')
            caret = len(offsetInfo.text)
            for lineAttempt in range(100):
                lineText = lineInfo.text.rstrip('\r\n')
                mylog(f"lineAttempt={lineAttempt}; paragraph:")
                mylog(lineText)
                isEmptyLine = len(lineText.strip()) == 0
                boundaries = [m.start() for m in wordRe.finditer(lineText)]
                boundaries = sorted(list(set(boundaries)))
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
                        newInfo = caretInfo
                        newInfo.move(textInfos.UNIT_CHARACTER, adjustment)
                    else:
                        newInfo = lineInfo
                        adjustment =  boundaries[newWordIndex]
                        newInfo.collapse(end=False)
                        mylog(f"adjustment={adjustment}")
                        result = newInfo.move(textInfos.UNIT_CHARACTER, adjustment)
                    if newWordIndex + 1 < len(boundaries):
                        mylog("This is not the end of line word, so need to make a non-empty textInfo")
                        followingWordIndex = newWordIndex + wordCount
                        followingWordIndex = max(0, followingWordIndex)
                        followingWordIndex = min(followingWordIndex, len(boundaries) - 1)
                        newInfo.move(
                            textInfos.UNIT_CHARACTER,
                            boundaries[followingWordIndex] - boundaries[newWordIndex],
                            endPoint='end',
                        )
                    speech.speakTextInfo(newInfo, unit=textInfos.UNIT_WORD, reason=controlTypes.REASON_CARET)
                    newInfo.collapse()
                    newInfo.updateCaret()
                    return
                else:
                    # New word found in the next para!
                    mylog("Next para!")
                    lineInfo.collapse()
                    result = lineInfo.move(textInfos.UNIT_PARAGRAPH, direction)
                    if result == 0:
                        self.beeper.fancyBeep('HF', 100, left=25, right=25)
                        return
                    lineInfo.expand(textInfos.UNIT_PARAGRAPH)
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
                boundaries = [m.start() for m in wordRe.finditer(lineText)]
                boundaries = sorted(list(set(boundaries)))
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
                    speech.speakTextInfo(newInfo, unit=textInfos.UNIT_WORD, reason=controlTypes.REASON_CARET)
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