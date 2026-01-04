## 失物招领系统  

使用前 pip install django mysqlclient pillow

运行./run.ps1启动服务  

进入 http://127.0.0.1:8000/MyApp/  访问主页  


## 访问后台管理（Admin）

- 启动开发服务器：
  - PowerShell / CMD：`python manage.py runserver`
  - 或使用脚本：`.\run.ps1`（如被阻止，可临时允许脚本：`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`）
- 后台地址：`http://127.0.0.1:8000/admin/`
- 登录：使用超级用户（没有可创建：`python manage.py createsuperuser`）

在站点模板中加入后台入口示例（只对 staff 用户显示）：

```html
{% raw %}{% if request.user.is_staff %}
  <a href="{% url 'admin:index' %}">后台管理</a>
{% endif %}{% endraw %}
```

> 提示：项目中有自定义的 `MyApp.models.User` 用于存储用户数据，但 Django 后台登录与权限由内置 `auth.User` 管理；若需要把自定义用户与认证系统合并，请提前告知，我可以帮你规划迁移方案。