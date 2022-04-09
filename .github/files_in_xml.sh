echo $(ls)
for f in $(ls ./WCLRanks/Data/*.lua); do
	echo "$f"
	name=$(basename "$f")
	pattern="<Script\s+file=\"$name\"\s*/>"
	in_xml=$(grep -E -e $pattern ./WCLRanks/Data/WCLRanks.xml)
	if [ "$in_xml" = "" ]; then
		exit 1
	fi
done
for sf in $(grep -E -e "<Script\s+file=\".+\"\s*/>" ./WCLRanks/Data/WCLRanks.xml | sed -E 's/.*\"(.*)\".*/\1/g'); do
	echo "$sf"
	if [[ ! -f "./output/$sf" ]]; then
		exit 1
	fi
done
exit 0
