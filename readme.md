# Kingdomino

## 1. Server

Change settings in `./common/config.py` file: \
For deployment:

```python
IP_SERVER = '127.0.0.1'
```

For production:

```python
IP_SERVER = '0.0.0.0'
```

Command to run server

```bash
python3 run_server.py
```

## 2. Client

Navigate to client directory

```bash
cd client
```

Change settings in config.py file: \
For deployment:

```python
C_IP_SERVER = '127.0.0.1'
```

For production:

```python
C_IP_SERVER = 'IP_SERVER'
```

Command to run client app

```bash
python3 run_client.py
```

Args:
login - enter your username example:

```bash
python3 main.py login="User-123456"
```

hacker_mode - enter hacker mode example:

```bash
python3 main.py hacker_mode="exit after choice"
```

List of hacker's mode:

- "exit after choice"
- "exit during game"
- "timeout"
- "spamming"

## 3. Cleaning logs files:

```bash
chmod +x clean_logs.sh
./clean_logs.sh
```

## 4. Link to specification of project:

http://mw.home.amu.edu.pl/zajecia/SIK2021/SIKPRO.html
