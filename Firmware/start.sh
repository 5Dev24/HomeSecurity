python3 ./__main__.py $*
Out=$?
echo Process exited with code "$Out"
if [ $Out eq 1 ]
then
	read -p ""
fi