#!/bin/bash
set +eux

# Find directory that the install.sh file is in
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
CHIA_PLOTTER_SCRIPTS_HOME=$DIR


# Create the log files
mkdir -p $CHIA_PLOTTER_SCRIPTS_HOME/logs/running
mkdir -p $CHIA_PLOTTER_SCRIPTS_HOME/logs/finished
touch $CHIA_PLOTTER_SCRIPTS_HOME/logs/cronjob.log

find $CHIA_PLOTTER_SCRIPTS_HOME/logs -type d -exec chmod 755 {} \;
find $CHIA_PLOTTER_SCRIPTS_HOME/logs -type f -exec chmod 644 {} \;


# Create config files
mkdir -p $CHIA_PLOTTER_SCRIPTS_HOME/conf/state
touch $CHIA_PLOTTER_SCRIPTS_HOME/conf/state/numberPlotsMade.txt
touch $CHIA_PLOTTER_SCRIPTS_HOME/conf/state/lastFinalDir.txt

find $CHIA_PLOTTER_SCRIPTS_HOME/conf -type d -exec chmod 755 {} \;
find $CHIA_PLOTTER_SCRIPTS_HOME/conf -type f -exec chmod 644 {} \;


# Grant execute to all the script files
chmod 755 $CHIA_PLOTTER_SCRIPTS_HOME/bin
chmod 744 $CHIA_PLOTTER_SCRIPTS_HOME/bin/*


# Create symbolic links to make starting easier
ln -s "$CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotter.sh" "$CHIA_PLOTTER_SCRIPTS_HOME"
ln -s "$CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotterGradually.sh" "$CHIA_PLOTTER_SCRIPTS_HOME"
ln -s "$CHIA_PLOTTER_SCRIPTS_HOME/bin/startGUI.sh" "$CHIA_PLOTTER_SCRIPTS_HOME"
ln -s "$CHIA_PLOTTER_SCRIPTS_HOME/bin/stopPlotter.sh" "$CHIA_PLOTTER_SCRIPTS_HOME"
ln -s "$CHIA_PLOTTER_SCRIPTS_HOME/bin/addNewFinalDirs.sh" "$CHIA_PLOTTER_SCRIPTS_HOME"

find $CHIA_PLOTTER_SCRIPTS_HOME -type l -exec chmod 744 {} \;


# Add alias' and variables
bashrc="$HOME"/.bashrc
if test -f "$bashrc"; then
  bash_profile="$HOME"/.bash_profile
  touch $bash_profile # create if it isn't there
  printf "\nRemoving old references to $CHIA_PLOTTER_SCRIPTS_HOME in .bash_profile\n"
  cat "$bash_profile" | grep -v "alias chia" | tee "$bash_profile" >/dev/null
  echo "alias chiaStartPlotter=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotter.sh\"" | tee -a $bash_profile
  echo "alias chiaStopPlotter=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/stopPlotter.sh\"" | tee -a $bash_profile
  echo "alias chiaStartGUI=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/startGUI.sh\"" | tee -a $bash_profile
  echo "alias chiaStartPlotterGradually=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotterGradually.sh\"" | tee -a $bash_profile

  # Scripts don't load up the variables... so deleting for now
  # echo "export PATH=\$PATH:$CHIA_PLOTTER_SCRIPTS_HOME/bin" | tee -a $bash_profile
  # echo "export CHIA_PLOTTER_SCRIPTS_HOME=$CHIA_PLOTTER_SCRIPTS_HOME" | tee -a $bash_profile

  numRefsToBashProfile=`cat "$bashrc" | grep "bash_profile" | wc -l`
  if [[ $numRefsToBashProfile -eq 0 ]]; then
    echo "source ~/.bash_profile" | tee -a "$bashrc" >/dev/null
  fi

  . "$bashrc" # Source .bashrc for immediate use in terminal if running install script with source command
fi


# Add alias' and variables
zshrc="$HOME"/.zshrc
if test -f "$zshrc"; then
  zsh_profile="$HOME"/.zsh_profile
  touch $zsh_profile # create if it isn't there
  printf "\nRemoving old references to $CHIA_PLOTTER_SCRIPTS_HOME in .zsh_profile\n"
  cat "$zsh_profile" | grep -v "alias chia" | tee "$zsh_profile" >/dev/null
  echo "alias chiaStartPlotter=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotter.sh\"" | tee -a $zsh_profile
  echo "alias chiaStopPlotter=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/stopPlotter.sh\"" | tee -a $zsh_profile
  echo "alias chiaStartGUI=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/startGUI.sh\"" | tee -a $zsh_profile
  echo "alias chiaStartPlotterGradually=\"bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotterGradually.sh\"" | tee -a $zsh_profile

  # Scripts don't load up the variables... so deleting for now
  # echo "export PATH=\$PATH:$CHIA_PLOTTER_SCRIPTS_HOME/bin" | tee -a $zsh_profile
  # echo "export CHIA_PLOTTER_SCRIPTS_HOME=$CHIA_PLOTTER_SCRIPTS_HOME" | tee -a $zsh_profile

  numRefsToZshProfile=`cat "$zshrc" | grep "zsh_profile" | wc -l`
  if [[ $numRefsToZshProfile -eq 0 ]]; then
    echo "source ~/.zsh_profile" | tee -a "$zshrc" >/dev/null
  fi

  . "$zshrc" # Source .zshrc for immediate use in terminal if running install script with source command
fi

# Don't accidentally plot
printf "\nMaking sure the plotter is off. Running stopPlotter.sh\n"
bash $CHIA_PLOTTER_SCRIPTS_HOME/bin/stopPlotter.sh

# Adding cronjob
cronjob=`crontab -l | grep "cronjob.log"`
numJobsFound=`echo $cronjob | wc -l`
if [[ $numJobsFound -ne 0 ]]; then 
  printf "\nRemoving old cronjobs that point to cronjob.log\n"
  echo "$cronjob"
  crontab -l | grep -v "cronjob.log" | crontab -
fi
printf "\nCreating new cronjob to run plotter\n"
(crontab -l; echo "*/1 * * * * $CHIA_PLOTTER_SCRIPTS_HOME/bin/chiaPlotter.sh >> $CHIA_PLOTTER_SCRIPTS_HOME/logs/cronjob.log 2>&1") | crontab -
newCronjob=`crontab -l | grep "cronjob.log"`
printf "$newCronjob\n\n"