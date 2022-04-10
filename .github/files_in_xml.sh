for f in $(ls ./Data/*.lua); do
	name=$(basename "$f")
	pattern="<Script\s+file=\"$name\"\s*/>"
	in_xml=$(grep -E -e $pattern ./Data/WCLRanks.xml)
	if [ "$in_xml" = "" ]; then
		exit 1
	fi
done
for sf in $(grep -E -e "<Script\s+file=\".+\"\s*/>" ./Data/WCLRanks.xml | sed -E 's/.*\"(.*)\".*/\1/g'); do
	if [[ ! -f "./Data/$sf" ]]; then
		exit 1
	fi
done
exit 0
