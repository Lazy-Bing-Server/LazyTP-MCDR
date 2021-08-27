# Lazy Teleport

**创造模式增强插件工坊** 第一弹

I have no time to translate this properly, so english language support for this plugin is awful, and this page has no english edition
我没有时间把它翻译完, 故本插件的英文支持很差, 且本页面是没有英文的

## 简介
快捷的维度间传送通道。同时提供快速传送到服务器路径点功能
## 适用场景
适用于主世界和下界间对应坐标免建造门直接传送和少量常用名称好记的路径点的免查询和免确认的传送（借助Location Marker实现）
## 依赖
- [MCDReforged](https://github.com/Fallen-Breath/MCDReforged/) **>= 2.1.0**
- [Minecraft Data API](https://github.com/MCDReforged/MinecraftDataAPI/) >= 1.4.0
- [Location Marker](https://github.com/TISUnion/LocationMarker) >= 1.3.0
- [WorldEdit](https://www.curseforge.com/minecraft/mc-mods/worldedit)（可选，传送后脱困需要创世神，无需脱困功能或服务端无创世神可在配置文件中设置`"we_unstuck"`为false）
## 下一步更新方向
可能将通过 [ChatBridgeReforged](https://github.com/rickyhoho/ChatBridgeReforged) 实现创造服务器之间的相互传送
## 服务端配置
玩家指令无法执行首选操作时都会被返回信息引导到默认路径点，而末地的首选传送行为就是前往默认路径点，故每个维度名为`default`的路径点**必须**存在并填写有效坐标。玩家传送后可能被困在实心位置，将`"we_unstuck"`设置为true会在玩家传送后显示一个提示，点击该提示以执行创世神的脱困(/unstuck)指令。
## 客户端指令
在MC客户端内可输入如下指令：
1. `!!overworld`和`!!nether`
直接使用将传送玩家到玩家对维度的对应坐标（和下界传送门对应关系相同）。
若输入了同维度将报错并询问是否前往服务器管理员设定的维度默认导航点。
若玩家在末路之地则直接传送玩家到输入指令对应维度的默认导航点。
2. `!!end`直接输入将传送到末路之地默认导航点。若已在末地将报错并询问是否前往末地默认导航点。
 
以下将使用`<Prefix>`替代指令前缀`!!overworld`, `!!nether`或`!!end`

3. `<Prefix> <x> <y> <z>`
传送到指令对应维度`<x>`,`<y>`,`<z>`处
4. `<Prefix> default`
传送到默认坐标点。**无需确认**

如下指令的前缀均为`!!tp`

5. `!!tp list`
列出路径点列表
6. `!!tp <x> <y> <z>`
传送到当前维度的指定点 
7. `!!tp <alias>/<player>`
传送到预存的一个坐标点或者玩家 **无需确认**
8. `!!tp add <alias> <loc>` 和 `!!tp rm <alias>`
从Location Marker的`<loc>`坐标点保存一个快速坐标点/移除一个预存坐标（不影响LocationMarker的数据）
9. `!!tp sweep`
清理已不存在于LocationMarker的路径点

## 注意事项
当前版本的配置文件与旧版本互不兼容（虽然八成也没人用这玩意）
