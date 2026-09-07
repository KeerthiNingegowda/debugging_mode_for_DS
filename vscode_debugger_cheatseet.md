# Debugger mode cheatseet

A debugger basically freezes a running program at the moment a dev would choose and lets you inspect it. Everything else is variation on the tool. The mental model that is quite important to have for this tool is
<i> It is not a tool that will magically fix bugs for you, but helps you to pause and inspect your code</i>

### Core loop
1) Pick a line where you want to knoe what's true. Click to the right of the line number - you'll see a red dot. 
2) F5. The program runs normally ans tops there. This step should also spin up the Run and Debug floating window to your left otherwise something is wrong in your vscode settings.

Your view should look something similar to this. I changed the value of c from debug console
<img src="./images/demo.png">

3) Inspect the variables pane, teh call stack and any other breakpoints you have set 
4) Additionally inspect Debug Console which gives REPL interface which helps you to inteact/inspect with the variables. 
<br>🚨 Keep in mind that the making changes to variables from the console is not read-only/ It affects the rest of the execution 🚨</br>
5) F10 to run the next line, F5 to continue to next breakpoint. You can also use the floating toolbar at the top of the screen for this

<ul>
<b>Some important shortcuts</b>
<li>F5 - Start the deubgging mode or continue to next breakpoint</li>
<li>F9 - toggle breakpoint</li>
<li>F10 - Step over (run the current line, but don't go inside)</li>
<li>F11 - Step into (go inside the function on this line)</li>
</ul>

### Some quirks to get the setup right
1) F5 on mac is by default is enabled for dictation. So change your keyboard settings to use function keys for F5 as a shortcut to kick-off a debugger
2) By default VS Code ships with justMyCode: true, which means you cannot step into library code most of the times. To change this 
a) You'll need a .vscode/launch.json. For this Cmd_Shift_P -> "Debug:Add Configuration"
b) In that generated file, find or add the line "justMyCode": true
c) Save and go on as usual


### What are breakpoints and what are various options available?

A breakpoint is an instruction to runtime. Its basically telling to interpreter that when you hit this point stop the execution and hand over the control to me. Note that source files wont be touched or modified 

#### Types of breakpoints
<ol>
<li><b>Standard breakpoint</b></li> - Stops everytime time.
<li><b>Conditional breakpoint</b></li> - Stops only when an expression is true. Something like epoch == 47. The expression needs to be put when adding this kind of breakpoint and this will be evaluated everytime the expression runs
<li><b>Hit count breakpoint</b></li> - Same as above, but slightl different. Its lik saying stop on the 500th time this line runs and is useful when the condition is awkward to express
<li><b>Log point</b></li> - A breakpoint that doesn't stop. This is eseentially a print message and continue except that dont write ```print()``` amnd clean up after its done. The best option for inherited code
<li><b>Exception breakpoint</b></li> - Not attached to a line. Best option to understand or debug the excepions or ypour ```try/except:pass``` blocks
<li><b>Function breakpoint</b></li> - Stops on entry to the function wherever its called from. Handy when you now what is happening but not where
</ol>


#### Some quirks when working with breakpoints
1) Only for logpoint type breakpoints you would need to put your expressions within {} - Imagine like how you would print ith fstrings
2) For conditionals treat them how you would write expression with python
3) When working with hit count, this is quite literally like printing some nth line within a loop. So useful expressions would be, if you want something to print every 50th time use something like %50
4) You can add multiple breakpoints to a single line of code; Conditionals will evaluate first and then your message will print later
5) Note log points are super helpful especially when compared to print/logger; It will save you from the cleanup once you have finished debugging the code
6) When using Raised Exceptions, the debugger is quite aggressive in catching your python, uv, vscode or any related raised exceptions. Keep hitting F5 to get to the control to the file in question
