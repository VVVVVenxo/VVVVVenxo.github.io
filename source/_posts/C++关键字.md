---
title: C++关键字
toc: true
categories:
  - 知识搬运
  - C++
tags:
  - 关键字
  - 类型转换
description: 详解 C++ 中的四种类型转换关键字：const_cast、static_cast、dynamic_cast 和 reinterpret_cast，分析它们的使用场景和区别。
---

## C++ 类型转换关键字
1. const_cast:：把const属性去掉，即将const转换为非const（也可以反过来），const_cast只能用于指针或引用，并且只能改变对象的底层const（顶层const，本身是const，底层const，指向对象const）；
2. static_cast:：隐式类型转换，可以实现C++中内置基本数据类型之间的相互转换，enum、struct、 int、char、float等，能进行类层次间的向上类型转换和向下类型转换（向下不安全，因为没有进行动态类型检查）。它不能进行无关类型(如非基类和子类)指针之间的转换，也不能作用包含底层const的对象；
3. dynamic_cast：动态类型转换，用于将基类的指针或引用安全地转换成派生类的指针或引用（也可以向上转换），若指针转换失败返回NULL，若引用返回失败抛出bad_cast异常。dynamic_cast是在运行时进行安全性检查；使用dynamic_cast父类一定要有虚函数，否则编译不通过；
4. reinterpret_cast：reinterpret是重新解释的意思，此标识符的意思即为将数据的二进制形式重新解释，但是不改变其值，有着和C风格的强制转换同样的能力。它可以转化任何内置的数据类型为其他任何的数据类型，也可以转化任何指针类型为其他的类型。它甚至可以转化内置的数据类型为指针，无须考虑类型安全或者常量的情形。不到万不得已绝对不用（比较不安全）。

>**static_cast和dynamic_cast的异同点？**
>二者都会做类型安全检查，只是static_cast在编译期进行类型检查，dynamic_cast在运行期进行类型检查。后者需要父类具备虚函数，而前者不需要。