
import urwid
import appdirs
import configparser
import os

def sync():
    """
    Adding function to configfile to sync up
    """
    with open(configFile,"w") as f:
        config.write(f)

def get_config():
    global config, configFile

    # Figure out where our config should be
    user_config_dir = appdirs.AppDirs("sharePlayer").user_config_dir

    # Make it if needed
    os.makedirs(user_config_dir,exist_ok=True)

    # Find our config file
    configFile = os.path.join(user_config_dir,"config.ini")
    
    config = configparser.ConfigParser()

    # Adding custom sync command
    config.sync = sync

    # If we don't have one, create it
    if not os.path.isfile(configFile):
        
        config['Server'] = {
            'IP': '0.0.0.0',
            'Port': '12345'
        }

        config['Redis'] = {
            'IP': '127.0.0.1',
            'Port': '6379'
        }

        config['Client'] = {
            'IP' : '',
            'Port': ''
        }

        config['User'] = {
            'Username': 'Anonymous'
        }

        config['Options'] = {
            'notify_volume': '100'
        }
        
        config.sync()

    # If we have a file, read it in
    else:
        config.read(configFile)


def run_view(ui):
    """Given UI instance, load up the config view."""

    # Update the config
    get_config()
    
    # Each cell will be a config option
    config_cells = []

    config_cells.append(urwid.LineBox(urwid.Edit(edit_text=config['Server']['ip'], multiline=False, align='left'), title='Server IP'))
    config_cells.append(urwid.LineBox(urwid.Edit(edit_text=config['Server']['port'], multiline=False, align='left'), title='Server Port'))
    config_cells.append(urwid.LineBox(urwid.Edit(edit_text=config['Redis']['ip'], multiline=False, align='left'), title='Redis IP'))
    config_cells.append(urwid.LineBox(urwid.Edit(edit_text=config['Redis']['port'], multiline=False, align='left'), title='Redis Port'))
    config_cells.append(urwid.LineBox(urwid.Edit(edit_text=config['User']['username'], multiline=False, align='left'), title='Username'))
    config_cells.append(urwid.LineBox(urwid.Edit(edit_text=config['Options']['notify_volume'], multiline=False, align='left'), title='Notify Volume'))

    config_grid = urwid.GridFlow(config_cells, 40, 1, 1, 'center')

    user_data = {
            'ui': ui,
            'server_ip': config_cells[0].base_widget,
            'server_port': config_cells[1].base_widget,
            'redis_ip': config_cells[2].base_widget,
            'redis_port': config_cells[3].base_widget,
            'username': config_cells[4].base_widget,
            'notify_volume': config_cells[5].base_widget,
            }

    config_submit = urwid.Button('Submit', on_press=submit_button, user_data=user_data)

    config_pile = urwid.Pile([config_grid, config_submit])

    ui.middle_box.widget_list[0] = urwid.Filler(config_pile)

def submit_button(button, user_data):
    global config

    ui = user_data['ui']

    # Save off the values
    config['Server']['ip'] = user_data['server_ip'].get_text()[0]
    config['Server']['port'] = user_data['server_port'].get_text()[0]
    config['Redis']['ip'] = user_data['redis_ip'].get_text()[0]
    config['Redis']['port'] = user_data['redis_port'].get_text()[0]
    config['User']['username'] = user_data['username'].get_text()[0]
    config['Options']['notify_volume'] = user_data['notify_volume'].get_text()[0]
    config.sync()

    ui.middle_box.widget_list[0] = ui.chat_box

# Only init config once
try:
    config
except:
    get_config()
