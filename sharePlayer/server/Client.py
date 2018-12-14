
import logging
logger = logging.getLogger('SharePlayer:Server:Client')

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

def connect(ui):
    """Connect up!"""
    global config, config_file, srv_p, redis_connection, redis_pubsub

    # Figure out where our config should be
    user_config_dir = appdirs.AppDirs("sharePlayer").user_config_dir

    # Make it if needed
    os.makedirs(user_config_dir,exist_ok=True)

    config_file = os.path.join(user_config_dir,"stunnel_config.ini")
    psk_file = os.path.join(user_config_dir,"stunnel_config.psk")
    pid_file = os.path.join(user_config_dir,"stunnel.pid")
    
    config = configparser.ConfigParser()

    config['SharePlayer Client'] = {
        'client': 'yes',
        'accept': MenuConfig.config['Redis']['ip'] + ":" + MenuConfig.config['Redis']['port'],
        'connect': MenuConfig.config['Server']['ip'] + ":" + MenuConfig.config['Server']['port'],
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

    client_p = subprocess.Popen(['stunnel', config_file], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    # Slight race condition in setting up stunnel. Give it a head start
    sleep(0.5)

    #
    # Connect to Redis
    #

    ui._share_player.redis_connection = redis.Redis(host=MenuConfig.config['Redis']['ip'], port=MenuConfig.config['Redis']['port'], db=0)
    ui._share_player.redis_pubsub = ui._share_player.redis_connection.pubsub()

    # Make sure our name is set
    ui._share_player.redis_connection.client_setname(MenuConfig.config['User']['username'])

    # Tell Chat to subscribe
    Chat.do_subscribe(ui)

    # Update status widget
    ui.status_box.base_widget.set_text('Connected: ' + MenuConfig.config['Server']['ip'] + ':' + MenuConfig.config['Server']['port'])


def stop_server():
    client_p.kill()

from time import sleep
from ..ui import Config as MenuConfig
from ..ui import Chat
