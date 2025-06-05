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
from NVDAObjects.behaviors import Terminal
import NVDAObjects.IAccessible.chromium
from NVDAObjects.IAccessible import IA2TextTextInfo
import treeInterceptorHandler
from comtypes import COMError

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
# 1a. Empty string consisting of spaces or tabs but without any newline characters (used in browse mode)
wrEmpty = r"^(?=((?!\r|\n)\s)*$)"
# 1b. Or, End of line that is not preceded by any newline characters (for editables)
wrEol= r"(?<!\r|\n)$"
# 2. Newline \r or \n characters
wrNewline = r"[\r\n]+"
# 3. Beginning of any word
wrWord = r"\b\w"
# 4. Punctuation mark preceded by non-punctuation mark: (?<=[\w\s])[^\w\s]
wrPunc = r"(?<=[\w\s])[^\w\s]"
# 5. Punctuation mark preceded by beginning of the string
wrPunc2 = r"^[^\w\s]"

# word end regex - tweaking some clauses of word start regex
# 3. End of word
wrWordEnd = r"(?<=\w)\b"
# 4. non-Punctuation mark preceded by punctuation mark
wrPuncEnd = r"(?<=[^\w\s])[\w\s]"
# 5. End of string preceded by Punctuation mark
wrPunc2End = r"(?<=[^\w\s])$"

def getWordReString(browseMode):
    s = wrEmpty if browseMode else wrEol
    wordReString = f"{s}|{wrNewline}|{wrWord}|{wrPunc}|{wrPunc2}"
    wordEndReString = f"{s}|{wrNewline}|{wrWordEnd}|{wrPuncEnd}|{wrPunc2End}"
    return wordReString, wordEndReString


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


def getWordFineReString(browseMode):
    wordReString, wordEndReString = getWordReString(browseMode)
    wordReFineString = f"{wordReString}|{wfrLine}|{wfrCap}|{wfrDigit}"
    wordFineEndReString = f"{wordEndReString}|{wfrLine}|{wfrCap}|{wfrDigit}"
    return wordReFineString,wordFineEndReString

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

def generateWordReBulky(punctuation=None, browseMode=False):
    if punctuation is None:
        punctuation = getConfig("bulkyWordPunctuation")
    punctuation = escapeRegex(punctuation)
    #space = f"\\s{punctuation}"
    #wordReBulkyString = f"(^|(?<=[{space}]))[^{space}]|[\r\n]+"
    w = f"[^\s%s]" % punctuation
    sw = r"(^|(?<=\s))%s" % w
    ws = r"(?<=%s)(\s|$)" % w
    sp = r"(^|(?<=\s))[%s]" % punctuation
    ps = r"(?<=[%s])(\s|$)" % punctuation
    pw = r"(?<=[%s])%s" % (punctuation, w)
    s = wrEmpty if browseMode else wrEol
    wordReBulkyString = f"{s}|{wrNewline}|{sw}|{sp}|{pw}"
    wordEndReBulkyString = f"{s}|{wrNewline}|{ws}|{ps}|{pw}"
    return wordReBulkyString, wordEndReBulkyString

def generateWordReCustom():
    wordReBulkyString = getConfig("bulkyWordRegex")
    wordEndReBulkyString = getConfig("bulkyWordEndRegex") or wordReBulkyString
    return wordReBulkyString, wordEndReBulkyString

# These constants map command assignment combo box index to actual functions
# w stands for navigate by word
# b and f stand for navigate by bulky/fine word
# 0 stands for unassigned
leftControlFunctions = "wwwwwbfwwbf"
rightControlFunctions = "wwwbfwwbfww"
controlWindowsFunctions = "0bf0000fbfb"

def getRegexByFunction(index, browseMode):
    wordCount = 1
    if index == 1:
        begin, end = getWordReString(browseMode)
    elif index in [2,4]:
        begin, end = generateWordReBulky(None, browseMode)
        if index == 4:
            wordCount = getConfig("wordCount")
    elif index == 3:
        begin, end = getWordFineReString(browseMode)
    elif index == 5:
        begin, end =  generateWordReCustom()
    else:
        return None, None, None
    return (
        re.compile(begin),
        re.compile(end),
        wordCount,
    )

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
        self.enableSelectionCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.enableSelectionCheckbox.Value = getConfig("enableSelection")
      # checkbox select trailing space
        label = _("Include trailing space when selecting words with control+shift+rightArrow")
        self.selectTrailingSpaceCheckbox = sHelper.addItem(wx.CheckBox(self, label=label))
        self.selectTrailingSpaceCheckbox.Value = getConfig("selectTrailingSpace")
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

    def fancyCrackle(self, levels, volume):
        levels = self.uniformSample(levels, self.MAX_BEEP_COUNT )
        beepLen = self.BEEP_LEN
        pauseLen = self.PAUSE_LEN
        pauseBufSize = NVDAHelper.generateBeep(None,self.BASE_FREQ,pauseLen,0, 0)
        beepBufSizes = [NVDAHelper.generateBeep(None, self.getPitch(l), beepLen, volume, volume) for l in levels]
        bufSize = sum(beepBufSizes) + len(levels) * pauseBufSize
        buf = ctypes.create_string_buffer(bufSize)
        bufPtr = 0
        for l in levels:
            bufPtr += NVDAHelper.generateBeep(
                ctypes.cast(ctypes.byref(buf, bufPtr), ctypes.POINTER(ctypes.c_char)),
                self.getPitch(l), beepLen, volume, volume)
            bufPtr += pauseBufSize  # add a short pause
        tones.player.stop()
        tones.player.feed(buf.raw)

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
        left = max(0, min(left, 100))
        right = max(0, min(right, 100))
        beepLen = length
        freqs = self.getChordFrequencies(chord)
        sampleWidth = 2
        tones.player.stop()
        bufSize = 0
        bufSizes = []
        for freq in freqs:
            size = NVDAHelper.generateBeep(None, freq, beepLen, left, right)
            bufSizes.append(size)
            if size > bufSize:
                bufSize = size
        buf = ctypes.create_string_buffer(bufSize)
        totalSamples = None
        for freq in freqs:
            NVDAHelper.generateBeep(buf, freq, beepLen, left, right)
            samples = struct.unpack("<%dh" % (bufSize // sampleWidth), buf.raw[:bufSize])
            if totalSamples is None:
                totalSamples = list(samples)
            else:
                totalSamples = [s1 + s2 for s1, s2 in zip(totalSamples, samples)]
        maxSample = 32767
        minSample = -32768
        totalSamples = [max(minSample, min(maxSample, s)) for s in totalSamples]
        packedData = struct.pack("<%dh" % len(totalSamples), *totalSamples)
        tones.player.feed(packedData)

    def uniformSample(self, a, m):
        n = len(a)
        if n <= m:
            return a
        # Here assume n > m
        result = []
        for i in range(0, m*n, n):
            result.append(a[i // m])
        return result
    def stop(self):
        tones.player.stop()


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
        if modVk == winUser.VK_LCONTROL or modVk == winUser.VK_CONTROL:
            control = 'left'
        if modVk == winUser.VK_RCONTROL:
            control = 'right'
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
        return self.appModule.productName.startswith("Visual Studio Code")
    except (NameError, AttributeError, RuntimeError) as e:
        mylog(f"Error in isVscodeApp: {str(e)}")
        return False

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

def makeCaretTextInfo(obj):
    """
    As of November 2024 Chrome cannot correctly tell us caret location in contenteditable text areas:
    https://issues.chromium.org/issues/378692760
    This function provides a work around for the simplest case when the entire selection is contained within a single child IAccessible object.
    """
    chromeEditorClass = NVDAObjects.IAccessible.chromium.Editor
    if not isinstance(obj, chromeEditorClass):
        caretInfo = obj.makeTextInfo(textInfos.POSITION_CARET)
        return caretInfo, None
    
    # We start with selection as it appears to always work correctly in Chrome
    selectionInfo = obj.makeTextInfo(textInfos.POSITION_SELECTION)
    if selectionInfo.isCollapsed:
        return selectionInfo, selectionInfo
    if selectionInfo._startObj != selectionInfo._endObj:
        # This case is tricky; no easy workaround here.
        # Falling back to default behavior and hope Google will eventually fix the bug.
        caretInfo = obj.makeTextInfo(textInfos.POSITION_CARET)
        return caretInfo, selectionInfo
    # Easy case: hacking up caret textInfo
    caretInfo = selectionInfo.copy()
    innerObj = caretInfo._startObj
    caretOffset = innerObj.IAccessibleTextObject.caretOffset
    caretInfo._start._startOffset = caretOffset
    caretInfo._start._endOffset = caretOffset
    caretInfo._end._startOffset = caretOffset
    caretInfo._end._endOffset = caretOffset
    return caretInfo, selectionInfo


def script_caret_moveByWordWordNav(self,gesture):
    mods = getModifiers(gesture)
    key = gesture.mainKeyName
    isBrowseMode = isinstance(self, treeInterceptorHandler.DocumentTreeInterceptor)
    isEnabled = getConfig("enableInBrowseMode" if isBrowseMode else "overrideMoveByWord")
    obj = self.rootNVDAObject if isBrowseMode else self
    blacklisted = isBlacklistedApp(obj)
    isTerminal = isinstance(obj, Terminal)
    gd = isGoogleDocs(obj)
    disableGd = gd if getConfig("disableInGoogleDocs") else False
    if not isBrowseMode:
        isVSCode = isVscodeApp(obj)
        if isVSCode:
            isVSCodeMain = isVSCodeMainEditor(obj)
    else:
        isVSCode = False
    option = f"{mods}AssignmentIndex"
    pattern, patternEnd, wordCount = getRegexByFunction(getConfig(option), isBrowseMode)
    if (
        not isEnabled
        or pattern is None
        or blacklisted
        or disableGd
        or (isVSCode and not isVSCodeMain)
        or isTerminal
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
        caretInfo, _ = makeCaretTextInfo(self)
    doWordMove(caretInfo, pattern, direction, wordCount)



beeper = Beeper()
def chimeCrossParagraphBorder():
    volume = getConfig("paragraphChimeVolume")
    beeper.fancyBeep("AC#EG#", 30, volume, volume)

def chimeNoNextWord():
    volume = getConfig("paragraphChimeVolume")
    beeper.fancyBeep('HF', 100, left=volume, right=volume)

def getParagraphUnit(textInfo):
    if isinstance(textInfo, VsWpfTextViewTextInfo):
        # TextInfo in Visual Studio doesn't understand UNIT_PARAGRAPH
        return textInfos.UNIT_LINE
    # In Windows 11 Notepad, we should use UNIT_PARAGRAPH instead of UNIT_LINE in order to handle wrapped lines correctly
    return textInfos.UNIT_PARAGRAPH

def _expandParagraph(info):
    paragraphUnit = getParagraphUnit(info)
    info.expand(paragraphUnit)
    if isinstance(info, ITextDocumentTextInfo):
        # Workaround for PoEdit. In PoEdit the last character of edit box is newline, but it's impossible to take textInfo there, so we need to exclude it.
        collapsedInfo = info.copy()
        collapsedInfo.collapse(end=True)
        if collapsedInfo.compareEndPoints(info, "endToEnd") < 0:
            info.setEndPoint(collapsedInfo, "endToEnd")

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
        collapsedAnchorPoint = paragraph.copy()
    else:
        paragraph.collapse(end=False)
        result = paragraph.move(textInfos.UNIT_CHARACTER, -1)
        if result == 0:
            return False
    _expandParagraph(paragraph)
    #if paragraph.isCollapsed:
        #return False
    if (
        direction > 0
        and paragraph.compareEndPoints(collapsedAnchorPoint, "startToStart") < 0
    ):
        # Sometimes in Microsoft word it just selects the same last paragraph repeatedly
        # Also in Google Chrome it appears to select the last line if there are no more paragraphs
        return False
    if (
        direction > 0
        and paragraph.compareEndPoints(oldParagraph, "startToStart") <= 0
        and paragraph.compareEndPoints(oldParagraph, "endToEnd") <= 0
    ):
        # At last position in Notepad++ when the last line is empty
        return False
    return True


def patchMoveToCodepointOffsetInCompoundMozillaTextInfo():
    # My optimized implementation sucks - doesn't work correctly in some cases
    # E.g. in Gmail editor with spelling errors.
    # Because it assumes if __start and _end belong to the same textInfo, then we can call moveToCodepointOffset on that inner textInfo, which is offsetTextInfo,
    # but that's not the case, because we need to also recurse into inner text infos.
    # So use this hacky implementation until fixed in NVDA.
    
    from NVDAObjects.IAccessible.ia2TextMozilla import MozillaCompoundTextInfo
    from textInfos import offsets
    from NVDAObjects.IAccessible.ia2TextMozilla import _getEmbedded, _getRawTextInfo
    from NVDAObjects import NVDAObjectTextInfo

    def adjustTextInfoOffset(textInfo, offset):
        textInfo = textInfo.copy()
        textInfo._startOffset = textInfo._endOffset = offset
        # We need to store a hard reference to the object, because otherwise the object apparently sometimes dies before we can make use of it.
        # NVDA is using a questionable memory model where they don't rely on Python GC, but rather rely on reference counters.
        # So in order to prevent circular references - e.g. when textInfo references object and vice versa,
        # They use weak references instead.
        # This apparently generates a lot of headache especially in complicated algorithms.
        # Wondering if there are any tangible benefits of this approach.
        textInfo._hardObj = textInfo._obj()
        return textInfo
        
    
    def _iterRecursiveText_wordNav(self, ti: offsets.OffsetsTextInfo, controlStack, formatConfig):
        encoder = ti._getOffsetEncoder()
        seenCharacters = 0
        if ti.obj == self._endObj:
            end = True
            ti.setEndPoint(self._end, "endToEnd")
        else:
            end = False
    
        for item in ti._iterTextWithEmbeddedObjects(controlStack is not None, formatConfig=formatConfig):
            if item is None:
                yield ""
            elif isinstance(item, str):
                startOffset = ti._startOffset + encoder.strToEncodedOffsets(seenCharacters, seenCharacters)[0]
                yield adjustTextInfoOffset(ti, startOffset)
                yield item
                seenCharacters += len(item)
            elif isinstance(item, int):  # Embedded object.
                seenCharacters += 1
                embedded: typing.Optional[IAccessible] = _getEmbedded(ti.obj, item)
                if embedded is None:
                    continue
                notText = _getRawTextInfo(embedded) is NVDAObjectTextInfo
                if controlStack is not None:
                    controlField = self._getControlFieldForObject(embedded)
                    controlStack.append(controlField)
                    if controlField:
                        if notText:
                            controlField["content"] = embedded.name
                        controlField["_startOfNode"] = True
                        yield textInfos.FieldCommand("controlStart", controlField)
                if notText:
                    # A 'stand-in' character is necessary to make routing work on braille devices.
                    # Note #11291:
                    # Using a space character (EG " ") causes 'space' to be announced after objects like graphics.
                    # If this is replaced with an empty string, routing to cell becomes innaccurate.
                    # Using the textUtils.OBJ_REPLACEMENT_CHAR which is the
                    # "OBJECT REPLACEMENT CHARACTER" (EG "\uFFFC")
                    # results in '"0xFFFC' being displayed on the braille device.
                    startOffset = ti._startOffset + encoder.strToEncodedOffsets(seenCharacters - 1, seenCharacters - 1)[0]
                    yield adjustTextInfoOffset(ti, startOffset)
                    yield " "
                else:
                    for subItem in self._iterRecursiveText_wordNav(
                        self._makeRawTextInfo(embedded, textInfos.POSITION_ALL),
                        controlStack,
                        formatConfig,
                    ):
                        yield subItem
                        if subItem is None:
                            return
                if controlStack is not None and controlField:
                    controlField["_endOfNode"] = True
                    del controlStack[-1]
                    yield textInfos.FieldCommand("controlEnd", None)
            else:
                yield item
                raise RuntimeError
    
        if end:
            # None means the end has been reached and text retrieval should stop.
            yield None
    
    def _getText_wordNav(self, withFields, formatConfig=None):
        fields = []
        if self.isCollapsed:
            return fields
    
        if withFields:
            # Get the initial control fields.
            controlStack = []
            rootObj = self.obj
            obj = self._startObj
            ti = self._start
            cannotBeStart = False
            while obj and obj != rootObj:
                field = self._getControlFieldForObject(obj)
                if field:
                    if ti._startOffset == 0:
                        if not cannotBeStart:
                            field["_startOfNode"] = True
                    else:
                        # We're not at the start of this object, which also means we're not at the start of any ancestors.
                        cannotBeStart = True
                    fields.insert(0, textInfos.FieldCommand("controlStart", field))
                controlStack.insert(0, field)
                ti = self._getEmbedding(obj)
                if not ti:
                    log.debugWarning(
                        "_getEmbedding returned None while getting initial fields. " "Object probably dead.",
                    )
                    return []
                obj = ti.obj
        else:
            controlStack = None
    
        # Get the fields for start.
        fields += list(self._iterRecursiveText_wordNav(self._start, controlStack, formatConfig))
        if not fields:
            # We're not getting anything, so the object must be dead.
            # (We already handled collapsed above.)
            return fields
        obj = self._startObj
        while fields[-1] is not None:
            # The end hasn't yet been reached, which means it isn't a descendant of obj.
            # Therefore, continue from where obj was embedded.
            if withFields:
                try:
                    field = controlStack.pop()
                except IndexError:
                    # We're trying to walk up past our root. This can happen if a descendant
                    # object within the range died, in which case _iterRecursiveText_wordNav will
                    # never reach our end object and thus won't yield None. This means this
                    # range is invalid, so just return nothing.
                    log.debugWarning("Tried to walk up past the root. Objects probably dead.")
                    return []
                if field:
                    # This object had a control field.
                    field["_endOfNode"] = True
                    fields.append(textInfos.FieldCommand("controlEnd", None))
            ti = self._getEmbedding(obj)
            if not ti:
                log.debugWarning(
                    "_getEmbedding returned None while ascending to get more text. " "Object probably dead.",
                )
                return []
            obj = ti.obj
            if ti.move(textInfos.UNIT_OFFSET, 1) == 0:
                # There's no more text in this object.
                continue
            ti.setEndPoint(self._makeRawTextInfo(obj, textInfos.POSITION_ALL), "endToEnd")
            fields.extend(self._iterRecursiveText_wordNav(ti, controlStack, formatConfig))
        del fields[-1]
    
        if withFields:
            # Determine whether the range covers the end of any ancestors of endObj.
            obj = self._endObj
            ti = self._end
            while obj and obj != rootObj:
                field = controlStack.pop()
                if field:
                    fields.append(textInfos.FieldCommand("controlEnd", None))
                if ti.compareEndPoints(self._makeRawTextInfo(obj, textInfos.POSITION_ALL), "endToEnd") == 0:
                    if field:
                        field["_endOfNode"] = True
                else:
                    # We're not at the end of this object, which also means we're not at the end of any ancestors.
                    break
                ti = self._getEmbedding(obj)
                obj = ti.obj
    
        return fields
    def _getTextWith_Mapping_wordNav(self):
        text = []
        currentStringIndex = 0
        stringIndicesToTextInfos = {}
        for field in self._getText_wordNav(withFields=False):
            if isinstance(field, textInfos.TextInfo):
                stringIndicesToTextInfos[currentStringIndex] = field
            elif isinstance(field, str):
                text.append(field)
                currentStringIndex += len(field)
            else:
                pass
        return "".join(text), stringIndicesToTextInfos
        
    def moveToCodepointOffset_wordNav(self, codepointOffset):
        text, mapping = self._getTextWith_Mapping_wordNav()
        knownOffsets = sorted(list(mapping.keys()))
        i = bisect.bisect_right(knownOffsets, codepointOffset) - 1
        knownOffset = knownOffsets[i]
        innerTextInfo = mapping[knownOffset]
        tmpOffset = innerTextInfo._startOffset
        innerTextInfo.expand(textInfos.UNIT_STORY)
        innerTextInfo._startOffset = tmpOffset
        innerAnchor = innerTextInfo.moveToCodepointOffset(codepointOffset - knownOffset)
        anchor = self.copy()
        anchor._start = anchor._end = innerAnchor
        anchor._startObj = anchor._endObj = innerAnchor._hardObj
        for textInfo in mapping.values():
            # Manually releasing hard references to the objects we didn't need.
            # As if Python no longer has a GC.
            del textInfo._hardObj
        return anchor
        
    def moveToCodepointOffset_wordNav_generic(self, codepointOffset):
        return self.moveToCodepointOffset(codepointOffset)
    
    MozillaCompoundTextInfo._iterRecursiveText_wordNav = _iterRecursiveText_wordNav
    MozillaCompoundTextInfo._getText_wordNav = _getText_wordNav
    MozillaCompoundTextInfo._getTextWith_Mapping_wordNav = _getTextWith_Mapping_wordNav
    MozillaCompoundTextInfo.moveToCodepointOffset_wordNav = moveToCodepointOffset_wordNav
    textInfos.TextInfo.moveToCodepointOffset_wordNav = moveToCodepointOffset_wordNav_generic

patchMoveToCodepointOffsetInCompoundMozillaTextInfo()

class MoveToCodePointOffsetError(Exception):
    pass


VISUAL_STUDIO_CODEPOINT_EXCEPTION_RE = re.compile("^Inner textInfo text '.*' doesn't match outer textInfo text")

def isPlainMozillaCompoundTextInfo(textInfo):
    try:
        return (
            isinstance(textInfo, MozillaCompoundTextInfo)
            and textInfo._startObj == textInfo._endObj
            and textInfo._startObj.iaHypertext.nHyperlinks == 0
        )
    except COMError as e:
        if e.args[1] == 'Not implemented':
            return True
    return False

def moveToCodePointOffset(textInfo, offset):
    exceptionMessage = "Unable to find desired offset in TextInfo."
    try:
        return textInfo.moveToCodepointOffset_wordNav(offset)
    except RuntimeError as e:
        if str(e) == exceptionMessage:
            raise MoveToCodePointOffsetError(e)
        elif (
            isinstance(textInfo, VsWpfTextViewTextInfo)
            and len(textInfo.text) >= 1
            and textInfo.text[-1] == '\n'
            and VISUAL_STUDIO_CODEPOINT_EXCEPTION_RE.search(str(e)) is not None
        ):
            # Visual Studio textInfo has the following weirdness: when you select a line, it also includes a trailing newline character \n.
            # However, when you count characters from the back, that newline character is sometimes not counted.
            # This causes exceptions during word navigation. Working around by trying again without that trailing newline character.
            newTextInfo = textInfo.copy()
            result = newTextInfo.move(textInfos.UNIT_CHARACTER, -1, 'end')
            if (result != -1) or (len(newTextInfo.text) != len(textInfo.text) - 1):
                raise e
            return moveToCodePointOffset(newTextInfo, offset)
        else:
            raise e

def doWordMove(caretInfo, pattern, direction, wordCount=1):
    speech.clearTypedWordBuffer()
    if not caretInfo.isCollapsed:
        raise RuntimeError("Caret must be collapsed")
    paragraphInfo = caretInfo.copy()
    _expandParagraph(paragraphInfo)
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
                if len(text.rstrip("\r\n")) > 0:
                    doRight = not wordEndIsParagraphEnd
                else:
                    doRight = direction < 0
                if isinstance(newCaretInfo, MozillaCompoundTextInfo):
                    # Also Chrome sometimes forgets cursor location if updated via accessibility API, 
                    # for example when doing alt-tab right after updating,
                    # so fake keyboard commands:
                    executeAsynchronously(asyncUpdateNotepadPPCursorWhenModifiersReleased(doRight, globalGestureCounter))
                if isinstance(newCaretInfo, ScintillaTextInfo):
                    # Notepad++ doesn't remember cursor position when updated from here and then navigating by line up or down
                    # This hack makes it remember new position
                    executeAsynchronously(asyncUpdateNotepadPPCursorWhenModifiersReleased(doRight, globalGestureCounter))
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
        IAccessible2 doesn't allow setting selection across paragraphs and there is nothing we can do to work around.
        Here be dragons.
    """
    caretAheadOfAnchor = newCaretInfo.compareEndPoints(anchorInfo, "startToStart") < 0
    try:
        hwnd = newCaretInfo._obj().windowHandle
        globalCaretAheadOfAnchor[hwnd] = caretAheadOfAnchor
    except AttributeError:
        pass
    isBrowseMode = isinstance(newCaretInfo._obj(), treeInterceptorHandler.DocumentTreeInterceptor)
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
    elif isinstance(newCaretInfo, IA2TextTextInfo) and newCaretInfo.obj.IAccessibleTextObject.NSelections == 1:
        # updateSelection implementation is not good enough when selection is already present. This can cause unselected/selected stuttering in Chrome.
        # providing a better implementation
        anchorOffset, caretOffset = spanInfo._startOffset, spanInfo._endOffset
        if caretAheadOfAnchor:
            anchorOffset, caretOffset = caretOffset, anchorOffset
        spanInfo.obj.IAccessibleTextObject.setSelection(0, anchorOffset, caretOffset)
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
    isBrowseMode = isinstance(self, treeInterceptorHandler.DocumentTreeInterceptor)
    isEnabled = getConfig("enableSelection")
    isNpp = isinstance(self, Scintilla)
    obj = self.rootNVDAObject if isBrowseMode else self
    blacklisted = isBlacklistedApp(obj)
    isTerminal = isinstance(obj, Terminal)
    gd = isGoogleDocs(obj)
    disableGd = gd if getConfig("disableInGoogleDocs") else False
    if not isBrowseMode:
        isVSCode = isVscodeApp(obj)
        if isVSCode:
            isVSCodeMain = isVSCodeMainEditor(obj)
    else:
        isVSCode = False
    option = f"{mods}AssignmentIndex"
    pattern, patternEnd, wordCount = getRegexByFunction(getConfig(option), isBrowseMode)
    direction = -1 if "leftArrow" in key else 1
    if (
        not isEnabled
        or pattern is None
        or blacklisted
        or disableGd
        or (isVSCode and not isVSCodeMain)
        or isTerminal
    ):
        if 'Windows' not in mods:
            if isBrowseMode:
                return cursorManager.CursorManager._selectionMovementScriptHelper(self, unit=textInfos.UNIT_WORD, direction=direction)
            else:
                try:
                    return self.editableText.EditableText.script_caret_changeSelection(self, gesture)
                except AttributeError:
                    pass
        gesture.send()
        return
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
        caretInfo, selectionInfo = makeCaretTextInfo(self)
        selectionInfo = selectionInfo or self.makeTextInfo(textInfos.POSITION_SELECTION)
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
    speech.clearTypedWordBuffer()
    if not caretInfo.isCollapsed:
        raise RuntimeError("Caret must be collapsed")
    if not anchorInfo.isCollapsed:
        raise RuntimeError("anchor must be collapsed")
    paragraphInfo = caretInfo.copy()
    _expandParagraph(paragraphInfo)
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
    """
    In certain cases we also override selection by character.
    This applies only to those situations where it's impossible to specify at which end of selection we should place the caret (e.g. in UIA applications).
    So we emulate caret being present at this or that end.
    So we override selection by character in those applications as well to preserve consistent behavior.
    """
    speech.clearTypedWordBuffer()
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
        cursorManager.CursorManager._CursorManager__gestures["kb:control+numpad1+shift"] = "selectByWordWordNav"
        cursorManager.CursorManager._CursorManager__gestures["kb:control+Windows+numpad1+shift"] = "selectByWordWordNav"
      # inputManager.executeGesture
        global originalExecuteGesture
        originalExecuteGesture = inputCore.InputManager.executeGesture
        inputCore.InputManager.executeGesture = preExecuteGesture



    def  removeHooks(self):
        pass
