# ClearBot
**A Discord bot for the [ClearFly](https://discord.gg/jjpwtusf6n) server**

## Docker
This bot has the ability to run in Docker. The `Dockerfile` is provided and the following run command is recommended.
```bash
docker run -d --env-file .env -v /path/to/database:/usr/src/ClearBot/database --name ClearBot <image-name>
```
Where `path/to/database` is the location where you'd like to store the SQLite databases (`main.db` and `va.db`)