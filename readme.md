1. Server
Navigate to server directory
cd server

Change settings in config.py file:
For deployment: IP_SERVER='127.0.0.1'
For production: IP_SERVER='0.0.0.0'

Command to run server
python3  main.py

2. Client
Navigate to client directory
cd client

Change settings in config.py file:
For deployment: IP_SERVER='127.0.0.1'
For production: IP_SERVER='IP_SERVER'

Command to run client app
python3 main.py

Args:
login -  enter your username example: 
python3 main.py login="User-123456"

hacker_mode - enter hacker mode example:
python3 main.py hacker_mode="exit after choice"

List of hacker's mode:
- "exit after choice"
- "exit during game"
- "timeout"
- "spamming"

3. Cleaning logs files:
chmod +x clean_logs.sh
./clean_logs.sh

4. Link to specification of project: 
http://mw.home.amu.edu.pl/zajecia/SIK2021/SIKPRO.html


