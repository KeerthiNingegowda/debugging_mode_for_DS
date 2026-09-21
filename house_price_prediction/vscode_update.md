## Vscode setup 

To make a debugger seamlessly on a multi-file package, you would need to make some changes to .vscode/launch.json. 

By default the launch.json will point to current file that you have open. So when you hit F5 to start the debugging model you will hit a wall

Modify the settings to the following

Here's what to do in .vscode/launch.json:

1. Open the file (Cmd+P → launch.json, or Run & Debug panel → gear icon).

2. Inside the "configurations": [ ... ] array,

<pre>
{
    "name": "Debug: house-price CLI",
    "type": "debugpy",
    "request": "launch",
    "module": "house_price_prediction.cli",
    "args": [
        "--data", "house_price_prediction/datasets/houses_synthetic.csv",
         "--trials", "5"
        ],
    "console": "integratedTerminal",
    "cwd": "${workspaceFolder}",
    "justMyCode": true
}

</pre>

<b>Note:-</b> Given that the program expects arguments you have to update the args parameter. DO NOT make changes to the program that you are debugging