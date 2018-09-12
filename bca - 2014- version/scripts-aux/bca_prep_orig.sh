#!/bin/env bash

# Where is everything?
WORKING_PATH='/e/tmp/TestRun'
TEMPLATE='/c/tmp/CostBenTool'
MODELRUNS='/c/tmp/'
BASELINE="$MODELRUNS/2010_06_NO TOLL"
ALTERNATIVE="$MODELRUNS/2010_06_TOLLED"
ALTNEW="$WORKING_PATH/alt"
BASNEW="$WORKING_PATH/base"



# Test if working path already exists, fail if it exists, otherwise
# create it.
if [ -d "$WORKING_PATH" ]; then
    echo "$WORKING_PATH exists, aborting" 1>&2
    exit 1
else
    echo "Creating $WORKING_PATH"
    mkdir -p "$WORKING_PATH"
fi


# Make copies of both the alternative and baseline scenarios
#mkdir -p "$ALTNEW" "$BASNEW"
# note: regular cp truncates files at 2GB. oops.
echo "Copying alternative and baseline scenarios"
cp -r "$ALTERNATIVE" "$ALTNEW"
cp -r "$BASELINE" "$BASNEW"

# Remove any old copies of the BCA Prep tool
rm -rf "$ALTNEW/CostBenTool" 
rm -rf "$BASNEW/CostBenTool"

# Copy in the template stuff
echo "Copying BCA prep template"
cp -r "$TEMPLATE" "$ALTNEW"
cp -r "$TEMPLATE" "$BASNEW"

# Copy the PATHS* files into the template folder; sure is a lot of
# duplicated data in here...
echo "Copying alternative scenario banks"
for bank in `ls $ALTNEW |grep -Ei Bank[1-9]$`;
do mkdir -p "$ALTNEW/CostBenTool/$bank";
   cp $ALTNEW/$bank/PATHS* "$ALTNEW/CostBenTool/";
done

echo "Copying baseline banks"
for bank in `ls $BASNEW |grep -Ei Bank[1-9]$`;
do mkdir -p "$ALTNEW/CostBenTool/$bank";
   cp $ALTNEW/$bank/PATHS* "$ALTNEW/CostBenTool/";
done

echo "If you are copying EMME/3 projects, you now MUST create a new
external project and upgrade each of the databanks. For the BCA tool,
there are 5 emmebanks per scenario in the following folders: Bank1,
Bank2, Bank3, TODModel, and TripGen. There is no need to create a
backup, as this script will (by default) copy a fresh version each
time."
