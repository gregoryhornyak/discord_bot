while [ 1 -eq 1 ]
do
    # git pull
    git fetch
    git pull
    echo date
    echo "Bot up-to-date"
    # start app
    python3 sample/basic_bot.py resources/token/token
    # once ends, git pull again
    sleep 2
done
