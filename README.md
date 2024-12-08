# This Project is used to parse a video web side to remove ads.

Author：[jaysen.lin@foxmail.com](mailto://jaysen.lin@foxmail.com)

此项目是为了解析一个视频网站，去除广告，使得看视频时，点击网站的任何链接或按钮不在被广告跳转而干扰。

# 项目结构
采用的是python的Flask网站引擎框架。结合了解析框架：BeautifulSoup4解析DOM，和urllib的标准库request请求网络。
- beautifulsoup4
- Flask
- urllib

# 安装依赖
```dos
pip install -r requirments.txt
```
# 运行项目
```console
$ py3 main.py
```

# 在浏览器打开本地网站首页

地址是:[http://172.0.0.1:5000](http://172.0.0.1:5000)


