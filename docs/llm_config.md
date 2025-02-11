# SiliconFlow 大模型 API 配置

1. 申请大模型API
目前国内多家大模型厂商都提供了API接口，可以自行申请。
也可以使用中转站，使用 OpenAI 或 Claude的API。


这里以国内的 [SiliconCloud](https://cloud.siliconflow.cn/i/onCHcaDx) 的 API 为例子，其已经集合国内多家大模型厂商。（注意以上是我的推广链接，通过此可以获得14元额度，介意就百度自行搜索注册，非广告）

![api](images/get_api.png)

注册后，在[设置](https://cloud.siliconflow.cn/account/ak)中获取API Key。

![config](images/api-setting.png)

API 接口地址： https://api.siliconflow.cn/v1 （需要添加 /v1）

API Key： 将 SiliconCloud 平台的密钥粘贴到此处。

点击检查连接，“模型”设置栏会自动填充所有支持的模型名称。

选择需要的模型名称，推荐：deepseek-ai/DeepSeek-V3

> 2025 年 2 月 6 日起，未实名用户每日最多请求此模型 100 次

根据官方要求该模型需要实名才能获取更多的调用次数。不想实名可以考虑使用其他中转站。

还有两个重要参数需要配置:

`1. 批处理大小 (Batch Size)`

此参数决定每次向大模型发送的字幕条数。就像是一次性给大模型看多少句话:
- 数值越大,携带的上下文信息越丰富
- 但也会增加处理出错的风险

🔸 推荐: 10条

`2. 线程数 (Thread Count)`

控制同时处理字幕的线程数量。形象地说,这就像餐厅的厨师数量:
- 线程越多,处理速度越快
- 但要考虑服务商的并发限制

建议根据实际情况灵活设置,在服务商允许的范围内尽可能调高。

🔸 SiliconCloud API 推荐设置: 5个线程


# 中转站配置


1. 先在 [本项目的中转站](https://api.videocaptioner.cn) 注册账号
,通过此链接注册默认赠送 $0.4 测试余额。

2. 然后获取 API Key： [https://api.videocaptioner.cn/token](https://api.videocaptioner.cn/token)


3. 在软件设置中配置 API Key 和 API 接口地址, 如下图：

![api_setting](images/api-setting-2.png)

BaseURL: `https://api.videocaptioner.cn/v1`


API-key: `路上面获取的API Key`

💡 模型选择建议 (本人在各质量层级中精选出的高性价比模型)： 

 - 高质量之选： `claude-3-5-sonnet-20241022` (耗费比例：3) 

 - 较高质量之选： `gemini-2.0-flash`、`deepseek-chat` (耗费比例：1) 

 - 中质量之选： `gpt-4o-mini`、`gemini-1.5-flash` (耗费比例：0.15) 

本站支持超高并发，软件中线程数直接拉满即可~ 处理速度非常快~


`线程数 (Thread Count)`: 可直接拉满







