from playhouse.shortcuts import model_to_dict

from pyplanet.apps.core.maniaplanet.models import Map
from pyplanet.views.generics.list import ManualListView

from pyplanet.utils import times


class JukeboxListView(ManualListView):
	app = None

	title = 'Currently in the Jukebox'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Browse'

	data = []

	def __init__(self, app):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui

	async def get_fields(self):
		return [
			{
				'name': '#',
				'index': 'index',
				'sorting': True,
				'searching': False,
				'width': 10,
				'type': 'label'
			},
			{
				'name': 'Map',
				'index': 'map_name',
				'sorting': True,
				'searching': True,
				'width': 100,
				'type': 'label',
				'action': self.action_drop
			},
			{
				'name': 'Requested by',
				'index': 'player_nickname',
				'sorting': True,
				'searching': False,
				'width': 50
			},
		]

	async def action_drop(self, player, values, instance, **kwargs):
		await self.app.drop_from_jukebox(player, instance)

	async def get_data(self):
		index = 1
		items = []
		for item in self.app.jukebox:
			items.append({'index': index, 'map_name': item['map'].name, 'player_nickname': item['player'].nickname,
						  'player_login': item['player'].login})
			index += 1

		return items


class MapListView(ManualListView):
	model = Map
	title = 'Maps on this server'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Browse'

	custom_actions = list()

	def __init__(self, app):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui

	async def get_data(self):
		return [model_to_dict(m) for m in self.app.instance.map_manager.maps]

	async def get_fields(self):
		return [
			{
				'name': 'Name',
				'index': 'name',
				'sorting': True,
				'searching': True,
				'search_strip_styles': True,
				'width': 100,
				'type': 'label',
				'action': self.action_jukebox
			},
			{
				'name': 'Author',
				'index': 'author_login',
				'sorting': True,
				'searching': True,
				'search_strip_styles': True,
				'renderer': lambda row, field:
					row['author_login'],
					# TODO: Activate after resolving #83.
					# row['author_nickname']
					# if 'author_nickname' in row and row['author_nickname'] and len(row['author_nickname'])
					# else row['author_login'],
				'width': 50,
			},
		]

	async def get_actions(self):
		return self.custom_actions

	async def get_buttons(self):
		return [
			{
				'title': 'Folders',
				'width': 20,
				'action': self.action_folders
			}
		]

	async def action_jukebox(self, player, values, map_info, **kwargs):
		await self.app.add_to_jukebox(player, await self.app.instance.map_manager.get_map(map_info['uid']))

	async def action_folders(self, player, values, **kwargs):
		await self.app.folder_manager.display_folder_list(player)

	@classmethod
	def add_action(cls, target, name, text, text_size='1.2', require_confirm=False):
		cls.custom_actions.append(dict(
			name=name,
			action=target,
			text=text,
			textsize=text_size,
			safe=True,
			type='label',
			require_confirm=require_confirm,
		))

	@classmethod
	def remove_action(cls, target):
		for idx, custom in enumerate(cls.custom_actions):
			if custom['action'] == target:
				del cls.custom_actions[idx]


class FolderMapListView(MapListView):
	def __init__(self, app, map_list, fields):
		super().__init__(app)

		self.map_list = map_list
		self.fields = fields

	async def get_fields(self):
		fields = await super().get_fields()

		for field in self.fields:
			fields.append(field)

		return fields

	async def get_data(self):
		karma = any(f['index'] == "karma" for f in self.fields)
		length = any(f['index'] == "local_record" for f in self.fields)

		items = []
		for item in self.map_list:
			dict_item = model_to_dict(item)
			if length:
				dict_item['local_record'] = times.format_time((item.local['first_record'].score if hasattr(item, 'local') else 0))
			if karma:
				dict_item['karma'] = item.karma['map_karma'] if hasattr(item, 'karma') else 0
			items.append(dict_item)

		return items


class FolderListView(ManualListView):
	title = 'Maplist folders'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Browse'

	def __init__(self, folder_manager, player):
		super().__init__()

		self.folder_manager = folder_manager
		self.player = player
		self.app = folder_manager.app
		self.manager = folder_manager.app.context.ui

	@staticmethod
	def render_folder_name(row, field):
		icon = ''
		if row['type'] == 'auto':
			icon = '\uf013'
		elif row['type'] == 'public':
			icon = '\uf0c0'
		elif row['type'] == 'private':
			icon = '\uf023'

		return '{} {}'.format(icon, row[field['index']])

	async def get_fields(self):
		return [
			{
				'name': 'Folder',
				'index': 'name',
				'sorting': False,
				'searching': True,
				'width': 140,
				'renderer': self.render_folder_name,
				'type': 'label',
				'action': self.action_show
			},
			{
				'name': 'Type',
				'index': 'type',
				'sorting': True,
				'searching': False,
				'width': 30,
				'renderer': lambda row, field:
					row[field['index']].capitalize(),
				'type': 'label'
			},
			{
				'name': 'Owner',
				'index': 'owner',
				'sorting': False,
				'searching': False,
				'width': 80,
			},
		]

	async def get_buttons(self):
		return [
			{
				'title': 'Create folder',
				'width': 28,
				'action': self.create_folder
			}
		]

	async def action_show(self, player, values, instance, **kwargs):
		await self.folder_manager.display_folder(player, instance)

	async def create_folder(self, player, values, **kwargs):
		pass

	async def get_data(self):
		return await self.folder_manager.get_folders(self.player)
