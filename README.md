# Lazy Teleport
## 简介
快捷的维度间传送通道，同维度传送请直接/tp。同时提供快速传送到服务器路径点功能。
## 适用场景
适用于主世界和下界间对应坐标免建造门直接传送和少量常用名称好记的路径点的免查询和免确认的传送。如果需要可由玩家自己配置路径点的路径点插件，请使用Fallen_Breath的[Location Marker](https://github.com/TISUnion/LocationMarker)，本插件仅提供可由服务器管理员定义的路径点功能。
## 依赖
- [MCDReforged](https://github.com/Fallen-Breath/MCDReforged/) 1.x
- [Minecraft Data API](https://github.com/MCDReforged/MinecraftDataAPI/)
## 服务端配置
默认指令前缀和服务器路径点可由服务器管理员在MCDR目录下的`config/lazytp.json`中配置
## 客户端指令
在MC客户端内可输入如下指令：
1. `!!overworld`和`!!nether`
直接使用将传送玩家到玩家对维度的对应坐标（和下界传送门对应关系相同）。
若输入了同维度将报错并询问是否前往服务器管理员设定的维度默认导航点。
若玩家在末路之地则直接传送玩家到输入指令对应维度的默认导航点。
2. `!!end`直接输入将传送到末路之地出生点（可以在MCDR运行目录的`config/lazytp.json`中修改）。
 
如下将使用`<Prefix>`替代指令前缀`!!overworld`, `!!nether`或`!!end`

3.	`<Prefix> <x> <y> <z>`
传送到指令对应维度`<x>`,`<y>`,`<z>`处，**无需确认**。
4.	`<Prefix> <waypoint>`
传送到服务器管理员设定的路径点，**无需确认**，要求路径点名称`<waypoint>`全字匹配（路径点可能重名，请务必对应维度）。
5.	`<Prefix> list`
列出服务器管理员设定在该维度的路径点。
6.	`<Prefix> listall`
列出服务器管理员设定的所有路径点。
7.	`<Prefix> help`
显示该插件帮助信息。
