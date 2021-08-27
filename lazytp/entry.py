import functools

from mcdreforged.api.types import PluginServerInterface, PlayerCommandSource, CommandSource, MCDReforgedLogger
from mcdreforged.api.command import *
from mcdreforged.api.rtext import *
from mcdreforged.api.decorator import new_thread
from typing import Iterable, Union, Callable
from types import MethodType

from location_marker.constants import PREFIX as LOC_PREFIX
from minecraft_data_api import get_player_coordinate, get_server_player_list, get_player_dimension
from lazytp.constants import TP_PREFIX, global_server, META, DEBUG_MODE
from lazytp.storage import config, Dimension, LocationNotFound, LocationAlreadyExist, Coordinate, EzTeleportLocations


class SourceIsNotPlayer(CommandError):
    def __init__(self, name):
        super(SourceIsNotPlayer, self).__init__('Command is not from a player', name, name)


# Utilities
def tr(key: str, *args, **kwargs):
    text = global_server.tr(f'{META.id}.{key}', *args, **kwargs)
    if DEBUG_MODE:
        global_server.logger.debug(text, no_check=True)
    return text


def show_help(source: CommandSource):
    source.reply(tr('help_msg', TP_PREFIX, META.id, str(META.version)))


def print_tp_message(source: PlayerCommandSource):
    source.reply(
        tr('text.tp') + (RText(tr('text.unstuck')).c(
            RAction.run_command, '/unstuck').h(tr('hover.unstuck')) if config.we_unstuck else '')
    )


# This is a decorator
def ensure_player(func: Callable):
    @functools.wraps(func)
    def wrapper(source: CommandSource, *args, **kwargs):
        if not isinstance(source, PlayerCommandSource):
            raise SourceIsNotPlayer(source.__class__.__name__)
        func(source, *args, **kwargs)

    return wrapper


# TP preset management
def add_loc(source: CommandSource, alias: str, loc: str):
    try:
        config.add_wp(alias, loc)
    except LocationAlreadyExist:
        loc_already_exist(source)
    else:
        source.reply(tr('text.added', alias))


def rm_loc(source: CommandSource, alias: str):
    try:
        config.rm_wp(alias)
    except LocationNotFound:
        loc_not_found(source)
    else:
        source.reply(tr('text.rmed', alias))


def list_locs(source: CommandSource):
    text, num = RTextList(tr('text.list_title', len(config.ez_teleport_destnations))), 1
    for loc in config.ez_teleport_destnations:  # type: EzTeleportLocations
        alias_text = RText(loc.alias, RColor.light_purple)
        if loc.ensure_existance():
            alias_text = alias_text.c(RAction.run_command, f'{TP_PREFIX} {loc.alias}').h('hover.tp_to')
        text.append('\n', f'[{num}] ', alias_text, ' §7->§r ')
        if loc.ensure_existance():
            text.append(
                RText(loc.location_name, RColor.dark_purple).c(
                    RAction.run_command, f'{LOC_PREFIX} info {loc.location_name}').h(tr('hover.show_loc'))
            )
        else:
            text.append(
                RText(loc.location_name, RColor.dark_gray, RStyle.strikethrough).h(tr('hover.invalid_loc'))
            )
        num += 1
    source.reply(text)


def sweep_locs(source: CommandSource):
    num = config.remove_invalid().get_return_value(block=True)
    source.reply(tr('text.swept', num))


# Teleport to any dimensions
@ensure_player
@new_thread(META.name.replace(" ", ""))
def tp_player_loc(source: PlayerCommandSource, target: str):
    is_added = False
    for loc in config.ez_teleport_destnations:
        if target == loc.alias and loc.ensure_existance():
            is_added = True
            break
    player_list = {}
    for p in get_server_player_list()[2]:
        player_list[p.lower()] = p
    if is_added:
        loc = config.get_location(target)
        dim, pos = Dimension(loc.dim).name, ' '.join((str(loc.pos.x), str(loc.pos.y), str(loc.pos.z)))
        source.get_server().execute(f'execute in {dim} run tp {source.player} {pos}')
        print_tp_message(source)
    elif target.lower() in player_list.keys():
        dim, pos = Dimension(get_player_dimension(player_list[target.lower()])).name, target
        source.get_server().execute(f'execute in {dim} run tp {source.player} {pos}')
        print_tp_message(source)
    else:
        invalid_tp_target(source)


@ensure_player
@new_thread(META.name.replace(" ", ""))
def tp_coordinate(source: PlayerCommandSource, target: str, y: str, z: str):
    x = target
    char_read = 1
    dim = Dimension(get_player_dimension(source.player)).name
    try:
        x, y, z = float(x), float(y), float(z)
    except ValueError:
        for num in (x, y, z):
            if num != '~' and not isinstance(num, float):
                cmd_error(source)
                return
            char_read += 1

    source.get_server().execute(f'execute in {dim} tp {source.player} {x} {y} {z}')
    global_server.logger.debug(f'execute in {dim} tp {source.player} {x} {y} {z}')
    print_tp_message(source)


# Teleport to specified dimension
@ensure_player
@new_thread(META.name.replace(" ", ""))
def tp_to_corresponding(source: PlayerCommandSource, context: CommandContext):
    dim = Dimension.get(context.command.split(' ')[0])
    global_server.logger.debug(f'Target dim: {dim.name}')
    current_dim = get_player_dimension(source.player)
    global_server.logger.debug(f'Current dim: {Dimension(current_dim).name}')
    if current_dim == dim.value:
        source.reply(
            RText(tr('text.same_dim')).c(RAction.run_command, f'{dim.prefix} default').h(tr('hover.same_dim'))
        )
    else:
        if current_dim < 1 and dim.value < 1:
            loc = get_player_coordinate(source.player)
            if current_dim == 0:
                x, z = loc.x / 8, loc.z / 8
            else:
                x, z = loc.x * 8, loc.z * 8

            source.get_server().execute(f'execute in {dim.name} run tp {source.player} {x} {loc.y} {z}')
            print_tp_message(source)
        else:
            tp_to_default_loc(source, context)


@ensure_player
def tp_to_specified_coordinates(source: PlayerCommandSource, context: CommandContext):
    dim = Dimension.get(context.command.split(' ')[0])
    try:
        loc = f"{float(context['x'])} {float(context['y'])} {float(context['z'])}"
    except ValueError:
        char_read, loc = 1, ''
        for num in (context['x'], context['y'], context['z']):
            if num != '~':
                raise IllegalArgument("Coordinate value should be float or '~'", char_read)
            char_read += 1
            loc += f' {num}'
    source.get_server().execute(f'execute in {dim.name} run tp {source.player} {loc.strip()}')
    print_tp_message(source)


@ensure_player
def tp_to_default_loc(source: PlayerCommandSource, context: CommandContext):
    dim = Dimension.get(context.command.split(' ')[0])
    target = Coordinate.deserialize(config.default_waypoints.serialize()[dim.name])
    source.get_server().execute(f'execute in {dim.name} run tp {source.player} {target.text}')
    print_tp_message(source)


# Errors
def invalid_tp_target(source: CommandSource):
    source.reply(tr(
        'error.not_found',
        RText(tr('element.click'), RColor.gray).c(
            RAction.run_command, f'{TP_PREFIX} list').h(tr('hover.list_locs')),
        RText(f"§7{tr('element.click')}§r").c(
            RAction.run_command, '/list').h(tr('hover.list_players')))
    )


def loc_already_exist(source: CommandSource):
    source.reply(tr('error.already_exist', RText(tr('element.click')).c(
        RAction.run_command, f'{TP_PREFIX} list').h(tr('hover.list_locs')).set_color(RColor.gray)))


def loc_not_found(source: CommandSource):
    source.reply(tr('error.loc_not_found', RText(tr('element.click')).c(
            RAction.run_command, f'{TP_PREFIX} list').h(tr('hover.list_locs')).set_color(RColor.gray)))


def cmd_error(source: CommandSource):
    source.reply(RText(tr('error.cmd'), color=RColor.red).c(RAction.run_command, TP_PREFIX).h(tr('hover.get_help')))


def source_is_not_player(source: CommandSource):
    source.reply(RText(tr('error.not_player_src'), color=RColor.red))


def on_load(server: PluginServerInterface, prev_module):
    def debug(self: MCDReforgedLogger, *args, option=None, no_check=False):
        if DEBUG_MODE:
            super(MCDReforgedLogger, self).debug(*args)
    server.logger.debug = MethodType(debug, server.logger)
    server.register_help_message(TP_PREFIX, tr('reg_help_msg'))

    def eprefix(literal: Union[Iterable, str]):
        return Literal(literal).on_child_error(CommandError, cmd_error, handled=True).on_child_error(
            SourceIsNotPlayer, source_is_not_player, handled=True)

    server.register_command(
        eprefix(TP_PREFIX).runs(show_help).then(
            Literal('add').then(
                QuotableText('alias').then(
                    QuotableText('loc').runs(lambda src, ctx: add_loc(src, **ctx))))).then(
            Literal('list').runs(list_locs)).then(
            Literal('sweep').runs(sweep_locs)).then(
            Literal('rm').then(
                QuotableText('alias').runs(lambda src, ctx: rm_loc(src, **ctx)))).then(
            QuotableText('target').runs(lambda src, ctx: tp_player_loc(src, ctx['target'])).then(
                QuotableText('y').then(
                    QuotableText('z').runs(lambda src, ctx: tp_coordinate(src, ctx['target'], ctx['y'], ctx['z'])))))
    )
    for dim in [Dimension.overworld, Dimension.the_nether, Dimension.the_end]:   # type: Dimension
        server.logger.debug(f'Registered command {dim.prefix} for {dim.name}')
        server.register_command(
            eprefix(dim.prefix).runs(lambda src, ctx: tp_to_corresponding(src, ctx)).then(
                Literal('default').runs(lambda src, ctx: tp_to_default_loc(src, ctx))
            ).then(
                QuotableText('x').then(
                    QuotableText('y').then(
                        QuotableText('z').runs(lambda src, ctx: tp_to_specified_coordinates(src, ctx))
                    ))))
