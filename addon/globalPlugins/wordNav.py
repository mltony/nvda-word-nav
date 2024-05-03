#A part of  WordNav addon for NVDA
#Copyright (C) 2020-2024 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import api
import bisect
import braille
import browseMode
import collections
import config
import controlTypes
import core
import copy
import ctypes
from ctypes import create_string_buffer, byref
import cursorManager
import documentBase
import eventHandler
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
from NVDAObjects.IAccessible.ia2TextMozilla import MozillaCompoundTextInfo 
from compoundDocuments import CompoundTextInfo
from NVDAObjects.window.scintilla import ScintillaTextInfo
import nvwave
import operator
import os
import re
from scriptHandler import script, willSayAllResume, isScriptWaiting
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
from dataclasses import dataclass
from appModules.devenv import VsWpfTextViewTextInfo
from NVDAObjects import behaviors
import weakref
from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.window.edit import ITextDocumentTextInfo
from textInfos.offsets import OffsetsTextInfo
from NVDAObjects.window.scintilla import ScintillaTextInfo
from NVDAObjects.window.scintilla import Scintilla
from NVDAObjects.UIA import UIATextInfo
from NVDAObjects.window.edit import EditTextInfo

try:
    REASON_CARET = controlTypes.REASON_CARET
except AttributeError:
    REASON_CARET = controlTypes.OutputReason.CARET



debug = False
if debug:
    import threading
    LOG_FILE_NAME = "C:\\Users\\tony\\1.txt"
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

INFINITY = 10**10
module = "wordNav"
def initConfiguration():
    defaultBulkyRegexp = r'$|(^|(?<=[\s\(\)]))[^\s\(\)]|\b(:\d+)+\b'
    confspec = {
        "overrideMoveByWord" : "boolean( default=True)",
        "enableInBrowseMode" : "boolean( default=True)",
        "enableSelection" : "boolean( default=True)",
        "selectTrailingSpace" : "boolean( default=False)",
        "leftControlAssignmentIndex": "integer( default=3, min=0, max=5)",
        "rightControlAssignmentIndex": "integer( default=1, min=0, max=5)",
        "leftControlWindowsAssignmentIndex": "integer( default=2, min=0, max=5)",
        "rightControlWindowsAssignmentIndex": "integer( default=4, min=0, max=5)",
        "bulkyWordPunctuation" : f"string( default='():')",
        "bulkyWordRegex" : f"string( default='{defaultBulkyRegexp}')",
        "bulkyWordEndRegex" : f"string( default='')",
        "paragraphChimeVolume" : "integer( default=5, min=0, max=100)",
        "wordCount": "integer( default=5, min=1, max=1000)",
        "applicationsBlacklist" : f"string( default='')",
        "disableInGoogleDocs" : "boolean( default=False)",
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
# 1. Empty string consisting of spaces or tabs but without any newline characters
wrEmpty = r"^(?=((?!\r|\n)\s)*$)"
# 2. Newline \r or \n characters
wrNewline = r"[\r\n]+"
# 3. Beginning of any word
wrWord = r"\b\w"
# 4. Punctuation mark preceded by non-punctuation mark: (?<=[\w\s])[^\w\s]
wrPunc = r"(?<=[\w\s])[^\w\s]"
# 5. Punctuation mark preceded by beginning of the string
wrPunc2 = r"^[^\w\s]"
wordReString = f"{wrEmpty}|{wrNewline}|{wrWord}|{wrPunc}|{wrPunc2}"
wordRe = re.compile(wordReString)

# word end regex - tweaking some clauses of word start regex
# 3. End of word
wrWordEnd = r"(?<=\w)\b"
# 4. non-Punctuation mark preceded by punctuation mark
wrPuncEnd = r"(?<=[^\w\s])[\w\s]"
# 5. End of string preceded by Punctuation mark
wrPunc2End = r"(?<=[^\w\s])$"

wordEndReString = f"{wrEmpty}|{wrNewline}|{wrWordEnd}|{wrPuncEnd}|{wrPunc2End}"
wordEndRe = re.compile(wordEndReString)


# Regular expression for beginning of fine word. This word definition breaks
# camelCaseIdentifiers  and underscore_separated_identifiers into separate sections for easier editing.
# Includes all conditions for wordRe plus additionally:
# 6. Word letter, that is not  underscore, preceded by underscore.
wfrLine = r"(?<=_)(?!_)\w"
# 7. Capital letter preceded by a lower-case letter.
wfrCap = r"(?<=[a-z])[A-Z]"
# 8. Digit followed by alphabetic character
wfrDigit = r"(?<=\d)[a-zA-Z]"
#wfrDigit2 = r"(?<=[a-zA-Z])\d"
wordReFineString = f"{wordReString}|{wfrLine}|{wfrCap}|{wfrDigit}"
wordReFine = re.compile(wordReFineString)
wordFineEndReString = f"{wordEndReString}|{wfrLine}|{wfrCap}|{wfrDigit}"
wordFineEndRe = re.compile(wordFineEndReString)

# Regular expression for bulky words. Treats any punctuation signs as part of word.
# Matches either:
# 1. Empty string, or
# 2. End of string, or
# 3.     Non-space character preceded either by beginning of the string or a space character.
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
    #space = f"\\s{punctuation}"
    #wordReBulkyString = f"(^|(?<=[{space}]))[^{space}]|[\r\n]+"
    sw = r"(^|(?<=\s))\w"
    ws = r"(?<=\w)(\s|$)"
    sp = r"(^|(?<=\s))[%s]" % punctuation
    ps = r"(?<=[%s])(\s|$)" % punctuation
    pw = r"(?<=[%s])\w" % punctuation
    wordReBulkyString = f"{wrEmpty}|{wrNewline}|{sw}|{sp}|{pw}"
    wordReBulky = re.compile(wordReBulkyString)
    wordEndReBulkyString = f"{wrEmpty}|{wrNewline}|{ws}|{ps}|{pw}"
    wordEndReBulky = re.compile(wordEndReBulkyString)
    return wordReBulky, wordEndReBulky

def generateWordReCustom():
    wordReBulkyString = getConfig("bulkyWordRegex")
    wordReBulky = re.compile(wordReBulkyString)
    wordEndReBulkyString = getConfig("bulkyWordEndRegex")
    if len(wordEndReBulkyString) > 0:
        wordEndReBulky = re.compile(wordEndReBulkyString)
    else:
        wordEndReBulky = wordReBulky
    return wordReBulky, wordEndReBulky

# These constants map command assignment combo box index to actual functions
# w stands for navigate by word
# b and f stand for navigate by bulky/fine word
# 0 stands for unassigned
leftControlFunctions = "wwwwwbfwwbf"
rightControlFunctions = "wwwbfwwbfww"
controlWindowsFunctions = "0bf0000fbfb"

def getRegexByFunction(index):
    if index == 1:
        return wordRe, wordEndRe, 1
    elif index == 2:
        return generateWordReBulky()+ (1,)
    elif index == 3:
        return wordReFine, wordFineEndRe, 1
    elif index == 4:
        return generateWordReBulky(), None, getConfig("wordCount")
    elif index == 5:
        return generateWordReCustom() + (1,)
    else:
        return None, None, None

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
      # checkbox enableSelection
        label = _("Enable WordNav word selection")
        self.selectTrailingSpaceCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.selectTrailingSpaceCheckbox.Value = getConfig("enableSelection")
      # checkbox select trailing space
        label = _("Include trailing space when selecting words with control+shift+rightArrow")
        self.enableSelectionCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.enableSelectionCheckbox.Value = getConfig("selectTrailingSpace")
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

      # Custom word regex
        self.customWordRegexEdit = sHelper.addLabeledControl(_("Custom word regular expression:"), wx.TextCtrl)
        self.customWordRegexEdit.Value = getConfig("bulkyWordRegex")
      # Custom word end regex
        self.customWordEndRegexEdit = sHelper.addLabeledControl(_("Optional Custom word end regular expression for word selection:"), wx.TextCtrl)
        self.customWordEndRegexEdit.Value = getConfig("bulkyWordEndRegex")
      # MultiWord word count
        # Translators: Label for multiWord wordCount edit box
        self.wordCountEdit = sHelper.addLabeledControl(_("Word count for multiWord navigation:"), wx.TextCtrl)
        self.wordCountEdit.Value = str(getConfig("wordCount"))
      # paragraphChimeVolumeSlider
        # Translators: Paragraph crossing chime volume
        label = _("Volume of chime when crossing paragraph border")
        self.paragraphChimeVolumeSlider = sHelper.addLabeledControl(label, wx.Slider, minValue=0,maxValue=100)
        self.paragraphChimeVolumeSlider.SetValue(getConfig("paragraphChimeVolume"))

      # applicationsBlacklist edit
        # Translators: Label for blacklisted applications edit box
        self.applicationsBlacklistEdit = sHelper.addLabeledControl(_("Disable WordNav in applications (comma-separated list)"), wx.TextCtrl)
        self.applicationsBlacklistEdit.Value = getConfig("applicationsBlacklist")
      # checkbox Disable in Google Docs
        label = _("Disable in Google Docs")
        self.DisableInGoogleDocsCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.DisableInGoogleDocsCheckbox.Value = getConfig("disableInGoogleDocs")

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
        setConfig("enableSelection", self.enableSelectionCheckbox.Value)
        setConfig("selectTrailingSpace", self.selectTrailingSpaceCheckbox.Value)
        setConfig("leftControlAssignmentIndex", self.leftControlAssignmentCombobox.Selection)
        setConfig("rightControlAssignmentIndex", self.rightControlAssignmentCombobox.Selection)
        setConfig("leftControlWindowsAssignmentIndex", self.leftControlWindowsAssignmentCombobox.Selection)
        setConfig("rightControlWindowsAssignmentIndex", self.rightControlWindowsAssignmentCombobox.Selection)
        setConfig("bulkyWordPunctuation", self.bulkyWordPunctuationEdit.Value)
        setConfig("bulkyWordRegex", self.customWordRegexEdit.Value)
        setConfig("bulkyWordEndRegex", self.customWordEndRegexEdit.Value)
        setConfig("wordCount", int(self.wordCountEdit.Value))
        setConfig("paragraphChimeVolume", self.paragraphChimeVolumeSlider.Value)
        setConfig("applicationsBlacklist", self.applicationsBlacklistEdit.Value)
        setConfig("disableInGoogleDocs", self.DisableInGoogleDocsCheckbox.Value)



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

originalExecuteGesture = None
globalGestureCounter = 0
def preExecuteGesture(self, gesture):
    global globalGestureCounter
    globalGestureCounter += 1
    return originalExecuteGesture(self, gesture)
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


controlModifiers = [
    winUser.VK_LCONTROL, winUser.VK_RCONTROL,
    winUser.VK_LSHIFT, winUser.VK_RSHIFT,
    winUser.VK_LMENU, winUser.VK_RMENU,
    winUser.VK_LWIN, winUser.VK_RWIN,
]
kbdRight = keyboardHandler.KeyboardInputGesture.fromName("RightArrow")
kbdLeft = keyboardHandler.KeyboardInputGesture.fromName("LeftArrow")

def areModifiersReleased():
    status = [
        winUser.getKeyState(k) & 32768
        for k in controlModifiers
    ]
    return not any(status)
    
def asyncUpdateNotepadPPCursorWhenModifiersReleased(doRight, localGestureCounter):
    global globalGestureCounter
    while not areModifiersReleased():
        if localGestureCounter != globalGestureCounter:
            return
        yield 10
    sequence = [kbdLeft, kbdRight]
    if doRight:
        sequence = sequence[::-1]
    for keystroke in sequence:
        keystroke.send()


def isBlacklistedApp(self):
    focus = self
    appName = focus.appModule.appName
    if appName.lower() in getConfig("applicationsBlacklist").lower().strip().split(","):
        return True
    return False


def getUrl(obj):
    if not isinstance(obj, IAccessible):
        return None
    url = None
    o = obj
    while o is not None:
        try:
            tag = o.IA2Attributes["tag"]
        except AttributeError:
            break
        except KeyError:
            o = o.simpleParent
            continue
        if tag in [
            "#document", # for Chrome
            "body", # For Firefox
        ]:
            thisUrl = o.IAccessibleObject.accValue(o.IAccessibleChildID)
            if thisUrl is not None and thisUrl.startswith("http"):
                url = thisUrl
        o = o.simpleParent
    return url

urlCache = weakref.WeakKeyDictionary()
def getUrlCached(interceptor, obj):
    try:
        result = urlCache[interceptor]
        if result is not None:
            return result
    except KeyError:
        pass
    url = getUrl(obj)
    if url is not None and url.startswith("http"):
        urlCache[interceptor] = url
    return url

def getModifiers(gesture):
    control = None
    windows = False
    for modVk, modExt in gesture.modifiers:
        if modVk == winUser.VK_LCONTROL:
            control = 'left'
        if modVk == winUser.VK_RCONTROL:
            control = 'right'
        if False:
            if not modExt:
                # Left control
                control = "left"
            else:
                # Right control
                control = "right"
        if modVk in [winUser.VK_LWIN, winUser.VK_RWIN]:
            windows = True
    if control is None:
        raise Exception("Control is not pressed - please don't reassign WordNav keystrokes!")
    result = control + "Control"
    if windows:
        result += "Windows"
    return result


def isGoogleDocs(obj):
    role = obj.role
    if role != controlTypes.Role.EDITABLETEXT:
        return False
    interceptor = obj.treeInterceptor
    if interceptor is None:
        return False
    url = getUrlCached(interceptor, obj)
    if url is None:
        return False
    if not url.startswith("https://docs.google.com/document/"):
        return False
    return True

def isVscodeApp(self):
    try:
        if self.treeInterceptor is not None:
            return False
    except NameError:
        return False
    return self.appModule.productName.startswith("Visual Studio Code")

def isVSCodeMainEditor(obj):
    if obj.role != controlTypes.Role.EDITABLETEXT:
        return False
    def findLandmark(obj):
        simpleParent = obj.simpleParent
        if simpleParent.role == controlTypes.Role.LANDMARK:
            return simpleParent
        while True:
            obj = obj.parent
            if obj is None:
                return None
            if obj.role == controlTypes.Role.LANDMARK:
                return obj

    landmark = findLandmark(obj)
    if landmark is None:
        return False
    try:
        return landmark.IA2Attributes['id'] == 'workbench.parts.editor'
    except (KeyError, AttributeError):
        return False

def makeVSCodeTextInfo(obj, position):
    try:
        textInfo = obj.makeEnhancedTextInfo(position)
    except AttributeError:
        errorMsg = _(
            "Error: in order for word navigation to work correctly in VSCode, please install the following:\n"
            "1. NVDA add-on IndentNav version v2.0 or later.\n"
            "2. VSCode extension: Accessibility for NVDA IndentNav.\n"
            "Please consult WordNav Readme file for more information."
        )
        wx.CallAfter(gui.messageBox, errorMsg, _("WordNav error"), wx.OK|wx.ICON_WARNING)
        return None
    if textInfo is None:
        errorMsg = _(
            "Error: in order for word navigation to work correctly in VSCode, please install the following:\n"
            "1. NVDA add-on IndentNav version v2.0 or later.\n"
            "2. VSCode extension: Accessibility for NVDA IndentNav.\n"
            "IndentNav add-on has been detected; but VSCode extension does not appear to be running..\n"
            "Please consultf WordNav Readme file for more information."
        )
        wx.CallAfter(gui.messageBox, errorMsg, _("WordNav error"), wx.OK|wx.ICON_WARNING)
        return None
    return textInfo


def script_caret_moveByWordWordNav(self,gesture):
    mods = getModifiers(gesture)
    key = gesture.mainKeyName
    isBrowseMode = isinstance(self, browseMode.BrowseModeDocumentTreeInterceptor)
    isEnabled = getConfig("enableInBrowseMode" if isBrowseMode else "overrideMoveByWord")
    obj = self.rootNVDAObject if isBrowseMode else self
    blacklisted = isBlacklistedApp(obj)
    gd = isGoogleDocs(obj)
    disableGd = gd if getConfig("disableInGoogleDocs") else False
    if not isBrowseMode:
        isVSCode = isVscodeApp(obj)
        if isVSCode:
            isVSCodeMain = isVSCodeMainEditor(obj)
    else:
        isVSCode = False
    option = f"{mods}AssignmentIndex"
    pattern, patternEnd, wordCount = getRegexByFunction(getConfig(option))
    if (
        not isEnabled
        or pattern is None
        or blacklisted
        or disableGd
        or (isVSCode and not isVSCodeMain)
    ):
        if 'Windows' not in mods:
            if isBrowseMode:
                if key == "rightArrow":
                    return cursorManager.CursorManager.script_moveByWord_forward(self, gesture)
                else:
                    return cursorManager.CursorManager.script_moveByWord_back(self, gesture)
            else:
                return editableText.EditableText.script_caret_moveByWord(self, gesture)
        else:
            gesture.send()
        return
    direction = 1 if "rightArrow" in key else -1
    if isVSCode:
        caretInfo = makeVSCodeTextInfo(self, textInfos.POSITION_CARET)
        if caretInfo is None:
            chimeNoNextWord()
            return
    else:
        caretInfo = self.makeTextInfo(textInfos.POSITION_CARET)
    doWordMove(caretInfo, pattern, direction, wordCount)



beeper = Beeper()
def chimeCrossParagraphBorder():
    volume = getConfig("paragraphChimeVolume")
    beeper.fancyBeep("AC#EG#", 30, volume, volume)

def chimeNoNextWord():
    volume = 25
    beeper.fancyBeep('HF', 100, left=volume, right=volume)

def getParagraphUnit(textInfo):
    if isinstance(textInfo, VsWpfTextViewTextInfo):
        # TextInfo in Visual Studio doesn't understand UNIT_PARAGRAPH
        return textInfos.UNIT_LINE
    # In Windows 11 Notepad, we should use UNIT_PARAGRAPH instead of UNIT_LINE in order to handle wrapped lines correctly
    return textInfos.UNIT_PARAGRAPH


def _moveToNextParagraph(
        paragraph: textInfos.TextInfo,
        direction: int,
) -> bool:
    paragraphUnit = getParagraphUnit(paragraph)
    oldParagraph = paragraph.copy()
    if direction > 0:
        try:
            paragraph.collapse(end=True)
        except RuntimeError:
            # Microsoft Word raises RuntimeError when collapsing textInfo to the last character of the document.
            return False
    else:
        paragraph.collapse(end=False)
        result = paragraph.move(textInfos.UNIT_CHARACTER, -1)
        if result == 0:
            return False
    paragraph.expand(paragraphUnit)
    #if paragraph.isCollapsed:
        #return False
    if (
        direction > 0
        and paragraph.compareEndPoints(oldParagraph, "startToStart") <= 0
    ):
        # Sometimes in Microsoft word it just selects the same last paragraph repeatedly
        return False
    return True


class MoveToCodePointOffsetError(Exception):
    pass


def moveToCodePointOffset(textInfo, offset):
    exceptionMessage = "Unable to find desired offset in TextInfo."
    try:
        return textInfo.moveToCodepointOffset(offset)
    except RuntimeError as e:
        if str(e) == exceptionMessage:
            raise MoveToCodePointOffsetError(e)
        else:
            raise e

def doWordMove(caretInfo, pattern, direction, wordCount=1):
    paragraphUnit = getParagraphUnit(caretInfo)
    if not caretInfo.isCollapsed:
        raise RuntimeError("Caret must be collapsed")
    paragraphInfo = caretInfo.copy()
    paragraphInfo.expand(paragraphUnit)
    pretextInfo = paragraphInfo.copy()
    pretextInfo.setEndPoint(caretInfo, 'endToEnd')
    caretOffset = len(pretextInfo.text)
    crossedParagraph = False
    MAX_ATTEMPTS = 10
    for attempt in range(MAX_ATTEMPTS):
        text = paragraphInfo.text
        mylog(f"attempt! {caretOffset=} n={len(text)} {text=}")
        stops = [
            m.start()
            for m in pattern.finditer(text)
        ]
        # dedupe:
        stops = sorted(list(set(stops)))
        #while len(stops) > 0:
        while True:
            mylog(f"wt {stops=}")
            if direction > 0:
                newWordIndex = bisect.bisect_right(stops, caretOffset)
            else:
                newWordIndex = bisect.bisect_left(stops, caretOffset) - 1
            mylog(f"{newWordIndex=}")
            if 0 <= newWordIndex < len(stops):
                # Next word found in the same paragraph
                # We will move to it unless moveToCodePointOffset fails, in which case we'll have to drop that stop and repeat the inner while loop again.
                mylog(f"Same Para!")
                if attempt == 0 and wordCount > 1:
                    # newWordIndex at this point already implies that we moved by 1 word. If requested to move by wordCount words, need to move by (wordCount - 1) more.
                    newWordIndex += (wordCount - 1) * direction
                    newWordIndex = max(0, newWordIndex)
                    newWordIndex = min(newWordIndex, len(stops) - 1)
                newCaretOffset = stops[newWordIndex]
                try:
                    wordEndOffset = stops[newWordIndex + wordCount]
                    wordEndIsParagraphEnd = False
                except IndexError:
                    wordEndOffset = len(text)
                    wordEndIsParagraphEnd = True
                mylog(f"resultWordOffsets: {newCaretOffset}..{wordEndOffset}")
                #newCaretInfo = paragraphInfo.moveToCodepointOffset(newCaretOffset)
                #wordEndInfo = paragraphInfo.moveToCodepointOffset(wordEndOffset)
                try:
                    newCaretInfo = moveToCodePointOffset(paragraphInfo, newCaretOffset)
                except MoveToCodePointOffsetError:
                    # This happens in MSWord when trying to navigate over bulleted list item.
                    mylog(f"Oops cannot move to word start offset={newCaretOffset} - deleting stops[{newWordIndex}]={stops[newWordIndex]}")
                    del stops[newWordIndex]
                    continue #inner loop
                if newCaretInfo.compareEndPoints(caretInfo, "startToStart") == 0:
                    if direction < 0:
                        mylog(f"Oh no, caret didn't move at all when moving backward. offset={newCaretOffset} - deleting stops[{newWordIndex}]={stops[newWordIndex]}")
                        # This happens in MSWord with UIA enabled when trying to move over a bulleted list item.
                        del stops[newWordIndex]
                        continue #inner loop
                    else:
                        # This has never been observed yet.
                        raise RuntimeError(f"Cursor didn't move {direction=}")
                try:
                    wordEndInfo = moveToCodePointOffset(paragraphInfo, wordEndOffset)
                except MoveToCodePointOffsetError as e:
                    mylog(f"Oops cannot move to word end offset={wordEndOffset} - deleting stops[{newWordIndex + wordCount}]={stops[newWordIndex + wordCount]}")
                    if wordEndIsParagraphEnd:
                        raise RuntimeError("moveToCodePointOffset unexpectedly failed to move to the end of paragraph", e)
                    del stops[newWordIndex + wordCount]
                    continue # inner loop
                wordInfo = newCaretInfo.copy()
                wordInfo.setEndPoint(wordEndInfo, "endToEnd")
                newCaretInfo.updateCaret()
                if isinstance(newCaretInfo, MozillaCompoundTextInfo):
                    # Google Chrome needs to be told twice
                    newCaretInfo.updateCaret()
                if isinstance(newCaretInfo, ScintillaTextInfo):
                    # Notepad++ doesn't remember cursor position when updated from here and then navigating by line up or down
                    # This hack makes it remember new position
                    executeAsynchronously(asyncUpdateNotepadPPCursorWhenModifiersReleased(True, globalGestureCounter))
                speech.speakTextInfo(wordInfo, unit=textInfos.UNIT_WORD, reason=REASON_CARET)
                if crossedParagraph:
                    chimeCrossParagraphBorder()
                return
            else:
                # New word found in the next paragraph!
                mylog(f"Next Para!")
                crossedParagraph = True
                if not _moveToNextParagraph(paragraphInfo, direction):
                    chimeNoNextWord()
                    return
                if direction > 0:
                    caretOffset = -1
                else:
                    caretOffset = INFINITY
                # Now break out of inner while loop and iterate the outer loop one more time
                break

doWordMove.__doc__ = _("WordNav move by word")
doWordMove.category = _("WordNav")

globalCaretAheadOfAnchor = {}
def updateSelection(anchorInfo, newCaretInfo):
    """
        There is no good unified way in NVDA to set selection preserving anchor location.
        Some implementations always put caret in the front, others always put caret in the back.
        We neeed to do it dynamically, depending on whether the user selects back or forward.
        UIA and plain Windows edit controls always put caret at the end, so we need to make use of fake caret trick:
        we just memorize where the caret is supposed to be and override selectByCharacter commands to also use that fake caret.
        IAccessible2 doesn't allow setting selection across paragraphs and there is nothing we fcan do to work around.
        Here be dragons.
    """
    caretAheadOfAnchor = newCaretInfo.compareEndPoints(anchorInfo, "startToStart") < 0
    try:
        hwnd = newCaretInfo._obj().windowHandle
        globalCaretAheadOfAnchor[hwnd] = caretAheadOfAnchor
    except AttributeError:
        pass
    isBrowseMode = isinstance(newCaretInfo._obj(), browseMode.BrowseModeDocumentTreeInterceptor)
    spanInfo = anchorInfo.copy()
    spanInfo.setEndPoint(newCaretInfo, 'startToStart' if caretAheadOfAnchor else 'endToEnd')
    if isBrowseMode:
        newCaretInfo._obj().isTextSelectionAnchoredAtStart = not caretAheadOfAnchor
        spanInfo.updateSelection()
    elif isinstance(newCaretInfo, ITextDocumentTextInfo):
        # This textInfo is used in many plain editables. Examples include:
        # NVDA Log Viewer
        # Windows+R run dialog
        import comInterfaces.tom
        #newCaretInfo.obj.ITextSelectionObject.MoveRight(comInterfaces.tom.tomCharacter, 1, comInterfaces.tom.tomExtend)
        caretOffset = newCaretInfo._rangeObj.start
        anchorOffset = anchorInfo._rangeObj.start
        newCaretInfo.obj.ITextSelectionObject.SetRange(anchorOffset, caretOffset)
    
    elif isinstance(newCaretInfo, CompoundTextInfo):
        innerAnchor = anchorInfo._start.copy()
        innerCaret = newCaretInfo._start.copy()
        if caretAheadOfAnchor:
            spanInfo._startObj.setFocus()
            innerTmpCaret = spanInfo._end.copy()
            innerTmpCaret.collapse(end=False)
            innerTmpAnchor = spanInfo._start.copy()
            innerTmpAnchor.collapse(end=True)
        else:
            spanInfo._endObj.setFocus()
            innerTmpCaret = spanInfo._start.copy()
            innerTmpCaret.collapse(end=True)
            innerTmpAnchor = spanInfo._end.copy()
            innerTmpAnchor.collapse(end=False)
        updateSelection(innerAnchor, innerTmpCaret)
        if spanInfo._start is not spanInfo._end:
            updateSelection(innerTmpAnchor, innerCaret)
    elif isinstance(newCaretInfo, OffsetsTextInfo):
        if caretAheadOfAnchor:
            # Hacking an invalid textInfo by swapping start and end
            tmp = spanInfo._startOffset
            spanInfo._startOffset = spanInfo._endOffset
            spanInfo._endOffset = tmp
        spanInfo.updateSelection()
    elif isinstance(newCaretInfo, UIATextInfo):
        # UIA sucks and doesn't allow to set caret at the front of selection
        # fakeCursor mode will kindof take care of that
        spanInfo.updateSelection()
    else:
        raise RuntimeError(f"Don't know how to set selection for textInfo of type {type(newCaretInfo).__name__}")

# This function was copied from EditableTextWithoutAutoSelectDetection.reportSelectionChange()
def reportSelectionChange(self, oldTextInfo):
	api.processPendingEvents(processEventQueue=False)
	newInfo=self.makeTextInfo(textInfos.POSITION_SELECTION)
	self._updateSelectionAnchor(oldTextInfo,newInfo)
	speech.speakSelectionChange(oldTextInfo,newInfo)
	braille.handler.handleCaretMove(self)

def restoreAutoDetectSelection(counter, timeoutMs, obj):
    global globalSelectByWordCounter
    yield timeoutMs
    if globalSelectByWordCounter != counter:
        return
    obj._autoSelectDetectionEnabled = True
    obj._autoSelectDetectionTemporarilyDisabled = False


def isFakeCaretMode(caretInfo):
    return isinstance(caretInfo, (UIATextInfo, EditTextInfo))

globalSelectByWordCounter = 0
def script_selectByWordWordNav(self,gesture):
    global globalSelectByWordCounter
    globalSelectByWordCounter += 1
    mods = getModifiers(gesture)
    key = gesture.mainKeyName
    isBrowseMode = isinstance(self, browseMode.BrowseModeDocumentTreeInterceptor)
    isEnabled = getConfig("enableSelection")
    isNpp = isinstance(self, Scintilla)
    obj = self.rootNVDAObject if isBrowseMode else self
    blacklisted = isBlacklistedApp(obj)
    gd = isGoogleDocs(obj)
    disableGd = gd if getConfig("disableInGoogleDocs") else False
    if not isBrowseMode:
        isVSCode = isVscodeApp(obj)
        if isVSCode:
            isVSCodeMain = isVSCodeMainEditor(obj)
    else:
        isVSCode = False
    option = f"{mods}AssignmentIndex"
    pattern, patternEnd, wordCount = getRegexByFunction(getConfig(option))
    if (
        not isEnabled
        or pattern is None
        or blacklisted
        or disableGd
        or (isVSCode and not isVSCodeMain)
    ):
        if 'Windows' not in mods:
            if isBrowseMode:
                if key == "rightArrow":
                    return cursorManager.CursorManager.script_moveByWord_forward(self, gesture)
                else:
                    return cursorManager.CursorManager.script_moveByWord_back(self, gesture)
            else:
                try:
                    return self.editableText.EditableText.script_caret_changeSelection(self, gesture)
                except AttributeError:
                    pass
        gesture.send()
        return
    direction = -1 if "leftArrow" in key else 1
    selectTrailingSpace = key not in ["leftArrow", "rightArrow"]
    if getConfig("selectTrailingSpace"):
        selectTrailingSpace = not selectTrailingSpace
    if selectTrailingSpace:
        patternEnd = pattern
    if isVSCode:
        caretInfo = makeVSCodeTextInfo(self, textInfos.POSITION_CARET)
        if caretInfo is None:
            chimeNoNextWord()
            return
        selectionInfo = makeVSCodeTextInfo(self, textInfos.POSITION_SELECTION)
        oldInfo = self.makeTextInfo(textInfos.POSITION_SELECTION)
    else:
        caretInfo = self.makeTextInfo(textInfos.POSITION_CARET)
        selectionInfo = self.makeTextInfo(textInfos.POSITION_SELECTION)
        oldInfo = selectionInfo.copy()
    fakeCaretMode = isFakeCaretMode(caretInfo)
    if isBrowseMode or fakeCaretMode:
        if isBrowseMode:
            caretAheadOfAnchor = not self.isTextSelectionAnchoredAtStart 
        else:
            hwnd = obj.windowHandle
            caretAheadOfAnchor = globalCaretAheadOfAnchor.get(hwnd, False)
        caretInfo = selectionInfo.copy()
        caretInfo.collapse(end=not caretAheadOfAnchor)
    if not caretInfo.isCollapsed:
        raise RuntimeError("Caret must be collapsed")
    anchorInfo = selectionInfo.copy()
    if selectionInfo.compareEndPoints(caretInfo, 'startToStart') == 0:
        anchorInfo.collapse(end=True)
    elif selectionInfo.compareEndPoints(caretInfo, 'endToEnd') == 0:
        anchorInfo.collapse(end=False)
    else:
        raise RuntimeError("Caretmust be at the beginning or at the end of selection")
    doWordSelect(caretInfo, anchorInfo, pattern, patternEnd, direction, wordCount)
    if isScriptWaiting() or eventHandler.isPendingEvents("gainFocus"):
        return
    if isNpp:
        # For some reason NPP bounceback messages regarding selection updates come in delayed.
        # Overriding this behavior and speaking updates manually.
        if self._autoSelectDetectionEnabled or getattr(self, '_autoSelectDetectionTemporarilyDisabled', False):
            self._autoSelectDetectionEnabled = False
            self._autoSelectDetectionTemporarilyDisabled = True
            executeAsynchronously(restoreAutoDetectSelection(globalSelectByWordCounter, 500, self))
            self._lastSelectionPos = self.makeTextInfo(textInfos.POSITION_SELECTION)
        reportSelectionChange(self, oldInfo)
    try:
        self.reportSelectionChange(oldInfo)
    except Exception:
        #log.exception("badaboom")
        return

def doWordSelect(caretInfo, anchorInfo, wordBeginPattern, wordEndPattern, direction, wordCount=1):
    paragraphUnit = getParagraphUnit(caretInfo)
    if not caretInfo.isCollapsed:
        raise RuntimeError("Caret must be collapsed")
    if not anchorInfo.isCollapsed:
        raise RuntimeError("anchor must be collapsed")
    paragraphInfo = caretInfo.copy()
    paragraphInfo.expand(paragraphUnit)
    pretextInfo = paragraphInfo.copy()
    pretextInfo.setEndPoint(caretInfo, 'endToEnd')
    caretOffset = len(pretextInfo.text)
    crossedParagraph = False
    MAX_ATTEMPTS = 10
    for attempt in range(MAX_ATTEMPTS):
        # anchorDirection tells us where anchor lies compared to current textInfo - in current paragraph, or before or after
        # anchorOffset represents offset within current paragraph, or some convenient fake values like -1 and 10**10 if it lies ouside of current paragraph.
        if paragraphInfo.compareEndPoints(anchorInfo, 'startToStart') > 0:
            anchorDirection = -1
            anchorOffset = -1
        elif paragraphInfo.compareEndPoints(anchorInfo, 'endToEnd') <= 0:
            anchorDirection = 1
            anchorOffset = INFINITY
        else:
            anchorDirection = 0
            preAnchorInfo = anchorInfo.copy()
            preAnchorInfo.setEndPoint(paragraphInfo, 'startToStart')
            anchorOffset = len(preAnchorInfo.text)
        text = paragraphInfo.text
        mylog(f"attempt! {caretOffset=} n={len(text)} {text=}")
        wordBeginStops = [
            m.start()
            for m in wordBeginPattern.finditer(text)
        ]
        wordEndStops = [
            m.start()
            for m in wordEndPattern.finditer(text)
        ]
        stops = [
            x for x in wordBeginStops if x <= anchorOffset
        ] + [
            x for x in wordEndStops if x >= anchorOffset
        ]
        # dedupe:
        stops = sorted(list(set(stops)))
        while True:  # inner loop
            mylog(f"wt {stops=}")
            if direction > 0:
                newWordIndex = bisect.bisect_right(stops, caretOffset)
            else:
                newWordIndex = bisect.bisect_left(stops, caretOffset) - 1
            mylog(f"{newWordIndex=}")
            if 0 <= newWordIndex < len(stops):
                # Next stop for selection found in current paragraph
                # We will move to it unless moveToCodePointOffset fails, in which case we'll have to drop that stop and repeat the inner while loop again.
                mylog(f"Same Para!")
                if attempt == 0 and wordCount > 1:
                    # newWordIndex at this point already implies that we moved by 1 word. If requested to move by wordCount words, need to move by (wordCount - 1) more.
                    newWordIndex += (wordCount - 1) * direction
                    newWordIndex = max(0, newWordIndex)
                    newWordIndex = min(newWordIndex, len(stops) - 1)
                newCaretOffset = stops[newWordIndex]
                mylog(f"resultWordOffset: {newCaretOffset}")
                try:
                    newCaretInfo = moveToCodePointOffset(paragraphInfo, newCaretOffset)
                except MoveToCodePointOffsetError:
                    # This happens in MSWord when trying to navigate over bulleted list item.
                    mylog(f"Oops cannot move to word start offset={newCaretOffset} - deleting stops[{newWordIndex}]={stops[newWordIndex]}")
                    del stops[newWordIndex]
                    continue #inner loop
                if newCaretInfo.compareEndPoints(caretInfo, "startToStart") == 0:
                    if direction < 0:
                        mylog(f"Oh no, caret didn't move at all when moving backward. offset={newCaretOffset} - deleting stops[{newWordIndex}]={stops[newWordIndex]}")
                        # This happens in MSWord with UIA enabled when trying to move over a bulleted list item.
                        del stops[newWordIndex]
                        continue #inner loop
                    else:
                        # This has never been observed yet.
                        raise RuntimeError(f"Cursor didn't move {direction=}")
                return updateSelection(anchorInfo, newCaretInfo)
            else:
                # New stop found in the next paragraph!
                mylog(f"Next Para!")
                crossedParagraph = True
                if not _moveToNextParagraph(paragraphInfo, direction):
                    chimeNoNextWord()
                    return
                if direction > 0:
                    caretOffset = -1
                else:
                    caretOffset = INFINITY
                # Now break out of inner while loop and iterate the outer loop one more time
                break

def script_selectByCharacterWordNav(self,gesture):
    selectionInfo = self.makeTextInfo(textInfos.POSITION_SELECTION)
    fakeCaretMode = isFakeCaretMode(selectionInfo)
    if not fakeCaretMode:
        try:
            return self.script_caret_changeSelection(gesture)
        except AttributeError:
            return gesture.send()
    key = gesture.mainKeyName
    direction = -1 if "leftArrow" in key else 1
    hwnd = self.windowHandle
    caretAheadOfAnchor = globalCaretAheadOfAnchor.get(hwnd, False)
    caretInfo = selectionInfo.copy()
    caretInfo.collapse(end=not caretAheadOfAnchor)
    anchorInfo = selectionInfo.copy()
    anchorInfo.collapse(end=caretAheadOfAnchor)
    result = caretInfo.move(textInfos.UNIT_CHARACTER, direction)
    if result == 0:
        return chimeNoNextWord()
    updateSelection(anchorInfo, caretInfo)

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
      # EditableText movement
        editableText.EditableText.script_caret_moveByWordWordNav = script_caret_moveByWordWordNav
        editableText.EditableText._EditableText__gestures["kb:control+leftArrow"] = "caret_moveByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+rightArrow"] = "caret_moveByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+Windows+leftArrow"] = "caret_moveByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+Windows+rightArrow"] = "caret_moveByWordWordNav"
        behaviors.EditableText._EditableText__gestures["kb:control+leftArrow"] = "caret_moveByWordWordNav"
        behaviors.EditableText._EditableText__gestures["kb:control+rightArrow"] = "caret_moveByWordWordNav"
      # EditableText word selection
        editableText.EditableText.script_selectByWordWordNav = script_selectByWordWordNav
        editableText.EditableText._EditableText__gestures["kb:control+leftArrow+shift"] = "selectByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+rightArrow+shift"] = "selectByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+numpad1+shift"] = "selectByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+Windows+leftArrow+shift"] = "selectByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+Windows+rightArrow+shift"] = "selectByWordWordNav"
        editableText.EditableText._EditableText__gestures["kb:control+Windows+numpad1+shift"] = "selectByWordWordNav"
      # EditableText character selection
        editableText.EditableText.script_selectByCharacterWordNav = script_selectByCharacterWordNav
        editableText.EditableText._EditableText__gestures["kb:leftArrow+shift"] = "selectByCharacterWordNav"
        editableText.EditableText._EditableText__gestures["kb:rightArrow+shift"] = "selectByCharacterWordNav"
      # CursorManager word movement
        cursorManager.CursorManager.script_caret_moveByWordWordNav = script_caret_moveByWordWordNav
        cursorManager.CursorManager._CursorManager__gestures["kb:control+leftArrow"] = "caret_moveByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+rightArrow"] = "caret_moveByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+leftArrow"] = "caret_moveByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+rightArrow"] = "caret_moveByWordWordNav"
      # CursorManager word selection
        cursorManager.CursorManager.script_selectByWordWordNav = script_selectByWordWordNav
        cursorManager.CursorManager._CursorManager__gestures["kb:control+leftArrow+shift"] = "selectByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+rightArrow+shift"] = "selectByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+leftArrow+shift"] = "selectByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+rightArrow+shift"] = "selectByWordWordNav"
      # inputManager.executeGesture
        global originalExecuteGesture
        originalExecuteGesture = inputCore.InputManager.executeGesture
        inputCore.InputManager.executeGesture = preExecuteGesture



    def  removeHooks(self):
        pass
