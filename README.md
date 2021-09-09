# AgefansCrawler
 从Agefans网站上下载动漫
## 安装
- 在cmd输入`git clone https://github.com/ChinHongTan/AgefansCrawler`

- 完成后用cd命令进入文件夹，输入`pip install -r requirements.txt`

- 输入`py agefanscrawler.py`即可运行程序


这是一个我自己改进后的爬虫，原作者：https://blog.csdn.net/qq_44700693/article/details/107510787

从 https://agefans.org/ 上搜寻并下载动漫

下载之后的动漫会储存在Spider文件夹中

在程序显示下载完成之前请不要终止程序，不然下载到一半的文件就要删掉重新下载

程序也会打印出动漫每一集的下载链接，如果下载有缺失可以使用链接在浏览器手动下载

我已经尽我所能提升了爬虫的下载速度，运用了多线程达到尽量高的下载速度

目前来看这个爬虫能达到很高的下载速度，但是由于我的网速并不算很高，不能测试最大的下载速度

目前的问题是有一些动漫会出现很奇怪的503错误，还没有找到解决方法

还有一些动漫是.m3u8格式，无法下载（我是尝试了很久不过都不能成功下载下来）

如果有人愿意提出任何建议/贡献都十分欢迎！
