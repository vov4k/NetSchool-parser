git fetch --all
git reset --hard origin/master

for i in {1..20};
do nohup python3 -u /home/panyuhin_nikita/NetSchool/run_last.py & sleep 3;
done >> ./src/log.txt
