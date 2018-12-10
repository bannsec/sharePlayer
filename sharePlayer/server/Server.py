
import subprocess
import configparser
import appdirs
import os
import pexpect
import redis

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
    
    config = configparser.ConfigParser()

    config['PSK server'] = {
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
; setuid = nobody
; setgid = nogroup\n\n""" + x)

    #
    # Write the psk file
    # 

    key = ui._share_player._shared_key
    with open(psk_file, "w") as f:
        f.write('user:' + key)

    #
    # Start up stunnel
    #

    # TODO: This will hang the exit process since the child is higher permissions.
    srv_p = subprocess.Popen(['sudo','stunnel',config_file], stderr=subprocess.PIPE)
    #srv_p = pexpect.spawn('sudo', ['stunnel', config_file])

    #
    # Connect to Redis
    #

    ui._share_player.redis_connection = redis.Redis(host=MenuConfig.config['Redis']['ip'], port=MenuConfig.config['Redis']['port'], db=0)
    ui._share_player.redis_pubsub = ui._share_player.redis_connection.pubsub()

    # Tell Chat to subscribe
    Chat.do_subscribe(ui)


def stop_server():
    # TODO: This doesn't really work atm..
    subprocess.run('sudo kill {}'.format(srv_p.pid), shell=True)

from ..ui import Config as MenuConfig
from ..ui import Chat
