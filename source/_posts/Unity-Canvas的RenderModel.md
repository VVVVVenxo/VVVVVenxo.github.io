---
title: Unity-Canvas的RenderModel
toc: true
tag: Unity
---


1. Screen Space -OverLay:只显示所创建的canvas中的内容，即只渲染画布。
2. Screen Space-Camera：只显示相机所渲染的区域，当保证camera的projection是perspective（透视模式）而不是（orthogonality）正交模式的时候通过调整canvas中image或其他物体的Rotation可以制作3D立体效果的UI，但是这种模式下不可以更改Canvas的ReactTransform,只能通过相机来调整canvas的显示位置和显示大小。
3. World Space：canvas的ReacTransform完全可以编辑并且把canvas完全当成一个普通的类似于Cube的物体在场景中进行渲染，仔细考虑一下这种模式，如果你把canvas赋给游戏人物，那么你会发现这种模式适合给人物做血条或者在场景中一直在游戏人物的头顶显示人物名称。