git fetch

if [[ $(git rev-parse HEAD) != $(git rev-parse @{u}) ]]; then
	kill `ps -ef | awk '/iterate.py/{print $2}' | head -n 1`
	git pull --rebase
	python3 -u /home/panyuhin_nikita/NetSchool/iterate.py
fi
