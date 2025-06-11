from tortoise.models import Model
from tortoise import fields
from datetime import datetime 

class CaseAnalysisRequest(Model):
    # 主键字段 request_id 是请求ID，作为主键
    request_id = fields.CharField(max_length=100, pk=True, description="请求唯一标识ID（主键）")
    case_number = fields.CharField(null=True, max_length=100, description="案件编号")   
    caller_identity_id = fields.CharField(max_length=20, description="调用者身份标识ID") 
    request_time = fields.DatetimeField(auto_now_add=True, description="请求时间（自动填充创建时的当前时间）")
    request_type = fields.CharField(null=True, max_length=100, description="案件类型:后台调用/案件查询/文档上传")   
    # 新增字段
    query_success = fields.IntField(default=0, description="数据库查询是否成功标识（0-查询失败，1-查询成功）")
    transcript_count = fields.IntField(default=0, description="本次分析关联的笔录文件数量")
    analysis_result_count = fields.IntField(default=0, description="分析完成后产生的有效结果数量")
    result_pushed = fields.IntField(default=0, description="分析结果是否已推送给用户（0-未返回，1-已返回）")
    is_completed = fields.IntField(default=0, description="调用流程是否完结标识（0-未完结，1-已完结）")
    # 时间戳
    push_time = fields.DatetimeField(default=None, null=True, description="分析结果推送时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
 
    class Meta:
        table = "case_analysis_request"  # 表名
        indexes = ['case_number','caller_identity_id']
 
class CaseAnalysisRequestRecord(Model):
    # 任务ID（主键，唯一标识符）
    task_id = fields.CharField(max_length=100, pk=True, description="任务唯一标识符主键")
    # 基础请求信息
    request_id = fields.CharField(max_length=100, description="请求ID")
    case_number = fields.CharField(null=True, max_length=100, description="案件编号")
    caller_identity_id = fields.CharField(max_length=20, description="调用者身份标识ID")
    # 笔录相关信息 
    transcript_number = fields.CharField(null=True,max_length=255, description="笔录编号")
    transcript_content = fields.TextField(default=None,null=True,description="笔录原文")
    ask_type = fields.CharField(null=True,max_length=10, description="询问类型")

    interviewee_name = fields.CharField(default=None,null=True,max_length=50, description="被询问人姓名")
    gender = fields.CharField(default=None,max_length=10, null=True, description="性别")  # 新增字段
    age = fields.IntField(default=None,null=True, description="年龄")  # 新增字段
    birth_date = fields.DateField(default=None,null=True, description="出生日期")  # 新增字段
    id_number = fields.CharField(default=None,null=True,max_length=100, description="身份证号码")
    household_registration = fields.CharField(default=None,null=True,max_length=255, description="户籍")
    transcript_time = fields.DatetimeField(default=None,null=True, description="笔录记录时间")
    register_dep = fields.CharField(default=None,null=True,max_length=100, description="立案单位")
    # address = fields.CharField(max_length=255, description="住址")
    # education_level = fields.CharField(max_length=100, description="文凭")
    # 分析结果与状态
    transcript_content_pp = fields.TextField(default=None,null=True,description="后处理的笔录原文")
    analysis_result = fields.TextField(default=None,null=True, description="笔录分析结果（JSON格式）")
    analysis_duration = fields.FloatField(default=None,null=True,description="笔录分析耗时（秒）")
    analysis_complete_time = fields.DatetimeField(default=None,null=True, description="笔录分析完结时间")
    is_analysis_complete = fields.IntField(default=0, description="笔录分析任务是否完结")
    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    return_time = fields.DatetimeField(default=None,null=True, description="分析结果返回时间")

    class Meta:
        table = "case_analysis_request_records"
        indexes = ['request_id', 'case_number','caller_identity_id'] 

class CaseAnalysisResultsPushed(Model):
    # 主键字段 request_id 是请求ID，作为主键
    push_id = fields.CharField(max_length=100, pk=True, description="推送唯一标识ID（主键）")
    request_id = fields.CharField(max_length=100, description="请求ID")
    analysis_result_pushed = fields.TextField(default=None,null=True, description="推送的笔录分析结果（JSON格式）")
    # 时间戳
    push_time = fields.DatetimeField(default=None, null=True, description="分析结果推送时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
 
    class Meta:
        table = "case_analysis_results_pushed"  # 表名
        indexes = ['push_id','request_id']
  