---
title: C++中的Static
toc: true
categories:
  - 编程语言
  - C++
tags:
  - 关键字
  - static
  - 单例模式
description: 理解 C++ 中 static 关键字的作用：静态数据成员、静态成员函数，以及如何利用 static 实现单例模式。
---

## Static 关键字概述

在一个数据或函数前面加一个 `static` 关键字，就会变成静态的。

相同的函数 通过传入不同的this ptr（地址），才可以处理到不同的数据

加入static关键字的数据，就和对象脱离了，它不属于对象，它在内存里单独有一份内存空间。

如果只需要有一份数据来共享使用 那么就使用静态数据。

静态函数也只有一份。

什么时候使用：

静态函数**没有this ptr**，那么就没办法像一般的成员函数一样去处理一般的成员数据。

只能去存取、处理静态的数据

如果是静态的数据 则需要在class的外头进行定义（获得内存空间）。

调用static函数的方式：

1. 通过object嗲用
2. 通过class name调用。

```cpp
class Account {
public:
	static double rate;
	static void set_rate (const double& x) {rate = x}	
};

// 需要在class的外头进行定义（分配内存空间）。
double Account::rate = 8.0;

int main() {
	Account::set_rate(5.0);
	
	Account a;
	a.set_rate(7.0);
}
```

- 扩展：只需要产生一个对象（**单例模式**）
- 把ctors放在private区 不希望外部进行创建

```cpp
class A {
public: 
	// 外界只能通过这个函数得到唯一的这个A
	static A& getInstance(return a;);
	
	// 成员函数
	setup() {...}
	
private:
	A();
	A(const A& rhs);
	static A a;
};

// 外部调用A里的成员函数
A::getInstance().setup();
```

上述例子不好的地方，如果说这个类没有被调用 那么仍然会有一个静态的A存在，有点浪费内存空间

优化：

把static的定义放在getInstance()函数里：
```cpp
class A {
public: 
	// 外界只能通过这个函数得到唯一的这个A
	static A& getInstance(return a;);
	
	// 成员函数
	setup() {...}
	
private:
	A();
	A(const A& rhs);
	// static A a; 去掉了
};

// 在函数里的静态数据 好处：只有当有人调用到的时候才会分配内存
A& A::getInstance() {
// 在这里进行定义（获得内存）
	static A a;
	return a;
} 
```