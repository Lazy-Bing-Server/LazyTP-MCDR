from mcdreforged.api.types import ServerInterface

CONFIG_PATH = 'config/lazytp.json'

TP_PREFIX = '!!tp'
OVERWORLD_PREFIX = '!!overworld'
NETHER_PREFIX = '!!nether'
END_PREFIX = '!!end'

global_server = ServerInterface.get_instance().as_plugin_server_interface()

META = global_server.get_self_metadata()
