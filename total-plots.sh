#!/bin/bash

noclr='\033[0m'
wht='\033[1;37m'
ylw='\033[0;33m'
pnk='\033[1;35m'
grn='\033[0;32m'

farm_list=$(ls /media/$(whoami)/)

seperator="$wht*********************************************************"

echo -e "$seperator"
for FARM in ${farm_list[@]};
do
	plots_in_dir=$(ls /media/$(whoami)/$FARM/plots/ | wc -l)
	printf "$wht*$pnk\t\tPLOTS IN FARM: %-7s - $ylw $plots_in_dir \t\t$wht*\n" "$FARM"
	total_plots=$(($total_plots + $plots_in_dir))
done

echo -e "$seperator"
echo -e "\t\t     $grn TOTAL PLOTS: $total_plots"
echo -e "$seperator"

