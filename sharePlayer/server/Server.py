
import subprocess
import configparser
import appdirs
import os
import pexpect
import redis
import atexit

def sync():
    """
    Adding function to configfile to sync up
    """
    with open(config_file,"w") as f:
        config.write(f)

def start_server(ui):
    """Start the things necessary to be a server."""
    global config, config_file, srv_p, redis_connection, redis_pubsub

    # Figure out where our config should be
    user_config_dir = appdirs.AppDirs("sharePlayer").user_config_dir

    # Make it if needed
    os.makedirs(user_config_dir,exist_ok=True)

    config_file = os.path.join(user_config_dir,"stunnel_config.ini")
    psk_file = os.path.join(user_config_dir,"stunnel_config.psk")
    pid_file = os.path.join(user_config_dir,"stunnel.pid")
    
    config = configparser.ConfigParser()

    config['SharePlayer server'] = {
        'accept': MenuConfig.config['Server']['ip'] + ":" + MenuConfig.config['Server']['port'],
        'connect': MenuConfig.config['Redis']['ip'] + ":" + MenuConfig.config['Redis']['port'],
        'ciphers': 'PSK',
        'PSKsecrets': psk_file,
    }

    sync()

    # Config parser can't do global variables apparently...
    with open(config_file, 'r+') as f:
        x = f.read()
        f.seek(0,0)
        f.write("""compression = deflate
foreground = yes
syslog = no
pid = {pid}
; setuid = nobody
; setgid = nogroup\n\n""".format(pid=pid_file) + x)

    #
    # Write the psk file
    # 

    key = ui._share_player._shared_key
    with open(psk_file, "w") as f:
        f.write('user:' + key)

    #
    # Start up stunnel
    #

    srv_p = subprocess.Popen(['stunnel', config_file], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    #srv_p = pexpect.spawn('stunnel', [config_file])

    #
    # Connect to Redis
    #

    ui._share_player.redis_connection = redis.Redis(host=MenuConfig.config['Redis']['ip'], port=MenuConfig.config['Redis']['port'], db=0)
    ui._share_player.redis_pubsub = ui._share_player.redis_connection.pubsub()

    # Tell Chat to subscribe
    Chat.do_subscribe(ui)

    # Register to kill off server at exist
    atexit.register(stop_server, ui)

    # Update status widget
    ui.status_box.base_widget.set_text('Serving: ' + MenuConfig.config['Server']['ip'] + ':' + MenuConfig.config['Server']['port'])

def stop_server(ui):
    srv_p.kill()
    ui.status_box.base_widget.set_text('Not Connected')

try:
    srv_p
except:
    srv_p = None

from ..ui import Config as MenuConfig
from ..ui import Chat
