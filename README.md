# security-config

#### 介绍

请求响应安全中间件（**插拔式组件**）



这个请求响应安全组件是一个基于过滤器的Java组件，为Web应用程序提供了多项安全功能。该组件支持以下五个主要功能：

1. 请求响应加解密：通过对请求和响应数据进行加密和解密，确保数据在传输过程中不被窃取或篡改。
2. 请求响应加签验签：通过对请求和响应数据进行数字签名和验证，确保请求和响应数据的完整性和真实性。
3. 请求参数SQL注入正则匹配：通过对请求参数进行正则匹配，检测是否存在SQL注入攻击，并进行相应的防御措施。
4. 慢接口扫描预警：对请求处理时间较长的接口进行扫描，及时预警并进行优化。
5. 请求Token验证：通过对请求中的Token进行验证，确保请求的来源是合法的，防止恶意攻击。（代码参考sa-token，如需更多token相关功能，可以搜索该项目进行学习和使用https://gitee.com/dromara/sa-token?_from=gitee_search）
6. 请求黑名单IP扫描：通过可配置的形式动态化监控指定接口地址对指定ip定向禁止访问
7. 数据库字段加解密及字段脱敏

以上七个功能均是与业务代码完全解耦，零耦合的基础上该组件每一项功能都可基于配置文件单独开启，功能之间互不依赖，具有很高的灵活性和可配置性



注意：当前项目并未发布maven中央仓库，如需使用请下载源码放入企业私库或项目中自行引入

#### 请求响应加解密配置案例

![输入图片说明](1.png)

**简介**：AES算法完成对于请求解密及响应加密，密钥和偏移量均可自定义输入，没有任何规则限制

**额外特点**：可通过实现**SecurityEncInterface**接口，对加解密方法进行重定义

**注意**：该功能当前仅限于json格式请求的加解密（经个人多番考虑，form-data格式加密的价值不高，因为你需要对多个参数以特殊的标识符拼接成一个字符串交予后端解密，如果请求参数中含有跟标识符同样的字符，则会拿到不正确的参数对）



**详细配置参数：**

```java
/**
 * 请求响应加密参数
 * @author LJJ
 * @Date 2023/1/11 20:34
 */
@Data
@ConfigurationProperties(prefix = "security-enc")
public class SecurityEncProperties {

    private boolean enable;

    /**
     * 需要验签的路径,支持 “*” 通配符,以","分割
     */
    private String encUrls;

    /**
     * 放行的地址, 支持 “*” 通配符
     */
    private List<String> excludeUrls;

    /**
     * GET,POST,PUT,DELETE
     */
    private String methods;

    /**
     * AES密钥
     */
    private String key;

    /**
     * 偏移量
     */
    private String offset;

    /**
     * 加解密类型： ECB/CBC 默认ECB
     */
    private String encType;

}

```

#### 请求响应验签配置案例

![输入图片说明](2.png)

**简介**：RSA算法完成请求的签名认证以及响应信息的生成签名，在前端请求过来的同时需要在请求头(Headers)携带参数名为Sign的签名信息，该签名信息支持form-data及json两种请求的签名认证，不同的请求方式，签名信息的生成有所不同

* form-data：将每一对请求参数以"&"符号拼接在一起，每一对请求参数的键值以"="拼接为字符串(例：name=张三&age=16),然后通过publicKey(公钥)以RSA或RSA2加密存入请求头的sign中
* json: 将json整体作为字符串(可以将整个json先转变为byte数组，再转为字符串，可避免json由于换行符问题而导致的解密失败情况)，然后通过publicKey(公钥)以RSA或RSA2加密存入请求头的sign中

**签名认证逻辑**：通过用privateKey(私钥)对sign进行解密，然后与请求参数比对，完全一致则为验证通过。

**签名认证好处**：有效的防止在请求传输过程中拦截被篡改的请求信息

**额外特点**：可通过实现**SecuritySignInterface**接口，对签名认证、生成签名方法进行重定义

**顺带一嘴**：密钥对的生成在RsaUtil中有相应的方法。响应返回的时候，也会在响应头携带响应信息，前端接收响应信息时可自由选择是否需要对响应进行验签



**详细配置参数：**

```java
/**
 * 验签参数
 * @author LJJ
 * @Date 2023/1/10 10:58
 */
@Data
@ConfigurationProperties(prefix = "security-sign")
public class SecuritySignProperties {

    private boolean enable;

    /**
     * 需要验签的路径,支持 “*” 通配符,以","分割
     */
    private String signUrls;

    /**
     * 放行的地址, 支持 “*” 通配符
     */
    private List<String> excludeUrls;

    /**
     * GET,POST,PUT,DELETE
     */
    private String methods;

    /**
     * 公钥
     */
    private String publicKey;

    /**
     * 私钥
     */
    private String privateKey;

    /**
     * 签名算法: RSA/RSA2
     */
    private String signType;

    /**
     * 请求验签方式: form-data/json
     */
    private String requestType;

}
```

#### 请求sql注入风险扫描配置案例

![输入图片说明](3.png)

**简介**：通过正则表达式进行sql注入风险的最外层拦截

**额外特点**：可通过实现**SecuritySqlInjectionInterface**接口，对sql注入风险判断方法进行重定义



**详细配置参数：**

```java
/**
 * sql注入参数
 * @author jyh
 * @Date 2023/1/13 15:58
 */
@Data
@ConfigurationProperties(prefix = "security-sql-injection")
public class SecuritySqlInjectionProperties {

    private boolean enable;

    /**
     * GET,POST,PUT,DELETE
     */
    private String methods;

    /**
     * 需要验证sql注入的路径,支持 “*” 通配符,以","分割 注入
     */
    private String sqlInjectUrls;

    /**
     * 放行的地址, 支持 “*” 通配符 正则
     */
    private List<String> excludeUrls;

    /**
     * sql注入正则表达
     */
    private String sqlInjectRegex;

}
```

#### 慢接口扫描配置案例

![输入图片说明](4.png)

**简介**：对项目接口性能进行实时监控，高效发掘低性能接口，并且因可配置的形式，可对每一个项目进行更加定制化地性能监控，默认情况下警告信息存入日志，可通过配置平台信息进行平台预警：当前支持平台：**钉钉**、**企业微信**



**详细配置参数：**

```java
/**
 * 方法扫描配置参数
 * @author LJJ
 * @Date 2023/3/2 10:05
 */
@Data
@ConfigurationProperties(prefix = "security-scan")
public class SecurityMethodScanProperties {

    private boolean enable;

    /**
     * 需要方法扫描的路径,支持 “*” 通配符,以","分割
     */
    private String scanUrls;

    /**
     * 放行的地址, 支持 “*” 通配符
     */
    private List<String> excludeUrls;

    /**
     * GET,POST,PUT,DELETE
     */
    private String methods;

    /**
     * 预警阈值，单位s
     */
    private Integer holdTime;


    /**
     * 报警次数：慢接口超过设定次数则报警
     */
    private Integer alarmNum;

    /**
     * 通知平台集合
     */
    private List<NotifyPlatform> platforms;

}
```



#### 请求token验证配置案例

![输入图片说明](5.png)

**简介**：在开启配置后，在自己密码验证成功的逻辑后面调用相应登录方法即可完成token的存入以及开启所有请求的接口验证



**功能方法列表：**



**token登录**

```
/**
 * token登录
 * @param id 账号id，建议的类型：（long | int | String）
*/
SecurityLogin.login(用户id);
```

**退出登录**

```
/**
 * token退出（退出登录:退出header中token账号）无token不生效
*/
SecurityLogin.logout();
```

**如果想要在token里存入额外信息，可在配置tokenStyle: JWT的情况下调用**

```java
SecurityLogin.login(10001, SecurityTokenUtil
  .setExtra("name","Zebord")
  .setExtra("age", 18)
  .setExtra("role", "超级管理员"));
```

**当你想从JWT风格的token中获取你设置的具体的额外信息，比如name属性**

```java
String name = JwtUtils.get(SecurityLogin.getTokenValue(),
                           SecurityLogin.getJwtSecretKey(), "name");
```

**详细配置参数：**

```java
/**
 * token参数
 * @author LJJ
 * @Date 2023/1/10 10:58
 */
@Data
@ConfigurationProperties(prefix = "security-token")
public class SecurityTokenProperties {

    private boolean enable;

    /**
     * 需要验证token的路径,支持 “*” 通配符,以","分割
     */
    private String tokenUrls;

    /**
     * 放行的地址, 支持 “*” 通配符
     */
    private List<String> excludeUrls;

    /**
     * GET,POST,PUT,DELETE
     */
    private String methods;

    /** token名称 (同时也是cookie名称) */
    private String tokenName;

    /** token的长久有效期(单位:秒) 默认30天, -1代表永久 */
    private long timeout = 60 * 60 * 24 * 30;

    /**
     * token临时有效期 [指定时间内无操作就视为token过期] (单位: 秒), 默认-1 代表不限制
     * (例如可以设置为1800代表30分钟内无操作就过期)
     */
    private long activityTimeout = -1;

    /** 是否允许同一账号并发登录 (为true时允许一起登录, 为false时新登录挤掉旧登录) */
    private Boolean isConcurrent = true;

    /** 在多人登录同一账号时，是否共用一个token (为true时所有登录共用一个token, 为false时每次登录新建一个token) */
    private Boolean isShare = true;

    /**
     * 同一账号最大登录数量，-1代表不限 （只有在 isConcurrent=true, isShare=false 时此配置才有效）
     */
    private int maxLoginCount = 12;

    /** 是否尝试从请求体里读取token */
    private Boolean isReadBody = true;

    /** 是否尝试从header里读取token */
    private Boolean isReadHeader = true;

    /** 是否尝试从cookie里读取token */
    private Boolean isReadCookie = false;

    /** 是否在登录后将 Token 写入到响应头 */
    private Boolean isWriteHeader = true;

    /** token风格(默认可取值：uuid、simple-uuid、random-32、random-64、random-128、tik) */
    private String tokenStyle = "uuid";

    /** 默认dao层实现类中，每次清理过期数据间隔的时间 (单位: 秒) ，默认值30秒，设置为-1代表不启动定时清理 */
    private int dataRefreshPeriod = 30;

    /** 获取[token专属session]时是否必须登录 (如果配置为true，会在每次获取[token-session]时校验是否登录) */
    private Boolean tokenSessionCheckLogin = true;

    /** 是否打开自动续签 (如果此值为true, 框架会在每次直接或间接调用getLoginId()时进行一次过期检查与续签操作)  */
    private Boolean autoRenew = true;

    /** token前缀, 格式样例(satoken: Bearer xxxx-xxxx-xxxx-xxxx) */
    private String tokenPrefix;

    /**
     * jwt秘钥 (只有集成 jwt 模块时此参数才会生效)
     */
    private String jwtSecretKey;

}

```

**顺带一嘴：**(在默认情况下我们的token是存入在jvm内存中，如需存入三方缓存，可参考下方配置集成redis)



##### 	Token验证集成redis，通过enabled控制token是否存入redis

![输入图片说明](6.png)



**注意：插拔式token灵感来源于sa-token，只具备其极小部分功能，如果你对token方面想要有更深入更多样性的使用或学习，可前往[sa-token](https://gitee.com/dromara/sa-token?_from=gitee_search)**



#### 请求黑名单IP扫描配置案例

![输入图片说明](7.png)

**简介：**黑名单IP校验功能，通过可配置的形式动态化监控指定接口地址对指定ip定向禁止访问



##### 配置参数

```java
	private boolean enable;

    /**
     * 需要方法扫描的路径,支持 “*” 通配符,以","分割
     */
    private String scanUrls;

    /**
     * 放行的地址, 支持 “*” 通配符
     */
    private List<String> excludeUrls;

    /**
     * GET,POST,PUT,DELETE
     */
    private String methods;

    /**
     * 黑名单ip集合
     */
    private List<String> blackIpList;
```

## 

#### 数据库加解密及字段脱敏功能
* 启动类加```@EnableMybatisSecret```注解开启数据库加解密及字段脱敏功能



* 配置参数：

  ```java
    @Data
    @Configuration
    @ConfigurationProperties(prefix = "mybatis-secret")
    public class EncryptorProperties {

    /**
     * 前缀(非必填)
     */
    private String prefix;

    /**
     * 密钥
     */
    private String key;

    /**
     * 偏移量
     */
    private String offset;


}

  ```

#### @SensitiveData

加解密实体类注解，要加解密一些字段的时候，需要在实体类上添加

```java
   @SensitiveData
   public class TestEntity implements Serializable {
   
   }
```

#### @SensitiveField

字段加解密注解，作用在字段上。

```java
   @SensitiveField
   private String name;
   
   @SensitiveField(supportLike = true, regex = RegexEnum.NAME)
   private String nameLike;
```

1. regex `分段加密规则`<br>
   目前支持姓名、手机号和身份证号分段加密。（**_注意分段加密后的密文会成倍增长，慎重考虑_**）<br>
   `RegexConfig.NAME = "1";//姓名按照每1位字符分段，如张三：张、三分段加密>`<br>
   `RegexConfig.PHONE = "3|4|4";//手机号11位按照3、4、4分段，如18912346611：189、1234、6611分段加密`<br>
   `RegexConfig.ID_CARD = "3|3|4|4|4";//身份证号18位按照3、3、4、4、4分段，如510220199812310310:510、220、1998、1231、0310分段加密`<br>
2. supportLike `支持模糊加密匹配`<br>
   默认不支持模糊加密匹配。（**_注意模糊加密字段不支持解密，只做模糊查询_**）
3. algorithm `加解密算法`<br>
   默认支持AES算法，其它算法未实现。
4. encryptor `加解密处理器`<br>
   默认处理器，自定义加解密处理器未实现。

#### @ParamEncrypt
请求参数加密注解 （**_注意请求参数加密注解必须加在mapper方法上_**）<br>
`fields`填写需要加密的字段
##### 请求参数为String
```java
   @ParamEncrypt(fields = {"phoneLike", "idCardLike"})
   List<String> queryByString(@Param("phoneLike") String phoneLike, @Param("idCardLike") String idCardLike);
```
##### 请求参数为Map
```java
   @ParamEncrypt(fields = {"nameLike", "phoneLike", "idCardLike"})
   List<Map<String, Object>> queryByMap(@Param("param") Map<String, Object> param);
```
##### 请求参数为Entity
请求参数为实体类，需要在实体类加`@SensitiveData`注解，在字段上加`@SensitiveField`。（mapper请求方法可以不加`@ParamEncrypt`注解）
```java
   TestInfo queryByEntity(TestInfo testInfo);
```
##### 请求方式为LambdaQuery
请求方式为lambdaQuery，需要在实体类加`@SensitiveData`注解，在字段上加`@SensitiveField`。（LambdaQuery请求方式可以不加`@ParamEncrypt`注解）<br>
目前支持EQ、NE、LE、GE、GT、IN、LIKE格式
```java
   public List<TestInfo> queryByLambda(@RequestBody TestInfo testInfo) {
     return testInfoService.lambdaQuery()
             .eq(TestInfo::getName, testInfo.getName())
             .ne(TestInfo::getNameLike, testInfo.getNameLike())
             .le(TestInfo::getPhone, testInfo.getPhone())
             .ge(TestInfo::getPhoneLike, testInfo.getPhoneLike())
             .gt(TestInfo::getIdCard, testInfo.getIdCard())
             .in(TestInfo::getAddress, testInfo.getAddress())
             .like(TestInfo::getIdCardLike, testInfo.getIdCardLike())
             .list();
   }
```

#### @ReturnDecrypt
返回结果解密注解（**_注意返回结果解密注解必须加在mapper方法上_**）<br>
`fields`填写需要解密的字段<br>
`isAll`返回结果是否全部解密，默认为false
##### 返回List
```java
   @ReturnDecrypt(isAll = true)
   List<String> queryByString(@Param("phoneLike") String phoneLike, @Param("idCardLike") String idCardLike);
```
##### 返回Map
```java
   @ReturnDecrypt(fields = {"name", "phone"})
   Map<String, Object> queryByMap(@Param("param") Map<String, Object> param);
```
##### 返回Entity
返回为实体类或者实体类集合，需要在实体类加`@SensitiveData`注解，在字段上加`@SensitiveField`。（mapper请求方法可以不加`@ReturnDecrypt`注解）
```java
   List<TestInfo> queryByList(@Param("list") List<String> list);
```

#### @FieldSensitive
字段脱敏，目前支持:中文名、身份证号、座机号、手机号、地址、电子邮件、银行卡号、密码、车牌号<br>
`SensitiveType` <br>
>CHINESE_NAME 中文名，张三：张*<br>
>
>ID_CARD 身份证号，51343620000320711X：5***************1X <br>
>
>PHONE 座机号， 09157518479：0915*****79<br>
>
>MOBILE 手机号，18049531999：180****1999<br>
>
>ADDRESS 地址，北京市海淀区马连洼街道289号：北京市海淀区马******** <br>
>
>EMAIL 电子邮箱，zhangsan@gmail.com.cn： ***********@gmail.com.cn<br>
>
>BANK_CARD 银行卡号，11011111222233333256：1101 **** **** **** 3256 <br>
>
>PASSWORD 密码，1234567890：**********<br>
>
>CAR_NUMBER 车牌号，京A12345：京A1***5 <br>
```
   @FieldSensitive(value = SensitiveType.PHONE)
   private String phone;
```
##### 自定义脱敏策略
```java
    @FieldSensitive("testStrategy")
    private String phone;
```
```java
   @Configuration
   public class SensitiveStrategyConfig {
   
       /**
        * 自定义Strategy类型脱敏处理
        */
       @Bean
       public void customStrategy() {
           new SensitiveStrategy().addStrategy("testStrategy", t -> t + "***test***");
       }
   }
```









## 更新日志 2023/03/03

慢接口预警在原有推送日志的基础上新增平台预警功能

* 可通过配置的形式搭建平台推送，当前支持平台：钉钉、企业微信

* 配置参数：

  ```java
  package com.security.notifier.entity;
  
  import lombok.Data;
  
  /**
   * 通知平台配置
   * @author LJJ
   * @Date 2023/3/3 13:55
   */
  @Data
  public class NotifyPlatform {
  
      /**
       * 平台名称
       */
      private String platform;
  
      /**
       * 网址令牌
       */
      private String urlKey;
  
      /**
       * 密钥
       */
      private String secret;
  
      /**
       * 通知范围
       */
      private String receivers = "所有人";
  }
  
  
  ```



## 更新日志 2023/03/13

新增黑名单IP校验功能

## 更新日志 2024/01/11

新增数据库字段加解密及序列化脱敏功能



## 参与贡献

zebord(LJJ)