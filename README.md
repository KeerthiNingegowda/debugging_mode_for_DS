# Debugging mode for Data Scientists using VSCode Debugger

This repo consists of exploration related to debugging mode in VSCode. The exploration is intended to answer the following questions
1) How to use this tool to debug a piece of code? - This is independant of whether you are a DS
2) How can one specifically leverage this tool to debug ML/DL specific failure points? The failure landscape for DS workflows is quite distinct when compared to traditional software engineering
3) How can one use a debugger to review AI generated code to understand the code? Not just use it as a debugger
4) Where does using AI to understand vibe-coded applications genuinely be useful and fall short?


<b><u>Medium blog:-</u></b> TBD

## Installation
VSCode allows breakpoints in files whose language has a registered debugger. So check if you actually have the extension that helps you to run the debugger
```
code --list-extensions
```
This should have ms-python.debugpy extension to be able to add the breakpoints easily from the UI; Otherwise you have to rely on manually adding them using breakpoints() which can be cumbersom

If you dont have this extension then add it using
```
code --install-extension ms-python.debugpy 
code --install-extension ms-python.python
```

## Fundamental mechanisms in a debugger
A debugger basically freezes a running program at the moment a dev would choose and lets you inspect it. Everything else is variation on the tool. 

#### What does "frozen" actually mean in this context?
It doesn't mean that the entire program is in someway crystaliized or snapshotted. It means the execution of the program is suspended - still alive, still holding all its memory - just not scheduled to run

#### What actually happens when you add a breakpoint?
When the interpreter hits a set breakpoint, the debugger adapter basically tells the python interpreter to stop executing at that specific point, and the thread parks itself. The OS will not gives the program CPU time but holds everything as-is for this program up until the breakpoint. These will be the ones that will be held on to

<ul>
<li><b>Stack frames</b> - every active function call still sits on the stack with its own locals</li>
<li><b>Heap objects</b> - every list, dict, dataframe , model object and its corresponding current address</li>
<li><b>Module globals and imports</b> - still loaded</li>
<li><b>OS resources</b> - open files, DB connections, sockets, external network connections</li>
</ul>

The main benefit of the debugger is that you get the option to walk the stack trace, click any frame in the call stack panel and the variables panel re-renders in that frame's namespace.

#### What is not "frozen"?
<ul>
<li><b>Wall clock time</b> - If you are trying to measure time, this will break. Some doing someting lke time.elapsed()</li>
<li><b>Outside world won't stop</b> HTTP requests time out, DB connections and other timeouts will fail</li>
<li><b>State can be mutated</b> - The Debug Console is not read-only. Typing df.dropna(inplace=True)modifies the program. Even evaluating something with side-effect like a property lazily-loading changes the run</li>
</ul>

#### Why the "frozen state" matters for DS work specifically?
Instead of the print-rerun-wait cycle on a 3 minute data load, you break once after the data load an then interrogate the state inetractively. Things like df.shapem df.dtypes etc., all can be computed agaist the thes live objects without paying the load cost again. This frozen state returns a REPL which you can use in debug console and dynamically query your data


## DS-tailored concepts


