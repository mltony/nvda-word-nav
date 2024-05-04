# nvda-word-nav
WordNav NVDA add-on improves built-in navigation  by word, as well as adds extra word navigation commands with different definition for the word. It also provides word selection commands.

Most text editors support Control+LeftArrow/RightArrow commands for word navigation. However the definition of the word changes from one program to another. This is especially true of modern web-based text editors, such as Monaco. NVDA should know the definition of word in given program in order to speak words correctly. If NVDA doesn't know the exact definition, then either words are going to be skipped, or pronounced multiple times. Moreover, some web-based text editors position the cursor in the end of the word, instead of the beginning, making editing much harder for visually impaired users. In order to combat this problem I have created enhanced word navigation commands, that take the word definition from Notepad++ and they do not rely on program's definition of words, but rather parse lines into words on NVDA's side. The Control+LeftArrow/RightArrow gesture is not even sent to the program, thus ensuring the consistency of the speech.
## Word navigation and word definitions
Currently WordNav supports five definitions of the word, assigned to different gestures:

- `Left Control+Arrows`: Notepad++ definition, that treats alphanumeric characters as words, and adjacent punctuation marks are also treated as words. This should be the most convenient word definition for the majority of users.
- `RightControl+Arrows`: Fine word definition splits `camelCaseIdentifiers` and `underscore_separated_identifiers` into separate parts, thus allowing the cursor to go into long identifiers.
- `LeftControl+Windows+Arros`: Bulky word definition treats almost all punctuation symbols adjacent to text as part of a single word, therefore it would treat paths like `C:\directory\subdirectory\file.txt` as a single word.
- `RightControl+Windows+Arros`: Multiword definition, that groups several words together. The amount of words is configurable.
- Unassigned: custom regular expression word definition: allows user to define a custom regular expression for word boundaries.

Gestures can be customized in WordNav settings panel.

## Word selection

Word selection is supported starting with WordNav v2.0. Just add `shift` modifier to any word navigation gestures to select words. There is also one extra gesture for word selection:

* `control+shift+numpad1` and `control+windows+shift+numpad1` select word to the right similar to their `rightArrow` counterparts, but they also include trailing spaces into selection.

Please note, however, that currently used accessibility APIs have multiple issues related to word selection. Please get yourself familiar with the following list of issues and workarounds:

* UIA applications (e.g. Notepad, Visual Studio, Microsoft Word) don't support setting caret at the beginning of selection. In those  applications caret location is stored on WordNav side. As an adverse side effect, word navigation commands might not play well with line and paragraph selection commands (`shift+up/downArrow`, `control+shift+up/downArrow`) and results might be unpredictable. For convenience, character selection commands (`shift+left/rightArrow`) have been updated in WordNav for UIA applications and should work well.
* Basic single line Windows edit controls also don't allow to set the caret in front of selection, so the previous point also applies to them. This affects all single line edit boxes within NVDA.
* IAccessible2 doesn't provide a way to set selection spanning across multiple paragraphs. There is no known workaround for this issue. This affects rich multiline edit boxes in Chrome and Firefox, such as compose email text area in GMail and compose email window in Thunderbird.
* In notepad++ selection update messages come unreasonably slow. As a workaround, WordNav announces selection on NVDA side for word selection commands and silences late notifications for the following 0.5 seconds. As a result, if you press word selection command followed by another (e.g. character) selection command in quick succession, you might miss selection notification for the latter one if it came within 0.5 seconds from the last word selection command.
* In multiline edit boxes supporting TOM interface NVDA incorrectly identifies cursor location when selection is present. This has been fixed in nvaccess/nvda#16455, which is scheduled to be included in NVDA v2024.2 release. Before that release word selection commands won't work correctly in TOM edit boxes, such as NVDA log viewer.

## Notes

- If you would like to use virtual desktops feature of Windows 10, please remember to disable Control+Windows+Arrows keyboard shortcuts either in WordNav Settings panel, or in NVDA Input gestures dialog.
- Compatibility with VSCode requires NVDA add-on IndentNav v2.0 or later to be installed. Additionally, VSCode extension [Accessibility for NVDA IndentNav](https://marketplace.visualstudio.com/items?itemName=TonyMalykh.nvda-indent-nav-accessibility) must be installed in VSCode.

##  Downloads

Please install the latest version from NVDA add-on store.