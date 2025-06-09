:: Set MOVES install location
set MOVESDir=C:\Users\Public\EPA\MOVES\MOVES3.0

:: Set up MOVES environment
cd /d %MOVESDir%
call setenv.bat

for %%X in (T:\2023November\brice\*.mrs) do ant run -Drunspec=%%X