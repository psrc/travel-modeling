:: Set MOVES install location
set MOVESDir=C:\Users\Public\EPA\MOVES\MOVES4.0

:: Set up MOVES environment
cd /d %MOVESDir%
call setenv.bat

for %%X in (T:\60day-TEMP\Brice\moves_run_specifications\2035_2050\*.mrs) do ant run -Drunspec=%%X