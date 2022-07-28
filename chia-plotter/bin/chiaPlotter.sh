#!/bin/bash
set -euxo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
CHIA_PLOTTER_SCRIPTS_HOME=`dirname $DIR`

runningLogsDir="$CHIA_PLOTTER_SCRIPTS_HOME/logs/running"
finishedLogsDir="$CHIA_PLOTTER_SCRIPTS_HOME/logs/finished"
numberPlotsMadeFile="$CHIA_PLOTTER_SCRIPTS_HOME/data/numberPlotsMade.txt"
lastFinalDirFile="$CHIA_PLOTTER_SCRIPTS_HOME/data/lastFinalDir.txt"

# Runs chia plotter pulling in variables from the config files

# -----------------------------------------------------

# Loading in and initializing variables
. $CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt

timestamp=`date +%Y-%m-%d_%H:%M:%S`
echo "-------------NEW CRONJOB-------------"
echo "current time $timestamp"


    echo "Checking if we need to move any plots"
    # moves all finished plots to the finishedLogsDir
    results=`grep "Renamed final file from" $runningLogsDir/* -i -s -l`
    for result in ${results[@]}; do
        resultBaseName=$(basename $result)
        echo "Moving finished plot for $resultBaseName to finished folder"
        mv $result $finishedLogsDir/
    done

if [[ $RUN_SCRIPT == "true" ]]; then
    echo "RUN_SCRIPT is set to $RUN_SCRIPT. Set it to false to stop new plots from running."

    # Checking how many plots we should start
    countRunningPlots=`grep "Starting phase 1/4" $runningLogsDir/* -i -s -l | wc -l`
    countRunningPlotsOutOfPhase1=`grep "Starting phase 2/4" $runningLogsDir/* -i -s -l | wc -l`
    countRunningPlotsInPhase1=$(($countRunningPlots - $countRunningPlotsOutOfPhase1))

    countRoomForNewPlots=$(($desiredNumberOfPlots - $countRunningPlots))
    countRoomForPlotsInPhase1=$(($desiredNumberOfPlotsInPhase1 - $countRunningPlotsInPhase1))

    if [[ $countRoomForNewPlots -gt $countRoomForPlotsInPhase1 ]]; then
        numPlotsToStart=$countRoomForPlotsInPhase1
    else
        numPlotsToStart=$countRoomForNewPlots
    fi

    # If we should start new plots, run logic on where to start them
    if [[ $numPlotsToStart -gt 0 ]]; then
        # note* I had a while loop in here, but was worried about a race condition. We may have to run 2 of these scripts to start all plots in certain conditions.
        echo "Starting $numPlotsToStart new plots because the following limits have not been met:"
        echo "There are $countRunningPlots plots running and there are $desiredNumberOfPlots desired"
        echo "There are $countRunningPlotsInPhase1 plots in phase 1 and there are $desiredNumberOfPlotsInPhase1 desired"


        # This is for my single raid array
        while [[ $numPlotsToStart -gt 0 ]]; do

            # find next finalDir
            nextFinalDirIndex=0 # ensures a match if the list of final directories changed
            lastFinalDir=`cat $lastFinalDirFile`
            for index in ${!finalDirs[@]}; do
                if [[ $lastFinalDir == ${finalDirs[index]} ]]; then
                    nextFinalDirIndex=$(($index+1))
                    # If we've past the end of the array, go back to start
                    if [[ ${#finalDirs[@]} -eq $nextFinalDirIndex ]]; then
                        nextFinalDirIndex=0
                    fi
                    break
                fi
            done
            nextFinalDir=${finalDirs[nextFinalDirIndex]}
            echo "$nextFinalDir" > $lastFinalDirFile
               
            # Creating logfile name
            tempDirBaseName=$(basename $tempDir)
            finalDirBaseName=$(basename $nextFinalDir)
            timestamp=`date +%Y-%m-%d_%H:%M:%S`
            numberPlotsMade=`cat $numberPlotsMadeFile`
            numberPlotsMade=$(( $numberPlotsMade + 1 ))
            echo "$numberPlotsMade" > $numberPlotsMadeFile
            logFileName="Run$numberPlotsMade.$tempDirBaseName.$finalDirBaseName-$timestamp"

            # start chia run
            cd $HOME/chia-blockchain/ && . ./activate
            if [[ $useOtherFarmerKeys == "true" ]]; then
                chiaStart="chia plots create -n 1 -k 32 -u 128 -f $farmerKey -p $publicKey -b $memoryPerPlot -r $threadsPerPlot -t $tempDir -d $nextFinalDir/plots"
            else
                chiaStart="chia plots create -n 1 -k 32 -u 128 -b $memoryPerPlot -r $threadsPerPlot -t $tempDir -d $nextFinalDir/plots"
            fi
            nohup $chiaStart > $runningLogsDir/$logFileName &
            echo "Started plotLogs: $logFileName PID: $!"

            numPlotsToStart=$(($numPlotsToStart - 1)) # decrement numPlotsToStart so we stop adding plots
     
        done
    else
        echo "Not starting new plots because one of the following limits has been met:"
        echo "There are $countRunningPlots plots running and there are $desiredNumberOfPlots desired"
        echo "There are $countRunningPlotsInPhase1 plots in phase 1 and there are $desiredNumberOfPlotsInPhase1 desired"
    fi
else
    echo "RUN_SCRIPT is set to $RUN_SCRIPT. Set it back to true to run."
fi
