from mcdreforged.api.types import PluginServerInterface, PlayerCommandSource, CommandSource
from mcdreforged.api.command import *
from mcdreforged.api.rtext import *
from typing import Iterable, Union, Callable

from location_marker.constants import PREFIX as LOC_PREFIX
from minecraft_data_api import get_player_coordinate, get_server_player_list, get_player_dimension
from lazytp.constants import TP_PREFIX, global_server, META
from lazytp.storage import config, Dimension, LocationNotFound, LocationAlreadyExist


class SourceIsNotPlayer(CommandError):
    def __init__(self):
        super(SourceIsNotPlayer, self).__init__('Command is not from a player', '', '')


# Utilities
def tr(key: str, *args, **kwargs):
    return global_server.tr(f'{META.id}.{key}', *args, **kwargs)


def show_help(source: CommandSource):
    source.reply(tr('help_msg', TP_PREFIX, META.id, str(META.version)))


def print_tp_message(source: PlayerCommandSource):
    source.reply(
        tr('text.tp') + (RText(tr('lazytp.text.unstuck')).c(
            RAction.run_command, '/unstuck').h(tr('hover.unstuck')) if config.we_unstuck else '')
    )


def ensure_player(func: Callable):
    def wrapper(source: CommandSource, *args, **kwargs):
        if not isinstance(PlayerCommandSource, str):
            raise SourceIsNotPlayer()
        func(source, *args, **kwargs)
    return wrapper


# TP preset management
def add_loc(source: CommandSource, alias: str, loc: str):
    try:
        config.add_wp(alias, loc)
    except LocationAlreadyExist:
        loc_not_found(source)
    else:
        source.reply(tr('text.rmed', alias))


def rm_loc(source: CommandSource, alias: str):
    try:
        config.rm_wp(alias)
    except LocationNotFound:
        loc_not_found(source)
    else:
        source.reply(tr('text.rmed', alias))


def list_locs(source: CommandSource):
    text, num = RTextList(tr('text.list_title', len(config.ez_teleport_destnations))), 1
    for loc in config.ez_teleport_destnations:
        text.append(
            '\n', f'[{num}] ', RText(loc.alias, RColor.light_purple).c(RAction.run_command, f'{TP_PREFIX} {loc.alias}'),
            ' §7->§r ', RText(loc.name, RColor.dark_purple).c(RAction.run_command, f'{LOC_PREFIX} info {loc.alias}')
        )
        num += 1
    source.reply(text)


def sweep_locs(source: CommandSource):
    num = config.remove_invalid().get_return_value(block=True)
    source.reply(tr('text.swept', num))


# Teleport to any dimensions
@ensure_player
def tp_player_loc(source: PlayerCommandSource, target: str):
    if target in config.ez_teleport_destnations:
        loc = config.get_location(target)
        dim, pos = Dimension(loc.dim).name, ' '.join(list(iter(loc.pos)))
        source.get_server().execute(f'execute in {dim} run tp {pos}')
        print_tp_message(source)
    elif target in get_server_player_list()[2]:
        dim, pos = get_player_dimension(target), target
        source.get_server().execute(f'execute in {dim} run tp {pos}')
        print_tp_message(source)
    else:
        invalid_tp_target(source)


@ensure_player
def tp_coordinate(source: PlayerCommandSource, target: str, y: str, z: str):
    x = target
    char_read = 1
    for num in (x, y, z):
        if num != '~' and not isinstance(num, float):
            raise IllegalArgument("Coordinate value should be float or '~'", char_read)
        char_read += 1
    source.get_server().execute(f'tp {x} {y} {z}')
    print_tp_message(source)


# Teleport to specified dimension
@ensure_player
def tp_to_corresponding(source: PlayerCommandSource, dim: Dimension):
    current_dim = get_player_dimension(source.player)
    if current_dim == dim.value:
        source.reply(
            RText(tr('text.same_dim').c(RAction.run_command, f'{dim.prefix} default').h(tr('hover.same_dim')))
        )
    else:
        if current_dim < 1 and dim.value < 1:
            loc = get_player_coordinate(source.player)
            if current_dim == 0:
                loc.x, loc.z = loc.x / 8, loc.z / 8
            else:
                loc.x, loc.z = loc.x * 8, loc.z * 8
            source.get_server().execute(f'execute in {dim.name} run tp {loc.x} {loc.y} {loc.z}')
            print_tp_message(source)
        else:
            tp_to_default_loc(source, dim)


@ensure_player
def tp_to_specified_coordinates(source: PlayerCommandSource, x: str, y: str, z: str, dim: Dimension):
    char_read = 1
    for num in (x, y, z):
        if num != '~' and not isinstance(num, float):
            raise IllegalArgument("Coordinate value should be float or '~'", char_read)
        char_read += 1
    source.get_server().execute(f'excuted in {dim.name} run tp {x} {y} {z}')
    print_tp_message(source)


@ensure_player
def tp_to_default_loc(source: PlayerCommandSource, dim: Dimension):
    target = config.default_waypoints.serialize()[dim.name].text
    source.get_server().execute(f'execute in {dim.name} run tp {target.text}')
    print_tp_message(source)


# Errors
def invalid_tp_target(source: CommandSource):
    source.reply(RText.format(
        tr('error.not_found'),
        RText(tr('element.click')).c(
            RAction.run_command, f'{TP_PREFIX} list').h(tr('hover.list_locs')).set_color(RColor.gray),
        RText(tr('element.click')).c(
            RAction.run_command, 'list').h(tr('hover.list_players')).set_hover_text(RColor.gray)
    ))


def loc_already_exist(source: CommandSource):
    source.reply(RText.format(tr('text.loc_not_found'), RText(tr('element.click')).c(
        RAction.run_command, f'{TP_PREFIX} list').h(tr('hover.list_locs')).set_color(RColor.gray)))


def loc_not_found(source: CommandSource):
    source.reply(RText.format(tr('text.loc_not_found'), RText(tr('element.click')).c(
            RAction.run_command, f'{TP_PREFIX} list').h(tr('hover.list_locs')).set_color(RColor.gray)))


def cmd_error(source: CommandSource):
    source.reply(RText(tr('error.cmd'), color=RColor.red).c(RAction.run_command, TP_PREFIX).h(tr('hover.get_help')))


def source_is_not_player(source: CommandSource):
    source.reply(RText(tr('error.not_player_src'), color=RColor.red))


def on_load(server: PluginServerInterface, prev_module):
    server.register_help_message(TP_PREFIX, tr('reg_help_msg'))

    def eprefix(literal: Union[Iterable, str]):
        return Literal(literal).on_child_error(CommandError, cmd_error, handled=True).on_child_error(
            SourceIsNotPlayer, source_is_not_player, handled=True)

    server.register_command(
        eprefix('!!tp').then(
            Literal('add').then(
                QuotableText('alias').then(
                    QuotableText('loc').runs(lambda src, ctx: add_loc(src, **ctx))))).then(
            Literal('list').runs(list_locs)).then(
            Literal('sweep').runs(sweep_locs)).then(
            Literal('rm').then(
                QuotableText('alias').runs(lambda src, ctx: rm_loc(src, **ctx)))).then(
            QuotableText('target').runs(lambda src, ctx: tp_player_loc(src, **ctx)).then(
                QuotableText('y').then(
                    QuotableText('z').runs(lambda src, ctx: tp_coordinate(src, **ctx)))))
    )
    for dim in Dimension:   # type: Dimension
        server.register_command(
            eprefix(dim.prefix).runs(lambda src: tp_to_corresponding(src, dim=dim)).then(
                Literal('default').runs(lambda src: tp_to_default_loc(src, dim=dim))
            ).then(
                QuotableText('x').then(
                    QuotableText('y').then(
                        QuotableText('z').runs(lambda src, ctx: tp_to_specified_coordinates(src, **ctx, dim=dim))
                    ))))
